"""BudgetAI Generation and Proposal acceptance service."""

from __future__ import annotations

import json
import uuid
from decimal import Decimal
from pathlib import Path

from app.core.domain import MemberRole, Permission, ProposalStatus, ProposalType
from app.core.errors import (
    ForbiddenError,
    InvalidRequestError,
    NotFoundError,
    StaleProposalError,
)
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.ai import repository as ai_repo
from app.modules.ai.provider import StructuredGenerationProvider
from app.modules.audit import repository as audit
from app.modules.budget import repository as budget_repo
from app.modules.budget.schemas import (
    BudgetAcceptRequest,
    BudgetProposalOut,
    BudgetProposalPayload,
)
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.preferences import repository as preferences_repo

PROMPT_FILE = Path(__file__).parent / "prompts" / "budget_generation_v1.md"


def _load_system_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8")
    return "You are BudgetAI, expert financial intelligence planner for weddings."


async def generate_budget_proposal(
    db: Database,
    ai_provider: StructuredGenerationProvider | None,
    principal: Principal,
    event_id: uuid.UUID,
    user_prompt: str,
) -> BudgetProposalOut:
    if ai_provider is None:
        raise InvalidRequestError("AI service is not configured or currently disabled.")

    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_PROPOSE)

        budget = budget_repo.get_budget(conn, event_id)
        total_limit = Decimal(str(budget["total_limit"])) if budget else Decimal("1000000.00")
        currency = budget["currency"] if budget else event["currency"]

        pref = preferences_repo.get_preferences(conn, event_id)
        existing_categories = budget_repo.list_categories(conn, budget["id"]) if budget else []

        context_payload = {
            "event": {
                "title": event["title"],
                "event_type": event["event_type"],
                "guest_count": event["expected_guest_count"],
                "currency": currency,
                "total_limit": str(total_limit),
                "city": event["city"],
            },
            "preferences": {
                "style_tags": pref["style_tags"] if pref else [],
                "cultural_context": pref["cultural_context"] if pref else {},
                "priorities": pref["priorities"] if pref else {},
            },
            "existing_categories": [c["name"] for c in existing_categories],
            "user_instructions": user_prompt,
        }

        system_instruction = _load_system_prompt()
        prompt_content = (
            f"Event and Budget Context:\n"
            f"{json.dumps(context_payload, indent=2)}\n\n"
            f"Host Request:\n{user_prompt}"
        )

        # Generate structured proposal
        res = await ai_provider.generate(
            task_name="budget_generation",
            system_instruction=system_instruction,
            user_input=prompt_content,
            response_schema=BudgetProposalPayload,
        )
        payload_data = BudgetProposalPayload(**res.parsed_json)

        # Deterministic verification of percentages and recalculate amounts with Decimal
        total_pct = sum(item.percentage for item in payload_data.proposed_allocations)
        if total_pct > Decimal("0.00"):
            # Normalize to 100% if slight rounding error (e.g. 99% - 101%)
            factor = Decimal("100.0") / total_pct
            for item in payload_data.proposed_allocations:
                item.percentage = (item.percentage * factor).quantize(Decimal("0.01"))
                item.suggested_amount = (total_limit * (item.percentage / Decimal("100.0"))).quantize(
                    Decimal("0.01")
                )

        # Store in ai_proposals
        proposal_row = ai_repo.insert_proposal(
            conn,
            event_id=event_id,
            conversation_id=None,
            created_by=principal.user_id,
            proposal_type=ProposalType.BUDGET_SUGGESTIONS.value,
            base_revision=event["revision"],
            schema_version=1,
            payload=payload_data.model_dump(mode="json"),
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="budget_proposal.generated",
            entity_type="ai_proposals",
            entity_id=proposal_row["id"],
            request_id=request_id,
            metadata={
                "total_limit": str(total_limit),
                "allocations_count": len(payload_data.proposed_allocations),
            },
        )

        return BudgetProposalOut(
            id=proposal_row["id"],
            event_id=proposal_row["event_id"],
            conversation_id=proposal_row["conversation_id"],
            proposal_type=proposal_row["proposal_type"],
            status=proposal_row["status"],
            base_revision=proposal_row["base_revision"],
            payload=payload_data,
            created_at=proposal_row["created_at"],
            accepted_at=proposal_row["accepted_at"],
        )


def accept_budget_proposal(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    request: BudgetAcceptRequest,
) -> BudgetProposalOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id, for_update=True)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_MANAGE)

        proposal = ai_repo.get_proposal(conn, event_id, proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal not found.")

        if proposal["status"] in (ProposalStatus.REJECTED.value, ProposalStatus.STALE.value):
            raise StaleProposalError(f"Cannot accept proposal with status '{proposal['status']}'.")
        if proposal["status"] == ProposalStatus.ACCEPTED.value:
            raise InvalidRequestError("Proposal has already been accepted.")

        # Stale revision check
        if event["revision"] != request.base_revision or proposal["base_revision"] != event["revision"]:
            ai_repo.update_proposal_status(conn, event_id, proposal_id, ProposalStatus.STALE.value)
            raise StaleProposalError(
                f"Event revision changed ({request.base_revision} -> {event['revision']}). Proposal is stale."
            )

        payload_dict = (
            proposal["payload"] if isinstance(proposal["payload"], dict) else json.loads(proposal["payload"])
        )
        payload = BudgetProposalPayload(**payload_dict)

        budget = budget_repo.get_budget(conn, event_id)
        if budget is None:
            budget = budget_repo.create_budget(conn, event_id, Decimal("0.00"), event["currency"])

        total_limit = Decimal(str(budget["total_limit"]))
        selected_keys = set(request.selected_category_keys)
        proposals_by_key = {item.category_key: item for item in payload.proposed_allocations}

        for key in selected_keys:
            if key not in proposals_by_key:
                raise InvalidRequestError(f"Category key '{key}' not found in proposal.")

        # Apply selected allocations to budget_categories
        sort_order = 10
        for key in selected_keys:
            p_cat = proposals_by_key[key]
            calculated_amount = (total_limit * (p_cat.percentage / Decimal("100.0"))).quantize(
                Decimal("0.01")
            )
            existing = budget_repo.get_category_by_key(conn, budget["id"], key)
            if existing is not None:
                budget_repo.update_category(
                    conn,
                    category_id=existing["id"],
                    name=p_cat.name,
                    planned_amount=calculated_amount,
                )
            else:
                budget_repo.create_category(
                    conn,
                    budget_id=budget["id"],
                    category_key=key,
                    name=p_cat.name,
                    planned_amount=calculated_amount,
                    sort_order=sort_order,
                )
            sort_order += 10

        new_status = (
            ProposalStatus.ACCEPTED.value
            if len(selected_keys) >= len(payload.proposed_allocations)
            else ProposalStatus.PARTIALLY_ACCEPTED.value
        )
        ai_repo.update_proposal_status(conn, event_id, proposal_id, new_status)

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="budget_proposal.accepted",
            entity_type="ai_proposals",
            entity_id=proposal_id,
            request_id=request_id,
            metadata={"accepted_categories": list(selected_keys), "status": new_status},
        )

        return BudgetProposalOut(
            id=proposal["id"],
            event_id=proposal["event_id"],
            conversation_id=proposal["conversation_id"],
            proposal_type=proposal["proposal_type"],
            status=new_status,
            base_revision=event["revision"],
            payload=payload,
            created_at=proposal["created_at"],
            accepted_at=proposal["accepted_at"],
        )

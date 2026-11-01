"""Service for PlanAI generation, proposal management and acceptance."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core.domain import Permission, ProposalStatus
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
from app.modules.events import repository as events_repo
from app.modules.events.context import build_event_context
from app.modules.events.permissions import require_permission
from app.modules.functions import repository as functions_repo
from app.modules.plan_ai.schemas import (
    PlanAcceptRequest,
    PlanAcceptResponse,
    PlanGenerateRequest,
    PlanProposalOut,
    PlanProposalPayload,
    validate_plan_proposal_domain,
)

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "plan_generation_v1.md"


def get_plan_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "You are PlanAI, the intelligent wedding planning assistant for UtsavAI."


async def generate_wedding_plan(
    db: Database,
    provider: StructuredGenerationProvider,
    principal: Principal,
    event_id: uuid.UUID,
    request: PlanGenerateRequest,
) -> PlanProposalOut:
    ctx = build_event_context(db, principal, event_id)
    if not ctx.permissions.can_generate_plan:
        raise ForbiddenError("Unauthorized to generate plans for this event.")

    current_revision = ctx.event.revision
    if request.base_revision != current_revision:
        raise StaleProposalError(
            f"Event has changed. Expected revision {current_revision}, received {request.base_revision}."
        )

    system_instruction = get_plan_prompt()
    user_input = (
        f"Event details:\n{ctx.event.model_dump_json()}\n"
        f"Event preferences:\n{ctx.preferences.model_dump_json()}\n"
        f"Existing functions: {[f.name for f in ctx.functions]}\n"
        f"Requested items: {request.include}\n"
        f"Base revision: {current_revision}\n\n"
        f"User request: {request.request}"
    )

    res = await provider.generate(
        task_name="plan_generation",
        system_instruction=system_instruction,
        user_input=user_input,
        response_schema=PlanProposalPayload,
    )

    parsed_payload = PlanProposalPayload(**res.parsed_json)
    validate_plan_proposal_domain(parsed_payload, ctx)

    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        status = "stale" if event["revision"] != current_revision else "proposed"

        proposal_row = ai_repo.insert_proposal(
            conn,
            event_id=event_id,
            conversation_id=request.conversation_id,
            created_by=principal.user_id,
            proposal_type="plan",
            base_revision=current_revision,
            schema_version=1,
            payload=parsed_payload.model_dump(mode="json"),
            model_id=res.model_id,
            prompt_version="plan_generation_v1",
        )
        proposal_id = proposal_row["id"]

        if status == "stale":
            ai_repo.update_proposal_status(conn, event_id, proposal_id, "stale")
            proposal_row["status"] = "stale"

        if request.conversation_id:
            ai_repo.insert_message(
                conn,
                conversation_id=request.conversation_id,
                role="assistant",
                content=f"I have generated a wedding plan proposal: {parsed_payload.summary}",
                proposal_id=proposal_id,
                model_id=res.model_id,
                prompt_version="plan_generation_v1",
                validation_status="valid",
            )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="plan.generated",
            entity_type="ai_proposals",
            entity_id=proposal_id,
            request_id=request_id,
            metadata={"base_revision": current_revision, "status": status},
        )

        return PlanProposalOut(
            proposal_id=proposal_row["id"],
            event_id=proposal_row["event_id"],
            conversation_id=proposal_row["conversation_id"],
            base_revision=proposal_row["base_revision"],
            status=proposal_row["status"],
            schema_version=proposal_row["schema_version"],
            payload=parsed_payload,
            created_at=proposal_row["created_at"],
            accepted_at=proposal_row["accepted_at"],
            model_metadata={"model": res.model_id, "latency_ms": res.latency_ms},
        )


def get_plan_proposal(
    db: Database, principal: Principal, event_id: uuid.UUID, proposal_id: uuid.UUID
) -> PlanProposalOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.EVENT_READ)

        row = ai_repo.get_proposal(conn, event_id, proposal_id)
        if row is None:
            raise NotFoundError("Proposal not found.")

        if row["status"] in ("proposed", "partially_accepted") and row["base_revision"] < event["revision"]:
            ai_repo.update_proposal_status(conn, event_id, proposal_id, "stale")
            row["status"] = "stale"

        payload_dict = row["payload"] if isinstance(row["payload"], dict) else json.loads(row["payload"])
        return PlanProposalOut(
            proposal_id=row["id"],
            event_id=row["event_id"],
            conversation_id=row["conversation_id"],
            base_revision=row["base_revision"],
            status=row["status"],
            schema_version=row["schema_version"],
            payload=PlanProposalPayload(**payload_dict),
            created_at=row["created_at"],
            accepted_at=row["accepted_at"],
            model_metadata={"model": row["model_id"]},
        )


def reject_plan_proposal(
    db: Database, principal: Principal, event_id: uuid.UUID, proposal_id: uuid.UUID
) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.PLAN_ACCEPT)

        row = ai_repo.get_proposal(conn, event_id, proposal_id)
        if row is None:
            raise NotFoundError("Proposal not found.")
        if row["status"] in ("accepted", "rejected"):
            raise InvalidRequestError(f"Proposal is already {row['status']}.")

        ai_repo.update_proposal_status(conn, event_id, proposal_id, "rejected")
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="plan.rejected",
            entity_type="ai_proposals",
            entity_id=proposal_id,
            request_id=request_id,
            metadata={},
        )


def accept_plan_proposal(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    request: PlanAcceptRequest,
) -> PlanAcceptResponse:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id, for_update=True)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(event["my_role"], Permission.PLAN_ACCEPT)

        proposal = ai_repo.get_proposal(conn, event_id, proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal not found.")

        if proposal["status"] in ("rejected", "stale"):
            raise StaleProposalError(f"Cannot accept proposal with status '{proposal['status']}'.")
        if proposal["status"] == "accepted":
            raise InvalidRequestError("Proposal has already been fully accepted.")

        if event["revision"] != request.base_revision or proposal["base_revision"] != event["revision"]:
            ai_repo.update_proposal_status(conn, event_id, proposal_id, "stale")
            raise StaleProposalError(
                f"Event revision changed ({request.base_revision} -> {event['revision']}). Proposal is stale."
            )

        payload_dict = (
            proposal["payload"] if isinstance(proposal["payload"], dict) else json.loads(proposal["payload"])
        )
        payload = PlanProposalPayload(**payload_dict)

        selected_fn_refs = set(request.selected_function_refs)
        selected_task_refs = set(request.selected_task_refs)

        if not selected_fn_refs and not selected_task_refs:
            raise InvalidRequestError("At least one function or task must be selected for acceptance.")

        proposed_fns_by_ref = {f.client_ref: f for f in payload.proposed_functions}
        for fref in selected_fn_refs:
            if fref not in proposed_fns_by_ref:
                raise InvalidRequestError(f"Function reference '{fref}' not found in proposal.")

        proposed_tasks_by_ref = {t.client_ref: t for t in payload.proposed_tasks}
        for tref in selected_task_refs:
            if tref not in proposed_tasks_by_ref:
                raise InvalidRequestError(f"Task reference '{tref}' not found in proposal.")
            task = proposed_tasks_by_ref[tref]
            for dep in task.depends_on:
                if dep not in selected_task_refs:
                    raise InvalidRequestError(
                        f"Selected task '{task.title}' depends on '{dep}', which was not selected."
                    )

        created_fn_ids: list[uuid.UUID] = []
        fn_id_map: dict[str, uuid.UUID] = {}

        for fref in selected_fn_refs:
            pfn = proposed_fns_by_ref[fref]
            fn_row = functions_repo.insert_function(
                conn,
                event_id=event_id,
                values={
                    "name": pfn.name,
                    "starts_at": pfn.starts_at,
                    "ends_at": pfn.ends_at,
                    "location_name": pfn.location_name,
                    "notes": pfn.notes,
                    "sort_order": pfn.sort_order,
                },
            )
            fn_id = fn_row["id"]
            created_fn_ids.append(fn_id)
            fn_id_map[fref] = fn_id

        created_task_ids: list[uuid.UUID] = []
        task_id_map: dict[str, uuid.UUID] = {}

        for tref in selected_task_refs:
            ptask = proposed_tasks_by_ref[tref]
            mapped_func_id = fn_id_map.get(ptask.function_ref) if ptask.function_ref else None

            t_row = conn.execute(
                """
                insert into public.tasks
                  (event_id, function_id, title, description, due_at, status, priority, origin)
                values
                  (%s, %s, %s, %s, %s, 'todo', %s, 'ai_accepted')
                returning id
                """,
                (
                    event_id,
                    mapped_func_id,
                    ptask.title,
                    ptask.description,
                    ptask.due_at,
                    ptask.priority,
                ),
            ).fetchone()
            assert t_row is not None
            t_id = t_row["id"]
            created_task_ids.append(t_id)
            task_id_map[tref] = t_id

        for tref in selected_task_refs:
            ptask = proposed_tasks_by_ref[tref]
            t_id = task_id_map[tref]
            for dep_ref in ptask.depends_on:
                dep_id = task_id_map[dep_ref]
                conn.execute(
                    """
                    insert into public.task_dependencies (task_id, depends_on_task_id)
                    values (%s, %s)
                    on conflict do nothing
                    """,
                    (t_id, dep_id),
                )

        total_proposed = len(payload.proposed_functions) + len(payload.proposed_tasks)
        total_accepted = len(selected_fn_refs) + len(selected_task_refs)
        new_status = (
            ProposalStatus.ACCEPTED.value
            if total_accepted >= total_proposed
            else ProposalStatus.PARTIALLY_ACCEPTED.value
        )
        accepted_at = datetime.now(UTC)
        ai_repo.update_proposal_status(conn, event_id, proposal_id, new_status, accepted_at)

        refetched_event = events_repo.get_event(conn, event_id)
        new_revision = refetched_event["revision"] if refetched_event else event["revision"] + 1

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="plan.accepted",
            entity_type="ai_proposals",
            entity_id=proposal_id,
            request_id=request_id,
            metadata={
                "accepted_functions_count": len(created_fn_ids),
                "accepted_tasks_count": len(created_task_ids),
                "status": new_status,
                "new_revision": new_revision,
            },
        )

        return PlanAcceptResponse(
            proposal_id=proposal_id,
            status=new_status,
            new_revision=new_revision,
            accepted_functions_count=len(created_fn_ids),
            accepted_tasks_count=len(created_task_ids),
            created_function_ids=created_fn_ids,
            created_task_ids=created_task_ids,
        )

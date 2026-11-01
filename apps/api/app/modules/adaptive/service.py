"""Service layer for Phase 6 Adaptive Planning Engine."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.domain import MemberRole, Permission, role_allows
from app.core.errors import ConflictError, ForbiddenError, InvalidRequestError, NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.adaptive import repository as adaptive_repo
from app.modules.adaptive.ai_explainer import explain_impact, interpret_change_prompt
from app.modules.adaptive.impact_engine import calculate_impact
from app.modules.adaptive.schemas import (
    ChangeProposalCreate,
    ChangeProposalOut,
    ImpactResult,
    InterpretedChangeResponse,
    ProposalAcceptRequest,
    ProposalRejectRequest,
    TypedChangeRequest,
)
from app.modules.ai.provider import StructuredGenerationProvider
from app.modules.audit import repository as audit
from app.modules.budget import repository as budget_repo
from app.modules.events import repository as events_repo
from app.modules.events.context import build_event_context
from app.modules.events.permissions import require_permission
from app.modules.functions import repository as functions_repo
from app.modules.gifts import repository as gifts_repo
from app.modules.tasks import repository as tasks_repo
from app.modules.vendors import repository as vendors_repo

logger = logging.getLogger(__name__)


def _parse_json_field(val: Any) -> Any:
    if isinstance(val, str):
        return json.loads(val)
    return val


def _to_proposal_out(row: dict[str, Any]) -> ChangeProposalOut:
    req_changes = _parse_json_field(row["requested_changes"])
    impact_data = _parse_json_field(row["impact_result"])

    return ChangeProposalOut(
        id=row["id"],
        event_id=row["event_id"],
        created_by=row["created_by"],
        base_revision=row["base_revision"],
        request_text=row["request_text"],
        requested_changes=req_changes,
        impact_result=ImpactResult(**impact_data),
        ai_explanation=row["ai_explanation"],
        status=row["status"],
        accepted_at=row["accepted_at"],
        accepted_revision=row["accepted_revision"],
        rules_version=row["rules_version"],
        schema_version=row["schema_version"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


async def create_change_proposal(
    db: Database,
    provider: StructuredGenerationProvider | None,
    principal: Principal,
    event_id: uuid.UUID,
    payload: ChangeProposalCreate,
) -> ChangeProposalOut:
    ctx = build_event_context(db, principal, event_id)
    if ctx.event.status == "archived":
        raise InvalidRequestError("Cannot propose changes to an archived event.")

    role = MemberRole(ctx.permissions.role)
    if not role_allows(role, Permission.ADAPTIVE_PLAN_PROPOSE):
        raise ForbiddenError("You do not have permission to propose adaptive planning changes.")

    if payload.base_revision != ctx.event.revision:
        raise ConflictError(
            f"Base revision {payload.base_revision} does not match "
            f"current event revision {ctx.event.revision}."
        )

    typed_req = TypedChangeRequest(
        schema_version=1,
        base_revision=payload.base_revision,
        request_text=payload.request_text,
        event_changes=payload.event_changes,
        budget_changes=payload.budget_changes,
        function_changes=payload.function_changes,
    )

    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        task_rows = [dict(t) for t in tasks_repo.list_tasks(conn, event_id)]
        quote_rows = [dict(q) for q in vendors_repo.list_all_event_quotes(conn, event_id)]
        registry_row = gifts_repo.get_registry_by_event(conn, event_id)
        registry_dict = dict(registry_row) if registry_row else None

        # 1. Deterministic impact calculation
        impact = calculate_impact(ctx, typed_req, task_rows, quote_rows, registry_dict)

        # 2. Advisory AI explanation (safe fallback if unavailable)
        explanation = await explain_impact(provider, ctx, typed_req, impact)

        # 3. Persist proposal
        row = adaptive_repo.create_proposal(
            conn,
            event_id=event_id,
            created_by=principal.user_id,
            base_revision=payload.base_revision,
            request_text=payload.request_text,
            requested_changes=typed_req.model_dump(mode="json"),
            impact_result=impact.model_dump(mode="json"),
            ai_explanation=explanation,
            rules_version=impact.rules_version,
            schema_version=1,
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="change_proposal.created",
            entity_type="change_proposal",
            entity_id=row["id"],
            request_id=request_id,
            metadata={
                "base_revision": payload.base_revision,
                "severity": impact.severity,
                "affected_modules": impact.affected_modules,
            },
        )

        return _to_proposal_out(dict(row))


def get_change_proposal(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
) -> ChangeProposalOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        ev = events_repo.get_event(conn, event_id)
        if not ev:
            raise NotFoundError("Event not found.")
        require_permission(ev["my_role"], Permission.ADAPTIVE_PLAN_READ)

        row = adaptive_repo.get_proposal(conn, event_id, proposal_id)
        if not row:
            raise NotFoundError("Change proposal not found.")

        return _to_proposal_out(dict(row))


def list_change_proposals(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    status: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list[ChangeProposalOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        ev = events_repo.get_event(conn, event_id)
        if not ev:
            raise NotFoundError("Event not found.")
        require_permission(ev["my_role"], Permission.ADAPTIVE_PLAN_READ)

        rows = adaptive_repo.list_proposals(conn, event_id, status=status, limit=limit, offset=offset)
        return [_to_proposal_out(dict(r)) for r in rows]


def reject_change_proposal(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    req: ProposalRejectRequest,
) -> ChangeProposalOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        ev = events_repo.get_event(conn, event_id)
        if not ev:
            raise NotFoundError("Event not found.")
        require_permission(ev["my_role"], Permission.ADAPTIVE_PLAN_PROPOSE)

        row = adaptive_repo.get_proposal(conn, event_id, proposal_id)
        if not row:
            raise NotFoundError("Change proposal not found.")

        if row["status"] != "proposed":
            raise InvalidRequestError(f"Cannot reject proposal with status '{row['status']}'.")

        updated = adaptive_repo.update_proposal_status(
            conn,
            event_id=event_id,
            proposal_id=proposal_id,
            status="rejected",
        )
        assert updated is not None

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="change_proposal.rejected",
            entity_type="change_proposal",
            entity_id=proposal_id,
            request_id=request_id,
            metadata={"reason": req.reason},
        )

        return _to_proposal_out(dict(updated))


def accept_change_proposal(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    req: ProposalAcceptRequest,
) -> ChangeProposalOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        # Strictly owner-only
        ev = events_repo.get_event(conn, event_id, for_update=True)
        if not ev:
            raise NotFoundError("Event not found.")

        require_permission(ev["my_role"], Permission.ADAPTIVE_PLAN_MANAGE)
        if ev["my_role"] != MemberRole.OWNER.value:
            raise ForbiddenError("Only the event owner may accept change proposals.")

        if ev["status"] == "archived":
            raise InvalidRequestError("Cannot accept change proposals on an archived event.")

        proposal = adaptive_repo.lock_proposal_for_update(conn, event_id, proposal_id)
        if not proposal:
            raise NotFoundError("Change proposal not found.")

        if proposal["status"] != "proposed":
            raise InvalidRequestError(
                f"Proposal cannot be accepted because its status is '{proposal['status']}'."
            )

        # Revision check
        if ev["revision"] != proposal["base_revision"]:
            adaptive_repo.update_proposal_status(
                conn,
                event_id=event_id,
                proposal_id=proposal_id,
                status="stale",
            )
            raise ConflictError(
                f"Event revision has changed from {proposal['base_revision']} to "
                f"{ev['revision']}. Proposal is stale."
            )

        req_changes = _parse_json_field(proposal["requested_changes"])
        impact_data = _parse_json_field(proposal["impact_result"])

        # 1. Apply primary event mutations
        event_chg = req_changes.get("event_changes")
        update_fields: dict[str, Any] = {}
        if event_chg:
            if event_chg.get("expected_guest_count") is not None:
                update_fields["expected_guest_count"] = event_chg["expected_guest_count"]
            if event_chg.get("start_at") is not None:
                update_fields["start_at"] = event_chg["start_at"]
            if event_chg.get("end_at") is not None:
                update_fields["end_at"] = event_chg["end_at"]
            if event_chg.get("timezone") is not None:
                update_fields["timezone"] = event_chg["timezone"]
            if event_chg.get("location_name") is not None:
                update_fields["location_name"] = event_chg["location_name"]
            if event_chg.get("city") is not None:
                update_fields["city"] = event_chg["city"]
            if event_chg.get("region") is not None:
                update_fields["region"] = event_chg["region"]
            if event_chg.get("country_code") is not None:
                update_fields["country_code"] = event_chg["country_code"]

        # Ensure event revision increments exactly once
        if not update_fields:
            update_fields["title"] = ev["title"]

        events_repo.update_event(conn, event_id, ev["revision"], update_fields)

        # 2. Apply budget changes
        budget_chg = req_changes.get("budget_changes")
        if budget_chg and budget_chg.get("total_limit") is not None:
            limit_dec = Decimal(str(budget_chg["total_limit"]))
            budget_repo.update_budget(conn, event_id, limit_dec)

        # 3. Apply function changes
        func_changes = req_changes.get("function_changes", [])
        for fc in func_changes:
            action = fc.get("action")
            if action == "add":
                f_name = fc.get("name") or "Celebration Function"
                f_start = fc.get("start_at")
                f_end = fc.get("end_at")
                functions_repo.insert_function(
                    conn,
                    event_id,
                    {
                        "name": f_name,
                        "starts_at": f_start,
                        "ends_at": f_end,
                        "location_name": None,
                        "notes": None,
                        "sort_order": 0,
                    },
                )
            elif action == "archive" and fc.get("function_id"):
                fid = uuid.UUID(str(fc["function_id"]))
                functions_repo.delete_function(conn, event_id, fid)
            elif action == "update" and fc.get("function_id"):
                fid = uuid.UUID(str(fc["function_id"]))
                patch_vals: dict[str, Any] = {}
                if fc.get("name"):
                    patch_vals["name"] = fc["name"]
                if fc.get("start_at"):
                    patch_vals["starts_at"] = fc["start_at"]
                if fc.get("end_at"):
                    patch_vals["ends_at"] = fc["end_at"]
                if patch_vals:
                    functions_repo.update_function(conn, event_id, fid, patch_vals)

        # 4. Apply selected secondary options strictly
        ALLOWED_OP_CODES = {
            "op_shift_task_due_dates",
            "op_extend_gift_registry_expiry",
            "op_flag_budget_for_review",
            "op_mark_vendor_quotes_review",
        }
        available_options = {opt["id"]: opt for opt in impact_data.get("suggested_options", [])}
        for sel_id in req.selected_option_ids:
            if sel_id not in available_options:
                raise InvalidRequestError(f"Selected option '{sel_id}' does not exist on proposal.")
            opt = available_options[sel_id]
            for op in opt.get("operations", []):
                op_code = op.get("op_code")
                if op_code not in ALLOWED_OP_CODES:
                    raise InvalidRequestError(
                        f"Unsupported or unregistered operation code '{op_code}' in option '{sel_id}'."
                    )
                payload = op.get("payload", {})
                if not isinstance(payload, dict):
                    raise InvalidRequestError(f"Malformed operation payload for '{op_code}'.")

                if op_code == "op_shift_task_due_dates":
                    try:
                        shift_sec = int(payload.get("shift_seconds", 0))
                    except (ValueError, TypeError) as err:
                        raise InvalidRequestError(
                            "Malformed payload for op_shift_task_due_dates: shift_seconds must be an integer."
                        ) from err
                    if shift_sec != 0:
                        adaptive_repo.shift_task_due_dates(conn, event_id, shift_sec)
                elif op_code == "op_extend_gift_registry_expiry":
                    reg_id_str = payload.get("registry_id")
                    new_exp_str = payload.get("new_expires_at")
                    if not reg_id_str or not new_exp_str:
                        raise InvalidRequestError(
                            "Malformed payload for op_extend_gift_registry_expiry: "
                            "missing registry_id or new_expires_at."
                        )
                    try:
                        reg_id = uuid.UUID(str(reg_id_str))
                        new_exp_dt = datetime.fromisoformat(str(new_exp_str))
                    except (ValueError, TypeError) as err:
                        raise InvalidRequestError(
                            f"Invalid registry_id or timestamp in operation payload: {err}"
                        ) from err

                    # Verify referenced registry belongs to this event
                    reg_check = conn.execute(
                        "SELECT event_id FROM public.gift_registries WHERE id = %s",
                        (reg_id,),
                    ).fetchone()
                    if reg_check is None or reg_check["event_id"] != event_id:
                        raise InvalidRequestError(
                            "Referenced gift registry in operation does not belong to this event."
                        )

                    adaptive_repo.extend_gift_registry_expiry(conn, reg_id, new_exp_dt)
                elif op_code in ("op_flag_budget_for_review", "op_mark_vendor_quotes_review"):
                    audit.record(
                        conn,
                        event_id=event_id,
                        actor_user_id=principal.user_id,
                        action=f"adaptive.{op_code}",
                        entity_type=op.get("target_module", "system"),
                        entity_id=event_id,
                        request_id=request_id,
                        metadata=payload,
                    )

        # 5. Fetch updated revision and finalize proposal
        updated_ev = events_repo.get_event(conn, event_id)
        assert updated_ev is not None
        new_revision = updated_ev["revision"]

        accepted_proposal = adaptive_repo.update_proposal_status(
            conn,
            event_id=event_id,
            proposal_id=proposal_id,
            status="accepted",
            accepted_revision=new_revision,
        )
        assert accepted_proposal is not None

        # 6. Mark other pending proposals stale
        adaptive_repo.mark_other_proposals_stale(conn, event_id, proposal_id)

        # 7. Audit log for proposal acceptance
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="change_proposal.accepted",
            entity_type="change_proposal",
            entity_id=proposal_id,
            request_id=request_id,
            metadata={
                "base_revision": proposal["base_revision"],
                "accepted_revision": new_revision,
                "selected_options": req.selected_option_ids,
            },
        )

        return _to_proposal_out(dict(accepted_proposal))


async def interpret_change_request(
    db: Database,
    provider: StructuredGenerationProvider | None,
    principal: Principal,
    event_id: uuid.UUID,
    payload: dict[str, Any],
) -> InterpretedChangeResponse:
    ctx = build_event_context(db, principal, event_id)
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise InvalidRequestError("Prompt cannot be empty.")

    summary, candidate_dict = await interpret_change_prompt(provider, ctx, prompt)
    return InterpretedChangeResponse(
        summary=summary,
        candidate_request=ChangeProposalCreate(**candidate_dict),
    )

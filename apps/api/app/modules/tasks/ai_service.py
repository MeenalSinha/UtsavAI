"""TimelineAI Generation and Proposal acceptance service."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from app.core.domain import (
    MemberRole,
    Permission,
    ProposalStatus,
    ProposalType,
    TaskOrigin,
)
from app.core.errors import (
    ConflictError,
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
from app.modules.events.permissions import require_permission
from app.modules.functions import repository as functions_repo
from app.modules.preferences import repository as preferences_repo
from app.modules.tasks import repository as tasks_repo
from app.modules.tasks.schemas import (
    TimelineAcceptRequest,
    TimelineProposalOut,
    TimelineProposalPayload,
)

PROMPT_FILE = Path(__file__).parent / "prompts" / "timeline_generation_v1.md"


def _load_system_prompt() -> str:
    if PROMPT_FILE.exists():
        return PROMPT_FILE.read_text(encoding="utf-8")
    return "You are TimelineAI, expert schedule and task planning intelligence for weddings."


def _validate_proposed_dag(payload: TimelineProposalPayload) -> None:
    client_refs = {t.client_ref for t in payload.proposed_tasks}
    if len(client_refs) != len(payload.proposed_tasks):
        raise ConflictError("Duplicate client_ref values in proposed tasks.")

    adjacency: dict[str, list[str]] = defaultdict(list)
    for t in payload.proposed_tasks:
        for dep in t.depends_on:
            if dep not in client_refs:
                continue
            if dep == t.client_ref:
                raise ConflictError(f"Self-dependency detected for task {t.client_ref}")
            adjacency[t.client_ref].append(dep)

    visited: dict[str, int] = {}

    def dfs(node: str) -> bool:
        visited[node] = 1
        for nbr in adjacency.get(node, []):
            st = visited.get(nbr, 0)
            if st == 1:
                return True
            if st == 0 and dfs(nbr):
                return True
        visited[node] = 2
        return False

    for ref in client_refs:
        if visited.get(ref, 0) == 0 and dfs(ref):
            raise ConflictError("Circular dependency detected in proposed schedule.")


async def generate_timeline_proposal(
    db: Database,
    ai_provider: StructuredGenerationProvider | None,
    principal: Principal,
    event_id: uuid.UUID,
    user_prompt: str,
) -> TimelineProposalOut:
    if ai_provider is None:
        raise InvalidRequestError("AI service is not configured or currently disabled.")

    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(MemberRole(event["my_role"]), Permission.TIMELINE_PROPOSE)

        pref = preferences_repo.get_preferences(conn, event_id)
        functions = functions_repo.list_functions(conn, event_id)
        existing_tasks = tasks_repo.list_tasks(conn, event_id)

        context_payload = {
            "event": {
                "title": event["title"],
                "event_type": event["event_type"],
                "start_at": event["start_at"].isoformat() if event["start_at"] else None,
                "end_at": event["end_at"].isoformat() if event["end_at"] else None,
                "timezone": event["timezone"],
                "guest_count": event["expected_guest_count"],
                "city": event["city"],
            },
            "ceremonies": [
                {
                    "id": str(f["id"]),
                    "name": f["name"],
                    "starts_at": f["starts_at"].isoformat() if f["starts_at"] else None,
                    "ends_at": f["ends_at"].isoformat() if f["ends_at"] else None,
                }
                for f in functions
            ],
            "preferences": {
                "style_tags": pref["style_tags"] if pref else [],
                "cultural_context": pref["cultural_context"] if pref else {},
                "priorities": pref["priorities"] if pref else {},
            },
            "existing_tasks_count": len(existing_tasks),
            "user_instructions": user_prompt,
        }

        system_instruction = _load_system_prompt()
        prompt_content = (
            f"Event Context & Existing Ceremonies:\n"
            f"{json.dumps(context_payload, indent=2)}\n\n"
            f"Host Scheduling Instructions:\n{user_prompt}"
        )

        # Generate structured timeline
        res = await ai_provider.generate(
            task_name="timeline_generation",
            system_instruction=system_instruction,
            user_input=prompt_content,
            response_schema=TimelineProposalPayload,
        )
        payload_data = TimelineProposalPayload(**res.parsed_json)

        # Validate DAG
        _validate_proposed_dag(payload_data)

        # Store in ai_proposals
        proposal_row = ai_repo.insert_proposal(
            conn,
            event_id=event_id,
            conversation_id=None,
            created_by=principal.user_id,
            proposal_type=ProposalType.TIMELINE.value,
            base_revision=event["revision"],
            schema_version=1,
            payload=payload_data.model_dump(mode="json"),
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="timeline_proposal.generated",
            entity_type="ai_proposals",
            entity_id=proposal_row["id"],
            request_id=request_id,
            metadata={"tasks_count": len(payload_data.proposed_tasks)},
        )

        return TimelineProposalOut(
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


def accept_timeline_proposal(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    request: TimelineAcceptRequest,
) -> TimelineProposalOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id, for_update=True)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(MemberRole(event["my_role"]), Permission.TASK_MANAGE)

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
        payload = TimelineProposalPayload(**payload_dict)

        selected_refs = set(request.selected_task_refs)
        tasks_by_ref = {t.client_ref: t for t in payload.proposed_tasks}

        for ref in selected_refs:
            if ref not in tasks_by_ref:
                raise InvalidRequestError(f"Task reference '{ref}' not found in proposal.")

        # Match function references
        func_rows = functions_repo.list_functions(conn, event_id)
        funcs_by_name = {f["name"].lower().strip(): f["id"] for f in func_rows}
        funcs_by_id = {str(f["id"]): f["id"] for f in func_rows}

        # Create tasks
        task_id_map: dict[str, uuid.UUID] = {}
        sort_order = 10
        for ref in selected_refs:
            ptask = tasks_by_ref[ref]
            fn_id: uuid.UUID | None = None
            if ptask.function_ref:
                fn_ref_clean = ptask.function_ref.strip()
                if fn_ref_clean in funcs_by_id:
                    fn_id = funcs_by_id[fn_ref_clean]
                elif fn_ref_clean.lower() in funcs_by_name:
                    fn_id = funcs_by_name[fn_ref_clean.lower()]

            created_row = tasks_repo.create_task(
                conn,
                event_id=event_id,
                title=ptask.title,
                description=ptask.description,
                due_at=ptask.due_at,
                priority=ptask.priority.value,
                function_id=fn_id,
                origin=TaskOrigin.AI_ACCEPTED.value,
                sort_order=sort_order,
            )
            task_id_map[ref] = created_row["id"]
            sort_order += 10

        # Create dependencies for selected tasks
        for ref in selected_refs:
            ptask = tasks_by_ref[ref]
            t_id = task_id_map[ref]
            for dep_ref in ptask.depends_on:
                if dep_ref in task_id_map:
                    dep_id = task_id_map[dep_ref]
                    tasks_repo.add_dependency(conn, t_id, dep_id)

        new_status = (
            ProposalStatus.ACCEPTED.value
            if len(selected_refs) >= len(payload.proposed_tasks)
            else ProposalStatus.PARTIALLY_ACCEPTED.value
        )
        ai_repo.update_proposal_status(conn, event_id, proposal_id, new_status, datetime.now(UTC))

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="timeline_proposal.accepted",
            entity_type="ai_proposals",
            entity_id=proposal_id,
            request_id=request_id,
            metadata={"accepted_tasks": list(selected_refs), "status": new_status},
        )

        return TimelineProposalOut(
            id=proposal["id"],
            event_id=proposal["event_id"],
            conversation_id=proposal["conversation_id"],
            proposal_type=proposal["proposal_type"],
            status=new_status,
            base_revision=event["revision"],
            payload=payload,
            created_at=proposal["created_at"],
            accepted_at=datetime.now(UTC),
        )

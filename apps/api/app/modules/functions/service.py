"""Use cases for event functions."""

from __future__ import annotations

import logging
import uuid

from app.core.domain import Permission
from app.core.errors import ForbiddenError, NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.audit import repository as audit
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.functions import repository
from app.modules.functions.schemas import FunctionCreate, FunctionOut, FunctionUpdate

logger = logging.getLogger(__name__)


def list_event_functions(db: Database, principal: Principal, event_id: uuid.UUID) -> list[FunctionOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.EVENT_READ)

        rows = repository.list_functions(conn, event_id)
        return [FunctionOut(**r) for r in rows]


def create_event_function(
    db: Database, principal: Principal, event_id: uuid.UUID, body: FunctionCreate
) -> FunctionOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(event["my_role"], Permission.FUNCTION_MANAGE)

        row = repository.insert_function(conn, event_id, body.model_dump())
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="function.created",
            entity_type="event_functions",
            entity_id=row["id"],
            request_id=request_id,
            metadata={"name": row["name"]},
        )
        return FunctionOut(**row)


def update_event_function(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    function_id: uuid.UUID,
    body: FunctionUpdate,
) -> FunctionOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(event["my_role"], Permission.FUNCTION_MANAGE)

        existing = repository.get_function(conn, event_id, function_id)
        if existing is None:
            raise NotFoundError("Function not found.")

        patch_data = body.model_dump(exclude_unset=True)
        merged_start = patch_data.get("starts_at", existing["starts_at"])
        merged_end = patch_data.get("ends_at", existing["ends_at"])
        if merged_start and merged_end and merged_end < merged_start:
            raise ValueError("Function end time cannot be before start time.")

        updated = repository.update_function(conn, event_id, function_id, patch_data)
        assert updated is not None
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="function.updated",
            entity_type="event_functions",
            entity_id=function_id,
            request_id=request_id,
            metadata={"fields": list(patch_data.keys())},
        )
        return FunctionOut(**updated)


def delete_event_function(
    db: Database, principal: Principal, event_id: uuid.UUID, function_id: uuid.UUID
) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(event["my_role"], Permission.FUNCTION_MANAGE)

        existing = repository.get_function(conn, event_id, function_id)
        if existing is None:
            raise NotFoundError("Function not found.")

        ok = repository.delete_function(conn, event_id, function_id)
        if not ok:
            raise NotFoundError("Function not found or unauthorized.")

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="function.deleted",
            entity_type="event_functions",
            entity_id=function_id,
            request_id=request_id,
            metadata={"name": existing["name"]},
        )

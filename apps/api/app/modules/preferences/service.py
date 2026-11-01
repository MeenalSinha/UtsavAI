"""Use cases for event preferences."""

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
from app.modules.preferences import repository
from app.modules.preferences.schemas import PreferencesResponse, PreferencesUpdate

logger = logging.getLogger(__name__)


def get_event_preferences(db: Database, principal: Principal, event_id: uuid.UUID) -> PreferencesResponse:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.EVENT_READ)

        row = repository.get_preferences(conn, event_id)
        if row is None:
            return PreferencesResponse(
                event_id=event_id,
                style_tags=[],
                cultural_context={},
                priorities={},
                accessibility_notes={},
                schema_version=1,
                updated_at=event["updated_at"],
            )
        return PreferencesResponse(
            event_id=row["event_id"],
            style_tags=row["style_tags"] or [],
            cultural_context=row["cultural_context"] or {},
            priorities=row["priorities"] or {},
            accessibility_notes=row["accessibility_notes"] or {},
            schema_version=row["schema_version"],
            updated_at=row["updated_at"],
        )


def replace_event_preferences(
    db: Database, principal: Principal, event_id: uuid.UUID, body: PreferencesUpdate
) -> PreferencesResponse:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(event["my_role"], Permission.PREFERENCE_MANAGE)

        updated = repository.upsert_preferences(conn, event_id, body.model_dump())
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="preferences.updated",
            entity_type="event_preferences",
            entity_id=event_id,
            request_id=request_id,
            metadata={"schema_version": body.schema_version},
        )
        return PreferencesResponse(
            event_id=updated["event_id"],
            style_tags=updated["style_tags"] or [],
            cultural_context=updated["cultural_context"] or {},
            priorities=updated["priorities"] or {},
            accessibility_notes=updated["accessibility_notes"] or {},
            schema_version=updated["schema_version"],
            updated_at=updated["updated_at"],
        )

"""Shared event context API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.deps import DatabaseDep, PrincipalDep
from app.modules.events.context import SharedEventContext, build_event_context

router = APIRouter(tags=["context"])


@router.get("/events/{event_id}/context", response_model=SharedEventContext)
def get_context(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> SharedEventContext:
    """Return unified, permission-filtered context for the event workspace."""
    return build_event_context(db, principal, event_id)


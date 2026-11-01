"""Event preferences API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.api.deps import DatabaseDep, PrincipalDep
from app.modules.preferences import service
from app.modules.preferences.schemas import PreferencesResponse, PreferencesUpdate

router = APIRouter(tags=["preferences"])


@router.get("/events/{event_id}/preferences", response_model=PreferencesResponse)
def get_preferences(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> PreferencesResponse:
    """Get validated cultural, style, and personal preferences for an event."""
    return service.get_event_preferences(db, principal, event_id)


@router.put("/events/{event_id}/preferences", response_model=PreferencesResponse)
def replace_preferences(
    event_id: uuid.UUID,
    body: PreferencesUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> PreferencesResponse:
    """Replace preferences document and touch the parent event revision."""
    return service.replace_event_preferences(db, principal, event_id, body)

"""Event functions API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import DatabaseDep, PrincipalDep
from app.modules.functions import service
from app.modules.functions.schemas import FunctionCreate, FunctionOut, FunctionUpdate

router = APIRouter(tags=["functions"])


@router.get("/events/{event_id}/functions", response_model=list[FunctionOut])
def list_functions(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> list[FunctionOut]:
    """List all functions/ceremonies configured for an event."""
    return service.list_event_functions(db, principal, event_id)


@router.post(
    "/events/{event_id}/functions",
    response_model=FunctionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_function(
    event_id: uuid.UUID,
    body: FunctionCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> FunctionOut:
    """Add a function/ceremony to the event."""
    return service.create_event_function(db, principal, event_id, body)


@router.patch("/events/{event_id}/functions/{function_id}", response_model=FunctionOut)
def update_function(
    event_id: uuid.UUID,
    function_id: uuid.UUID,
    body: FunctionUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> FunctionOut:
    """Update function name, scheduling or notes."""
    return service.update_event_function(db, principal, event_id, function_id, body)


@router.delete(
    "/events/{event_id}/functions/{function_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_function(
    event_id: uuid.UUID,
    function_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> Response:
    """Remove a function from the event."""
    service.delete_event_function(db, principal, event_id, function_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


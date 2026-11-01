"""Adaptive Planning API endpoints for cross-module replanning."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import AIProviderDep, DatabaseDep, PrincipalDep
from app.modules.adaptive import service as adaptive_service
from app.modules.adaptive.schemas import (
    ChangeProposalCreate,
    ChangeProposalOut,
    InterpretedChangeResponse,
    InterpretRequestPayload,
    ProposalAcceptRequest,
    ProposalRejectRequest,
)

router = APIRouter(tags=["adaptive"])


@router.post(
    "/events/{event_id}/change-proposals",
    response_model=ChangeProposalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Propose an adaptive planning change",
)
async def create_change_proposal(
    event_id: uuid.UUID,
    payload: ChangeProposalCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
    provider: AIProviderDep,
) -> ChangeProposalOut:
    return await adaptive_service.create_change_proposal(db, provider, principal, event_id, payload)


@router.post(
    "/events/{event_id}/change-proposals/interpret",
    response_model=InterpretedChangeResponse,
    status_code=status.HTTP_200_OK,
    summary="Interpret natural language change request",
)
async def interpret_change_request(
    event_id: uuid.UUID,
    payload: InterpretRequestPayload,
    principal: PrincipalDep,
    db: DatabaseDep,
    provider: AIProviderDep,
) -> InterpretedChangeResponse:
    return await adaptive_service.interpret_change_request(
        db, provider, principal, event_id, payload.model_dump()
    )


@router.get(
    "/events/{event_id}/change-proposals",
    response_model=list[ChangeProposalOut],
    summary="List change proposals for an event",
)
def list_change_proposals(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
    status: Annotated[str | None, Query(description="Filter by proposal status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ChangeProposalOut]:
    return adaptive_service.list_change_proposals(
        db, principal, event_id, status=status, limit=limit, offset=offset
    )


@router.get(
    "/events/{event_id}/change-proposals/{proposal_id}",
    response_model=ChangeProposalOut,
    summary="Get details of a change proposal",
)
def get_change_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ChangeProposalOut:
    return adaptive_service.get_change_proposal(db, principal, event_id, proposal_id)


@router.post(
    "/events/{event_id}/change-proposals/{proposal_id}/accept",
    response_model=ChangeProposalOut,
    summary="Accept and atomically apply a change proposal (Owner only)",
)
def accept_change_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    req: ProposalAcceptRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ChangeProposalOut:
    return adaptive_service.accept_change_proposal(db, principal, event_id, proposal_id, req)


@router.post(
    "/events/{event_id}/change-proposals/{proposal_id}/reject",
    response_model=ChangeProposalOut,
    summary="Reject a change proposal",
)
def reject_change_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    req: ProposalRejectRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ChangeProposalOut:
    return adaptive_service.reject_change_proposal(db, principal, event_id, proposal_id, req)

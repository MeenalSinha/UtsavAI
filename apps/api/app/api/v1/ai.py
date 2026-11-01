"""AI conversations and PlanAI planning API."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Response, status

from app.api.deps import AIProviderDep, DatabaseDep, PrincipalDep
from app.modules.ai import service as conv_service
from app.modules.ai.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    MessageCreate,
    MessageOut,
)
from app.modules.plan_ai import service as plan_service
from app.modules.plan_ai.schemas import (
    PlanAcceptRequest,
    PlanAcceptResponse,
    PlanGenerateRequest,
    PlanProposalOut,
)

router = APIRouter(tags=["ai"])


@router.post(
    "/events/{event_id}/ai/conversations",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    event_id: uuid.UUID,
    body: ConversationCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ConversationOut:
    """Create a new conversational planning session."""
    return conv_service.create_event_conversation(db, principal, event_id, body)


@router.get("/events/{event_id}/ai/conversations", response_model=list[ConversationOut])
def list_conversations(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> list[ConversationOut]:
    """List planning conversations for the current user and event."""
    return conv_service.list_event_conversations(db, principal, event_id)


@router.get(
    "/events/{event_id}/ai/conversations/{conversation_id}",
    response_model=ConversationDetailOut,
)
def get_conversation(
    event_id: uuid.UUID,
    conversation_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ConversationDetailOut:
    """Get conversation messages and details."""
    return conv_service.get_conversation_detail(db, principal, event_id, conversation_id)


@router.post(
    "/events/{event_id}/ai/conversations/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    event_id: uuid.UUID,
    conversation_id: uuid.UUID,
    body: MessageCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
    provider: AIProviderDep,
) -> MessageOut:
    """Send a message to PlanAI and receive a conversational assistant response."""
    return await conv_service.send_conversation_message(
        db, provider, principal, event_id, conversation_id, body
    )


@router.post(
    "/events/{event_id}/plans/generate",
    response_model=PlanProposalOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_plan(
    event_id: uuid.UUID,
    body: PlanGenerateRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
    provider: AIProviderDep,
) -> PlanProposalOut:
    """Generate a structured, personalized wedding plan proposal using Gemini."""
    return await plan_service.generate_wedding_plan(db, provider, principal, event_id, body)


@router.get(
    "/events/{event_id}/ai/proposals/{proposal_id}",
    response_model=PlanProposalOut,
)
def get_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> PlanProposalOut:
    """Fetch a previously generated proposal and verify its current revision freshness."""
    return plan_service.get_plan_proposal(db, principal, event_id, proposal_id)


@router.post(
    "/events/{event_id}/ai/proposals/{proposal_id}/accept",
    response_model=PlanAcceptResponse,
)
def accept_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    body: PlanAcceptRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> PlanAcceptResponse:
    """Selectively accept proposed functions and starter tasks and commit them to PostgreSQL."""
    return plan_service.accept_plan_proposal(db, principal, event_id, proposal_id, body)


@router.post(
    "/events/{event_id}/ai/proposals/{proposal_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reject_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> Response:
    """Reject an AI proposal."""
    plan_service.reject_plan_proposal(db, principal, event_id, proposal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

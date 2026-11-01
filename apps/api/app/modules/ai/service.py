"""Service for AI conversations and messaging."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from app.core.domain import Permission
from app.core.errors import ForbiddenError, NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.ai import repository
from app.modules.ai.provider import StructuredGenerationProvider
from app.modules.ai.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    MessageCreate,
    MessageOut,
)
from app.modules.events import repository as events_repo
from app.modules.events.context import build_event_context
from app.modules.events.permissions import require_permission

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "plan_ai" / "prompts" / "conversation_v1.md"


def get_conversation_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return "You are PlanAI, the celebration planning assistant for UtsavAI."


def create_event_conversation(
    db: Database, principal: Principal, event_id: uuid.UUID, body: ConversationCreate
) -> ConversationOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.PLAN_GENERATE)

        row = repository.create_conversation(conn, event_id, principal.user_id, body.title)
        return ConversationOut(**row)


def list_event_conversations(
    db: Database, principal: Principal, event_id: uuid.UUID
) -> list[ConversationOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.EVENT_READ)

        rows = repository.list_conversations(conn, event_id, principal.user_id)
        return [ConversationOut(**r) for r in rows]


def get_conversation_detail(
    db: Database, principal: Principal, event_id: uuid.UUID, conversation_id: uuid.UUID
) -> ConversationDetailOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.EVENT_READ)

        conv = repository.get_conversation(conn, event_id, conversation_id, principal.user_id)
        if conv is None:
            raise NotFoundError("Conversation not found.")

        messages = repository.list_messages(conn, conversation_id)
        return ConversationDetailOut(
            id=conv["id"],
            event_id=conv["event_id"],
            user_id=conv["user_id"],
            title=conv["title"],
            created_at=conv["created_at"],
            updated_at=conv["updated_at"],
            messages=[MessageOut(**m) for m in messages],
        )


async def send_conversation_message(
    db: Database,
    provider: StructuredGenerationProvider,
    principal: Principal,
    event_id: uuid.UUID,
    conversation_id: uuid.UUID,
    body: MessageCreate,
) -> MessageOut:
    request_id = request_id_var.get()
    # 1. Verify access & persist user message
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        if event["status"] == "archived":
            raise ForbiddenError("Archived events are read-only.")
        require_permission(event["my_role"], Permission.PLAN_GENERATE)

        conv = repository.get_conversation(conn, event_id, conversation_id, principal.user_id)
        if conv is None:
            raise NotFoundError("Conversation not found.")

        repository.insert_message(
            conn,
            conversation_id=conversation_id,
            role="user",
            content=body.content,
            validation_status="valid",
        )

    # 2. Build context outside transaction to avoid holding connection during LLM call
    ctx = build_event_context(db, principal, event_id)
    system_instruction = get_conversation_prompt()
    user_input = (
        f"Event details:\n{ctx.event.model_dump_json()}\n"
        f"Event preferences:\n{ctx.preferences.model_dump_json()}\n"
        f"Existing functions: {[f.name for f in ctx.functions]}\n\n"
        f"User message: {body.content}"
    )

    # 3. Call AI provider
    res = await provider.generate(
        task_name="conversation",
        system_instruction=system_instruction,
        user_input=user_input,
    )

    # 4. Save assistant response
    with db.transaction(principal.user_id, request_id) as conn:
        assistant_row = repository.insert_message(
            conn,
            conversation_id=conversation_id,
            role="assistant",
            content=res.raw_text,
            model_id=res.model_id,
            prompt_version="conversation-v1",
            validation_status="valid",
        )
        return MessageOut(**assistant_row)

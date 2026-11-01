"""Persistence for AI conversations, messages and proposals."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from app.database.pool import Connection


def create_conversation(
    conn: Connection, event_id: uuid.UUID, user_id: uuid.UUID, title: str | None
) -> dict[str, Any]:
    row = conn.execute(
        """
        insert into public.ai_conversations (event_id, user_id, title)
        values (%s, %s, %s)
        returning id, event_id, user_id, title, created_at, updated_at
        """,
        (event_id, user_id, title),
    ).fetchone()
    assert row is not None
    return dict(row)


def list_conversations(conn: Connection, event_id: uuid.UUID, user_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select id, event_id, user_id, title, created_at, updated_at
          from public.ai_conversations
         where event_id = %s and user_id = %s
         order by updated_at desc
        """,
        (event_id, user_id),
    ).fetchall()
    return [dict(r) for r in rows]


def get_conversation(
    conn: Connection, event_id: uuid.UUID, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> dict[str, Any] | None:
    row = conn.execute(
        """
        select id, event_id, user_id, title, created_at, updated_at
          from public.ai_conversations
         where id = %s and event_id = %s and user_id = %s
        """,
        (conversation_id, event_id, user_id),
    ).fetchone()
    return dict(row) if row else None


def insert_message(
    conn: Connection,
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    proposal_id: uuid.UUID | None = None,
    model_id: str | None = None,
    prompt_version: str | None = None,
    validation_status: str = "not_applicable",
) -> dict[str, Any]:
    row = conn.execute(
        """
        insert into public.ai_messages
          (conversation_id, proposal_id, role, content, model_id, prompt_version, validation_status)
        values
          (%s, %s, %s, %s, %s, %s, %s)
        returning id, conversation_id, proposal_id, role, content, validation_status, created_at
        """,
        (conversation_id, proposal_id, role, content, model_id, prompt_version, validation_status),
    ).fetchone()
    assert row is not None
    # Touch conversation updated_at
    conn.execute(
        "update public.ai_conversations set updated_at = now() where id = %s",
        (conversation_id,),
    )
    return dict(row)


def list_messages(conn: Connection, conversation_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select id, conversation_id, proposal_id, role, content, validation_status, created_at
          from public.ai_messages
         where conversation_id = %s
         order by created_at asc
        """,
        (conversation_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def insert_proposal(
    conn: Connection,
    event_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    created_by: uuid.UUID,
    proposal_type: str,
    base_revision: int,
    schema_version: int,
    payload: dict[str, Any],
    model_id: str | None = None,
    prompt_version: str | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        """
        insert into public.ai_proposals
          (event_id, conversation_id, created_by, proposal_type, base_revision,
           schema_version, payload, status, model_id, prompt_version)
        values
          (%s, %s, %s, %s, %s, %s, %s, 'proposed', %s, %s)
        returning id, event_id, conversation_id, base_revision, schema_version,
                  payload, status, model_id, prompt_version, created_at, accepted_at
        """,
        (
            event_id,
            conversation_id,
            created_by,
            proposal_type,
            base_revision,
            schema_version,
            json.dumps(payload),
            model_id,
            prompt_version,
        ),
    ).fetchone()
    assert row is not None
    return dict(row)


def get_proposal(conn: Connection, event_id: uuid.UUID, proposal_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        """
        select id, event_id, conversation_id, base_revision, schema_version,
               payload, status, model_id, prompt_version, created_at, accepted_at
          from public.ai_proposals
         where id = %s and event_id = %s
        """,
        (proposal_id, event_id),
    ).fetchone()
    return dict(row) if row else None


def update_proposal_status(
    conn: Connection,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    status: str,
    accepted_at: datetime | None = None,
) -> None:
    conn.execute(
        """
        update public.ai_proposals
           set status = %s, accepted_at = %s
         where id = %s and event_id = %s
        """,
        (status, accepted_at, proposal_id, event_id),
    )


def mark_outdated_proposals_stale(conn: Connection, event_id: uuid.UUID, current_revision: int) -> int:
    result = conn.execute(
        """
        update public.ai_proposals
           set status = 'stale'
         where event_id = %s
           and status in ('proposed', 'partially_accepted')
           and base_revision < %s
        """,
        (event_id, current_revision),
    )
    return result.rowcount

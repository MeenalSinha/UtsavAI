from __future__ import annotations

import uuid
from typing import Any

from psycopg.types.json import Jsonb

from app.database.pool import Connection


def record(
    conn: Connection,
    *,
    event_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    request_id: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append an audit row inside the caller's transaction. Never pass raw PII or secrets."""
    conn.execute(
        "insert into public.audit_logs "
        "(event_id, actor_user_id, actor_type, action, entity_type, entity_id, metadata, request_id) "
        "values (%s, %s, 'user', %s, %s, %s, %s, %s)",
        (
            event_id,
            actor_user_id,
            action,
            entity_type,
            entity_id,
            Jsonb(metadata or {}),
            request_id,
        ),
    )

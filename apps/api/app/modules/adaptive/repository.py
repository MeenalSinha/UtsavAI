"""Database repository for Phase 6 Adaptive Planning change proposals."""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from psycopg import Connection
from psycopg.rows import DictRow

_PROPOSAL_COLS = """
    id, event_id, created_by, base_revision, request_text,
    requested_changes, impact_result, ai_explanation, status,
    accepted_at, accepted_revision, rules_version, schema_version,
    created_at, updated_at
"""


def create_proposal(
    conn: Connection[DictRow],
    *,
    event_id: uuid.UUID,
    created_by: uuid.UUID,
    base_revision: int,
    request_text: str,
    requested_changes: dict[str, Any],
    impact_result: dict[str, Any],
    ai_explanation: str | None,
    rules_version: str = "1.0.0",
    schema_version: int = 1,
) -> DictRow:
    query = f"""
        insert into public.change_proposals (
            event_id, created_by, base_revision, request_text,
            requested_changes, impact_result, ai_explanation,
            status, rules_version, schema_version
        )
        values (%s, %s, %s, %s, %s, %s, %s, 'proposed', %s, %s)
        returning {_PROPOSAL_COLS}
    """  # noqa: S608
    row = conn.execute(
        query,
        (
            event_id,
            created_by,
            base_revision,
            request_text,
            json.dumps(requested_changes),
            json.dumps(impact_result),
            ai_explanation,
            rules_version,
            schema_version,
        ),
    ).fetchone()
    assert row is not None
    return row


def get_proposal(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
) -> DictRow | None:
    query = f"""
        select {_PROPOSAL_COLS}
          from public.change_proposals
         where id = %s
           and event_id = %s
    """  # noqa: S608
    return conn.execute(query, (proposal_id, event_id)).fetchone()


def lock_proposal_for_update(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
) -> DictRow | None:
    query = f"""
        select {_PROPOSAL_COLS}
          from public.change_proposals
         where id = %s
           and event_id = %s
           for update
    """  # noqa: S608
    return conn.execute(query, (proposal_id, event_id)).fetchone()


def lock_event_for_update(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
) -> DictRow | None:
    return conn.execute(
        "select * from public.events where id = %s for update",
        (event_id,),
    ).fetchone()


def list_proposals(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    status: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> Sequence[DictRow]:
    conditions = ["event_id = %s"]
    params: list[Any] = [event_id]

    if status:
        conditions.append("status = %s")
        params.append(status)

    params.extend([limit, offset])
    query = f"""
        select {_PROPOSAL_COLS}
          from public.change_proposals
         where {" and ".join(conditions)}
         order by created_at desc
         limit %s offset %s
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchall()


def update_proposal_status(
    conn: Connection[DictRow],
    *,
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    status: str,
    accepted_revision: int | None = None,
) -> DictRow | None:
    query = f"""
        update public.change_proposals
           set status = %s,
               accepted_at = case when %s = 'accepted' then now() else accepted_at end,
               accepted_revision = case when %s = 'accepted' then %s else accepted_revision end,
               updated_at = now()
         where id = %s
           and event_id = %s
        returning {_PROPOSAL_COLS}
    """  # noqa: S608
    return conn.execute(
        query,
        (status, status, status, accepted_revision, proposal_id, event_id),
    ).fetchone()


def mark_other_proposals_stale(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    exclude_proposal_id: uuid.UUID,
) -> int:
    res = conn.execute(
        """
        update public.change_proposals
           set status = 'stale',
               updated_at = now()
         where event_id = %s
           and id != %s
           and status = 'proposed'
        """,
        (event_id, exclude_proposal_id),
    )
    return res.rowcount


def shift_task_due_dates(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    shift_seconds: int,
) -> int:
    res = conn.execute(
        """
        update public.tasks
           set due_at = due_at + (%s || ' seconds')::interval,
               updated_at = now()
         where event_id = %s
           and due_at is not null
           and status not in ('done', 'cancelled')
        """,
        (str(shift_seconds), event_id),
    )
    return res.rowcount


def extend_gift_registry_expiry(
    conn: Connection[DictRow],
    registry_id: uuid.UUID,
    new_expires_at: datetime,
) -> bool:
    res = conn.execute(
        """
        update public.gift_registries
           set expires_at = %s,
               updated_at = now()
         where id = %s
        """,
        (new_expires_at, registry_id),
    )
    return res.rowcount > 0

"""Persistence for events. Every statement runs under the caller's RLS identity."""

from __future__ import annotations

import base64
import binascii
import json
import uuid
from datetime import datetime
from typing import Any

from psycopg import sql

from app.core.domain import EventSort
from app.core.errors import InvalidRequestError
from app.database.pool import Connection

_SELECT = """
select e.id, e.event_type, e.title, e.start_at, e.end_at, e.timezone,
       e.location_name, e.city, e.region, e.country_code,
       e.expected_guest_count, e.currency, e.status, e.revision,
       e.created_at, e.updated_at, e.archived_at, m.role as my_role
  from public.events e
  join public.event_members m
    on m.event_id = e.id
   and m.user_id = app.current_user_id()
   and m.status = 'active'
"""

UPDATABLE_COLUMNS = frozenset(
    {
        "title", "start_at", "end_at", "timezone", "location_name", "city", "region",
        "country_code", "expected_guest_count", "currency", "status",
    }
)  # fmt: skip


def insert_event(conn: Connection, owner_id: uuid.UUID, values: dict[str, Any]) -> uuid.UUID:
    row = conn.execute(
        """
        insert into public.events
          (owner_user_id, event_type, title, start_at, end_at, timezone,
           location_name, city, region, country_code, expected_guest_count, currency)
        values
          (%(owner)s, %(event_type)s, %(title)s, %(start_at)s, %(end_at)s, %(timezone)s,
           %(location_name)s, %(city)s, %(region)s, %(country_code)s,
           %(expected_guest_count)s, %(currency)s)
        returning id
        """,
        {**values, "owner": owner_id},
    ).fetchone()
    assert row is not None
    return row["id"]  # type: ignore[no-any-return]


def insert_owner_membership(conn: Connection, event_id: uuid.UUID, user_id: uuid.UUID) -> None:
    conn.execute(
        "insert into public.event_members (event_id, user_id, role, status) "
        "values (%s, %s, 'owner', 'active')",
        (event_id, user_id),
    )


def get_event(conn: Connection, event_id: uuid.UUID, *, for_update: bool = False) -> dict[str, Any] | None:
    suffix = " for update of e" if for_update else ""
    return conn.execute(f"{_SELECT} where e.id = %s{suffix}", (event_id,)).fetchone()  # noqa: S608


def update_event(
    conn: Connection, event_id: uuid.UUID, expected_revision: int, fields: dict[str, Any]
) -> bool:
    unknown = set(fields) - UPDATABLE_COLUMNS
    if unknown:
        raise ValueError(f"fields not updatable: {sorted(unknown)}")
    assignments = sql.SQL(", ").join(
        sql.SQL("{} = {}").format(sql.Identifier(name), sql.Placeholder(name)) for name in fields
    )
    query = sql.SQL(
        "update public.events set {assignments} where id = %(_id)s and revision = %(_rev)s returning id"
    ).format(assignments=assignments)
    row = conn.execute(query, {**fields, "_id": event_id, "_rev": expected_revision}).fetchone()
    return row is not None


def archive_event(conn: Connection, event_id: uuid.UUID) -> bool:
    row = conn.execute(
        "update public.events set status = 'archived' where id = %s and status <> 'archived' returning id",
        (event_id,),
    ).fetchone()
    return row is not None


# ----------------------------------------------------------------- listing


def encode_cursor(sort: EventSort, value: datetime, event_id: uuid.UUID) -> str:
    raw = json.dumps({"s": sort.value, "v": value.isoformat(), "id": str(event_id)})
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(cursor: str, sort: EventSort) -> tuple[datetime, uuid.UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if data["s"] != sort.value:
            raise ValueError("sort mismatch")
        return datetime.fromisoformat(data["v"]), uuid.UUID(data["id"])
    except (ValueError, KeyError, TypeError, binascii.Error, json.JSONDecodeError) as exc:
        raise InvalidRequestError("The cursor is invalid.") from exc


# Fixed expressions only. Client-supplied sort names are mapped, never interpolated.
_SORTS: dict[EventSort, tuple[str, str, str]] = {
    EventSort.START_ASC: ("e.start_at", "asc", ">"),
    EventSort.CREATED_DESC: ("e.created_at", "desc", "<"),
}


def list_events(
    conn: Connection,
    *,
    statuses: list[str],
    sort: EventSort,
    limit: int,
    cursor: tuple[datetime, uuid.UUID] | None,
) -> list[dict[str, Any]]:
    column, direction, comparator = _SORTS[sort]
    params: dict[str, Any] = {"statuses": statuses, "limit": limit + 1}
    cursor_clause = ""
    if cursor is not None:
        cursor_clause = f" and ({column}, e.id) {comparator} (%(c_value)s, %(c_id)s)"
        params.update(c_value=cursor[0], c_id=cursor[1])
    query = (
        f"{_SELECT} where e.status = any(%(statuses)s){cursor_clause} "  # noqa: S608
        f"order by {column} {direction}, e.id {direction} limit %(limit)s"
    )
    return conn.execute(query, params).fetchall()

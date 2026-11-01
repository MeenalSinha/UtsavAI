"""Persistence for event functions."""

from __future__ import annotations

import uuid
from typing import Any

from psycopg import sql

from app.database.pool import Connection

UPDATABLE_COLUMNS = frozenset({"name", "starts_at", "ends_at", "location_name", "notes", "sort_order"})


def list_functions(conn: Connection, event_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        select id, event_id, name, starts_at, ends_at, location_name,
               notes, sort_order, created_at, updated_at
          from public.event_functions
         where event_id = %s and not is_deleted
         order by sort_order asc, starts_at asc nulls last, created_at asc
        """,
        (event_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_function(conn: Connection, event_id: uuid.UUID, function_id: uuid.UUID) -> dict[str, Any] | None:
    row = conn.execute(
        """
        select id, event_id, name, starts_at, ends_at, location_name,
               notes, sort_order, created_at, updated_at
          from public.event_functions
         where id = %s and event_id = %s and not is_deleted
        """,
        (function_id, event_id),
    ).fetchone()
    return dict(row) if row else None


def insert_function(conn: Connection, event_id: uuid.UUID, values: dict[str, Any]) -> dict[str, Any]:
    row = conn.execute(
        """
        insert into public.event_functions
          (event_id, name, starts_at, ends_at, location_name, notes, sort_order)
        values
          (%(event_id)s, %(name)s, %(starts_at)s, %(ends_at)s, %(location_name)s, %(notes)s, %(sort_order)s)
        returning id, event_id, name, starts_at, ends_at, location_name,
                  notes, sort_order, created_at, updated_at
        """,
        {**values, "event_id": event_id},
    ).fetchone()
    assert row is not None
    return dict(row)


def update_function(
    conn: Connection, event_id: uuid.UUID, function_id: uuid.UUID, values: dict[str, Any]
) -> dict[str, Any] | None:
    fields = [k for k in values if k in UPDATABLE_COLUMNS]
    if not fields:
        return get_function(conn, event_id, function_id)

    set_clauses = [sql.SQL("{} = {}").format(sql.Identifier(k), sql.Placeholder(k)) for k in fields]
    query = sql.SQL(
        """
        update public.event_functions
           set {sets}
         where id = {fid} and event_id = {eid} and not is_deleted
        returning id, event_id, name, starts_at, ends_at, location_name,
                  notes, sort_order, created_at, updated_at
        """
    ).format(
        sets=sql.SQL(", ").join(set_clauses),
        fid=sql.Placeholder("func_id"),
        eid=sql.Placeholder("event_id"),
    )
    params = {**values, "func_id": function_id, "event_id": event_id}
    row = conn.execute(query, params).fetchone()
    return dict(row) if row else None


def delete_function(conn: Connection, event_id: uuid.UUID, function_id: uuid.UUID) -> bool:
    row = conn.execute(
        "select app.delete_event_function(%s, %s) as deleted",
        (event_id, function_id),
    ).fetchone()
    return bool(row["deleted"]) if row else False

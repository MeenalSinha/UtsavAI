"""Task and Dependency repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from psycopg import Connection
from psycopg.rows import DictRow

_TASK_COLS = (
    "id, event_id, function_id, title, description, due_at, "
    "status, priority, assigned_user_id, origin, sort_order, "
    "created_at, updated_at, completed_at"
)


def list_tasks(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    status: str | None = None,
    priority: str | None = None,
    function_id: uuid.UUID | None = None,
    assigned_user_id: uuid.UUID | None = None,
    search: str | None = None,
) -> Sequence[DictRow]:
    conditions = ["event_id = %s"]
    params: list[Any] = [event_id]

    if status:
        conditions.append("status = %s")
        params.append(status)
    if priority:
        conditions.append("priority = %s")
        params.append(priority)
    if function_id:
        conditions.append("function_id = %s")
        params.append(function_id)
    if assigned_user_id:
        conditions.append("assigned_user_id = %s")
        params.append(assigned_user_id)
    if search:
        conditions.append("(title ilike %s or description ilike %s)")
        q = f"%{search.strip()}%"
        params.extend([q, q])

    query = f"""
        select {_TASK_COLS}
          from public.tasks
         where {" and ".join(conditions)}
         order by sort_order asc, due_at asc nulls last, created_at asc
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchall()


def get_task(conn: Connection[DictRow], event_id: uuid.UUID, task_id: uuid.UUID) -> DictRow | None:
    query = f"""
        select {_TASK_COLS}
          from public.tasks
         where id = %s
           and event_id = %s
    """  # noqa: S608
    return conn.execute(query, (task_id, event_id)).fetchone()


def create_task(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    title: str,
    description: str | None = None,
    due_at: datetime | None = None,
    priority: str = "medium",
    function_id: uuid.UUID | None = None,
    assigned_user_id: uuid.UUID | None = None,
    origin: str = "manual",
    sort_order: int = 0,
) -> DictRow:
    query = f"""
        insert into public.tasks (
            event_id, title, description, due_at, priority,
            function_id, assigned_user_id, origin, sort_order
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        returning {_TASK_COLS}
    """  # noqa: S608
    row = conn.execute(
        query,
        (
            event_id,
            title,
            description,
            due_at,
            priority,
            function_id,
            assigned_user_id,
            origin,
            sort_order,
        ),
    ).fetchone()
    assert row is not None
    return row


def update_task(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    title: str | None = None,
    description: str | None = None,
    due_at: datetime | None = None,
    status: str | None = None,
    priority: str | None = None,
    function_id: uuid.UUID | None = None,
    assigned_user_id: uuid.UUID | None = None,
    sort_order: int | None = None,
    completed_at: datetime | None = None,
) -> DictRow | None:
    fields: list[str] = []
    params: list[Any] = []

    if title is not None:
        fields.append("title = %s")
        params.append(title)
    if description is not None:
        fields.append("description = %s")
        params.append(description)
    if due_at is not None:
        fields.append("due_at = %s")
        params.append(due_at)
    if status is not None:
        fields.append("status = %s")
        params.append(status)
    if priority is not None:
        fields.append("priority = %s")
        params.append(priority)
    if function_id is not None:
        fields.append("function_id = %s")
        params.append(function_id)
    if assigned_user_id is not None:
        fields.append("assigned_user_id = %s")
        params.append(assigned_user_id)
    if sort_order is not None:
        fields.append("sort_order = %s")
        params.append(sort_order)
    if completed_at is not None:
        fields.append("completed_at = %s")
        params.append(completed_at)

    if not fields:
        return get_task(conn, event_id, task_id)

    fields.append("updated_at = now()")
    params.extend([task_id, event_id])
    query = f"""
        update public.tasks
           set {", ".join(fields)}
         where id = %s
           and event_id = %s
        returning {_TASK_COLS}
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchone()


def cancel_task(conn: Connection[DictRow], event_id: uuid.UUID, task_id: uuid.UUID) -> bool:
    res = conn.execute(
        """
        update public.tasks
           set status = 'cancelled',
               updated_at = now()
         where id = %s
           and event_id = %s
        """,
        (task_id, event_id),
    )
    return res.rowcount > 0


def list_event_dependencies(conn: Connection[DictRow], event_id: uuid.UUID) -> Sequence[DictRow]:
    return conn.execute(
        """
        select d.task_id, d.depends_on_task_id, d.created_at
          from public.task_dependencies d
          join public.tasks t on t.id = d.task_id
         where t.event_id = %s
           and not coalesce(d.is_deleted, false)
        """,
        (event_id,),
    ).fetchall()


def get_task_dependencies(conn: Connection[DictRow], task_id: uuid.UUID) -> Sequence[uuid.UUID]:
    rows = conn.execute(
        """
        select depends_on_task_id
          from public.task_dependencies
         where task_id = %s
           and not coalesce(is_deleted, false)
        """,
        (task_id,),
    ).fetchall()
    return [r["depends_on_task_id"] for r in rows]


def add_dependency(conn: Connection[DictRow], task_id: uuid.UUID, depends_on_task_id: uuid.UUID) -> None:
    conn.execute(
        """
        insert into public.task_dependencies (task_id, depends_on_task_id, is_deleted)
        values (%s, %s, false)
        on conflict (task_id, depends_on_task_id) do update set is_deleted = false
        """,
        (task_id, depends_on_task_id),
    )


def remove_dependency(conn: Connection[DictRow], task_id: uuid.UUID, depends_on_task_id: uuid.UUID) -> bool:
    res = conn.execute(
        """
        update public.task_dependencies
           set is_deleted = true
         where task_id = %s
           and depends_on_task_id = %s
           and not coalesce(is_deleted, false)
        """,
        (task_id, depends_on_task_id),
    )
    return res.rowcount > 0

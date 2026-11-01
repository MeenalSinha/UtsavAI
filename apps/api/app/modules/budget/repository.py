"""Budget and Expense repository."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from psycopg import Connection
from psycopg.rows import DictRow

_CAT_COLS = (
    "id, budget_id, category_key, name, planned_amount, sort_order, is_deleted, created_at, updated_at"
)

_EXP_COLS = (
    "id, event_id, budget_category_id, vendor_id, description, "
    "amount, currency, expense_date, status, created_by, created_at, updated_at"
)


def get_budget(conn: Connection[DictRow], event_id: uuid.UUID) -> DictRow | None:
    return conn.execute(
        """
        select id, event_id, total_limit, currency, created_at, updated_at
          from public.budgets
         where event_id = %s
        """,
        (event_id,),
    ).fetchone()


def create_budget(
    conn: Connection[DictRow], event_id: uuid.UUID, total_limit: Decimal, currency: str
) -> DictRow:
    row = conn.execute(
        """
        insert into public.budgets (event_id, total_limit, currency)
        values (%s, %s, %s)
        returning id, event_id, total_limit, currency, created_at, updated_at
        """,
        (event_id, total_limit, currency),
    ).fetchone()
    assert row is not None
    return row


def update_budget(conn: Connection[DictRow], event_id: uuid.UUID, total_limit: Decimal) -> DictRow | None:
    return conn.execute(
        """
        update public.budgets
           set total_limit = %s,
               updated_at = now()
         where event_id = %s
        returning id, event_id, total_limit, currency, created_at, updated_at
        """,
        (total_limit, event_id),
    ).fetchone()


def list_categories(conn: Connection[DictRow], budget_id: uuid.UUID) -> Sequence[DictRow]:
    query = f"""
        select {_CAT_COLS}
          from public.budget_categories
         where budget_id = %s
           and not is_deleted
         order by sort_order asc, created_at asc
    """  # noqa: S608
    return conn.execute(query, (budget_id,)).fetchall()


def get_category(conn: Connection[DictRow], category_id: uuid.UUID) -> DictRow | None:
    query = f"""
        select {_CAT_COLS}
          from public.budget_categories
         where id = %s
           and not is_deleted
    """  # noqa: S608
    return conn.execute(query, (category_id,)).fetchone()


def get_category_by_key(conn: Connection[DictRow], budget_id: uuid.UUID, category_key: str) -> DictRow | None:
    query = f"""
        select {_CAT_COLS}
          from public.budget_categories
         where budget_id = %s
           and category_key = %s
           and not is_deleted
    """  # noqa: S608
    return conn.execute(query, (budget_id, category_key)).fetchone()


def create_category(
    conn: Connection[DictRow],
    budget_id: uuid.UUID,
    category_key: str,
    name: str,
    planned_amount: Decimal,
    sort_order: int = 0,
) -> DictRow:
    query = f"""
        insert into public.budget_categories (budget_id, category_key, name, planned_amount, sort_order)
        values (%s, %s, %s, %s, %s)
        returning {_CAT_COLS}
    """  # noqa: S608
    row = conn.execute(query, (budget_id, category_key, name, planned_amount, sort_order)).fetchone()
    assert row is not None
    return row


def update_category(
    conn: Connection[DictRow],
    category_id: uuid.UUID,
    name: str | None = None,
    planned_amount: Decimal | None = None,
    sort_order: int | None = None,
) -> DictRow | None:
    fields: list[str] = []
    params: list[Any] = []
    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if planned_amount is not None:
        fields.append("planned_amount = %s")
        params.append(planned_amount)
    if sort_order is not None:
        fields.append("sort_order = %s")
        params.append(sort_order)

    if not fields:
        return get_category(conn, category_id)

    fields.append("updated_at = now()")
    params.append(category_id)
    query = f"""
        update public.budget_categories
           set {", ".join(fields)}
         where id = %s
           and not is_deleted
        returning {_CAT_COLS}
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchone()


def delete_category(conn: Connection[DictRow], category_id: uuid.UUID) -> bool:
    res = conn.execute(
        """
        update public.budget_categories
           set is_deleted = true,
               updated_at = now()
         where id = %s
           and not is_deleted
        """,
        (category_id,),
    )
    return res.rowcount > 0


def count_active_expenses_for_category(conn: Connection[DictRow], category_id: uuid.UUID) -> int:
    row = conn.execute(
        """
        select count(*) as cnt
          from public.expenses
         where budget_category_id = %s
           and not is_deleted
           and status <> 'cancelled'
        """,
        (category_id,),
    ).fetchone()
    return int(row["cnt"]) if row else 0


def list_expenses(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    category_id: uuid.UUID | None = None,
    status: str | None = None,
    search: str | None = None,
) -> Sequence[DictRow]:
    conditions = ["event_id = %s", "not is_deleted"]
    params: list[Any] = [event_id]

    if category_id:
        conditions.append("budget_category_id = %s")
        params.append(category_id)
    if status:
        conditions.append("status = %s")
        params.append(status)
    if search:
        conditions.append("description ilike %s")
        params.append(f"%{search.strip()}%")

    query = f"""
        select {_EXP_COLS}
          from public.expenses
         where {" and ".join(conditions)}
         order by expense_date desc, created_at desc
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchall()


def get_expense(conn: Connection[DictRow], event_id: uuid.UUID, expense_id: uuid.UUID) -> DictRow | None:
    query = f"""
        select {_EXP_COLS}
          from public.expenses
         where id = %s
           and event_id = %s
           and not is_deleted
    """  # noqa: S608
    return conn.execute(query, (expense_id, event_id)).fetchone()


def create_expense(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    budget_category_id: uuid.UUID,
    description: str,
    amount: Decimal,
    currency: str,
    expense_date: date,
    status: str,
    created_by: uuid.UUID,
    vendor_id: uuid.UUID | None = None,
) -> DictRow:
    query = f"""
        insert into public.expenses (
            event_id, budget_category_id, vendor_id, description,
            amount, currency, expense_date, status, created_by
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        returning {_EXP_COLS}
    """  # noqa: S608
    row = conn.execute(
        query,
        (
            event_id,
            budget_category_id,
            vendor_id,
            description,
            amount,
            currency,
            expense_date,
            status,
            created_by,
        ),
    ).fetchone()
    assert row is not None
    return row


def update_expense(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    expense_id: uuid.UUID,
    budget_category_id: uuid.UUID | None = None,
    description: str | None = None,
    amount: Decimal | None = None,
    expense_date: date | None = None,
    status: str | None = None,
    vendor_id: uuid.UUID | None = None,
) -> DictRow | None:
    fields: list[str] = []
    params: list[Any] = []
    if budget_category_id is not None:
        fields.append("budget_category_id = %s")
        params.append(budget_category_id)
    if description is not None:
        fields.append("description = %s")
        params.append(description)
    if amount is not None:
        fields.append("amount = %s")
        params.append(amount)
    if expense_date is not None:
        fields.append("expense_date = %s")
        params.append(expense_date)
    if status is not None:
        fields.append("status = %s")
        params.append(status)
    if vendor_id is not None:
        fields.append("vendor_id = %s")
        params.append(vendor_id)

    if not fields:
        return get_expense(conn, event_id, expense_id)

    fields.append("updated_at = now()")
    params.extend([expense_id, event_id])
    query = f"""
        update public.expenses
           set {", ".join(fields)}
         where id = %s
           and event_id = %s
           and not is_deleted
        returning {_EXP_COLS}
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchone()


def delete_expense(conn: Connection[DictRow], event_id: uuid.UUID, expense_id: uuid.UUID) -> bool:
    res = conn.execute(
        """
        update public.expenses
           set is_deleted = true,
               updated_at = now()
         where id = %s
           and event_id = %s
           and not is_deleted
        """,
        (expense_id, event_id),
    )
    return res.rowcount > 0

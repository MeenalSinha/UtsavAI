"""Database repository for Phase 4 VendorConnect entities."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Any

from psycopg import Connection
from psycopg.rows import DictRow

_VENDOR_COLS = """
    id, event_id, category, name, contact_name, email,
    phone, website_url, notes, status, created_at, updated_at, archived_at
"""

_QUOTE_COLS = """
    id, vendor_id, amount, currency, scope_summary, valid_until, notes,
    status, created_at, updated_at
"""


def create_vendor(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    category: str,
    name: str,
    contact_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    website_url: str | None = None,
    notes: str | None = None,
) -> DictRow:
    query = f"""
        insert into public.event_vendors (
            event_id, category, name, contact_name, email,
            phone, website_url, notes, status
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, 'identified')
        returning {_VENDOR_COLS}
    """  # noqa: S608
    row = conn.execute(
        query,
        (event_id, category, name, contact_name, email, phone, website_url, notes),
    ).fetchone()
    assert row is not None
    return row


def get_vendor(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    include_archived: bool = True,
) -> DictRow | None:
    conditions = ["id = %s", "event_id = %s"]
    if not include_archived:
        conditions.append("archived_at is null")

    query = f"""
        select {_VENDOR_COLS}
          from public.event_vendors
         where {" and ".join(conditions)}
    """  # noqa: S608
    return conn.execute(query, (vendor_id, event_id)).fetchone()


def list_vendors(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[DictRow]:
    conditions = ["event_id = %s"]
    params: list[Any] = [event_id]

    if not include_archived:
        conditions.append("archived_at is null")
    if category:
        conditions.append("category = %s")
        params.append(category)
    if status:
        conditions.append("status = %s")
        params.append(status)
    if search:
        conditions.append("(name ilike %s or contact_name ilike %s or category ilike %s)")
        q = f"%{search.strip()}%"
        params.extend([q, q, q])

    params.extend([limit, offset])
    query = f"""
        select {_VENDOR_COLS}
          from public.event_vendors
         where {" and ".join(conditions)}
         order by created_at desc
         limit %s offset %s
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchall()


def update_vendor(
    conn: Connection[DictRow],
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    category: str | None = None,
    name: str | None = None,
    contact_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    website_url: str | None = None,
    notes: str | None = None,
    status: str | None = None,
) -> DictRow | None:
    fields: list[str] = []
    params: list[Any] = []

    if category is not None:
        fields.append("category = %s")
        params.append(category)
    if name is not None:
        fields.append("name = %s")
        params.append(name)
    if contact_name is not None:
        fields.append("contact_name = %s")
        params.append(contact_name)
    if email is not None:
        fields.append("email = %s")
        params.append(email)
    if phone is not None:
        fields.append("phone = %s")
        params.append(phone)
    if website_url is not None:
        fields.append("website_url = %s")
        params.append(website_url)
    if notes is not None:
        fields.append("notes = %s")
        params.append(notes)
    if status is not None:
        fields.append("status = %s")
        params.append(status)

    if not fields:
        return get_vendor(conn, event_id, vendor_id)

    params.extend([vendor_id, event_id])
    query = f"""
        update public.event_vendors
           set {", ".join(fields)}
         where id = %s
           and event_id = %s
        returning {_VENDOR_COLS}
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchone()


def archive_vendor(conn: Connection[DictRow], event_id: uuid.UUID, vendor_id: uuid.UUID) -> bool:
    res = conn.execute(
        """
        update public.event_vendors
           set archived_at = now(),
               status = case when status = 'booked' then 'booked' else 'declined' end
         where id = %s
           and event_id = %s
           and archived_at is null
        """,
        (vendor_id, event_id),
    )
    return res.rowcount > 0


# ------------------------------------------------------------------ Quotation Repository
def create_quote(
    conn: Connection[DictRow],
    vendor_id: uuid.UUID,
    amount: Decimal,
    currency: str,
    scope_summary: str,
    valid_until: date | None = None,
    notes: str | None = None,
) -> DictRow:
    query = f"""
        insert into public.vendor_quotes (
            vendor_id, amount, currency, scope_summary, valid_until, notes, status
        )
        values (%s, %s, %s, %s, %s, %s, 'received')
        returning {_QUOTE_COLS}
    """  # noqa: S608
    row = conn.execute(
        query,
        (vendor_id, amount, currency, scope_summary, valid_until, notes),
    ).fetchone()
    assert row is not None
    return row


def get_quote(conn: Connection[DictRow], vendor_id: uuid.UUID, quote_id: uuid.UUID) -> DictRow | None:
    query = f"""
        select {_QUOTE_COLS}
          from public.vendor_quotes
         where id = %s
           and vendor_id = %s
    """  # noqa: S608
    return conn.execute(query, (quote_id, vendor_id)).fetchone()


def list_quotes_for_vendor(conn: Connection[DictRow], vendor_id: uuid.UUID) -> Sequence[DictRow]:
    query = f"""
        select {_QUOTE_COLS}
          from public.vendor_quotes
         where vendor_id = %s
         order by created_at desc
    """  # noqa: S608
    return conn.execute(query, (vendor_id,)).fetchall()


def list_all_event_quotes(conn: Connection[DictRow], event_id: uuid.UUID) -> Sequence[DictRow]:
    query = """
        select q.id as quote_id, q.amount, q.currency, q.scope_summary, q.valid_until,
               q.notes as quote_notes, q.status as quote_status, q.created_at as quote_created_at,
               q.updated_at as quote_updated_at,
               v.id as vendor_id, v.name as vendor_name, v.category, v.status as vendor_status,
               v.contact_name, v.email, v.phone, v.website_url, v.archived_at
          from public.vendor_quotes q
          join public.event_vendors v on v.id = q.vendor_id
         where v.event_id = %s
           and v.archived_at is null
         order by v.category asc, q.amount asc
    """
    return conn.execute(query, (event_id,)).fetchall()


def update_quote(
    conn: Connection[DictRow],
    vendor_id: uuid.UUID,
    quote_id: uuid.UUID,
    amount: Decimal | None = None,
    currency: str | None = None,
    scope_summary: str | None = None,
    valid_until: date | None = None,
    notes: str | None = None,
    status: str | None = None,
) -> DictRow | None:
    fields: list[str] = []
    params: list[Any] = []

    if amount is not None:
        fields.append("amount = %s")
        params.append(amount)
    if currency is not None:
        fields.append("currency = %s")
        params.append(currency)
    if scope_summary is not None:
        fields.append("scope_summary = %s")
        params.append(scope_summary)
    if valid_until is not None:
        fields.append("valid_until = %s")
        params.append(valid_until)
    if notes is not None:
        fields.append("notes = %s")
        params.append(notes)
    if status is not None:
        fields.append("status = %s")
        params.append(status)

    if not fields:
        return get_quote(conn, vendor_id, quote_id)

    params.extend([quote_id, vendor_id])
    query = f"""
        update public.vendor_quotes
           set {", ".join(fields)}
         where id = %s
           and vendor_id = %s
        returning {_QUOTE_COLS}
    """  # noqa: S608
    return conn.execute(query, tuple(params)).fetchone()


# ------------------------------------------------------------------ Aggregations & Metrics
def get_vendor_metrics(conn: Connection[DictRow], event_id: uuid.UUID) -> dict[str, Any]:
    # Vendor status counts
    counts_row = conn.execute(
        """
        select
            count(*) as total,
            count(*) filter (where status = 'identified' and archived_at is null) as identified,
            count(*) filter (where status = 'contacted' and archived_at is null) as contacted,
            count(*) filter (where status = 'quoted' and archived_at is null) as quoted,
            count(*) filter (where status = 'shortlisted' and archived_at is null) as shortlisted,
            count(*) filter (where status = 'booked' and archived_at is null) as booked,
            count(*) filter (where status = 'declined' or archived_at is not null) as declined
        from public.event_vendors
        where event_id = %s
        """,
        (event_id,),
    ).fetchone()

    # Category summaries
    cat_rows = conn.execute(
        """
        select
            v.category,
            count(distinct v.id) as vendor_count,
            count(distinct case when q.id is not null then v.id end) as quoted_count,
            count(distinct case when v.status = 'shortlisted' then v.id end) as shortlisted_count,
            count(distinct case when v.status = 'booked' then v.id end) as booked_count
        from public.event_vendors v
        left join public.vendor_quotes q on q.vendor_id = v.id
        where v.event_id = %s and v.archived_at is null
        group by v.category
        order by v.category
        """,
        (event_id,),
    ).fetchall()

    # Quote total count
    quotes_count_row = conn.execute(
        """
        select count(*) as total_quotes
        from public.vendor_quotes q
        join public.event_vendors v on v.id = q.vendor_id
        where v.event_id = %s and v.archived_at is null
        """,
        (event_id,),
    ).fetchone()

    total_quotes = int(quotes_count_row["total_quotes"]) if quotes_count_row else 0
    shortlisted = int(counts_row["shortlisted"]) if counts_row else 0
    quoted = int(counts_row["quoted"]) if counts_row else 0
    pending_decisions = shortlisted + quoted

    return {
        "total_vendors": int(counts_row["total"]) if counts_row else 0,
        "identified_count": int(counts_row["identified"]) if counts_row else 0,
        "contacted_count": int(counts_row["contacted"]) if counts_row else 0,
        "quoted_count": int(counts_row["quoted"]) if counts_row else 0,
        "shortlisted_count": shortlisted,
        "booked_count": int(counts_row["booked"]) if counts_row else 0,
        "declined_count": int(counts_row["declined"]) if counts_row else 0,
        "quote_count": total_quotes,
        "pending_decisions": pending_decisions,
        "categories": [
            {
                "category": r["category"],
                "vendor_count": int(r["vendor_count"]),
                "quoted_count": int(r["quoted_count"]),
                "shortlisted_count": int(r["shortlisted_count"]),
                "booked_count": int(r["booked_count"]),
            }
            for r in cat_rows
        ],
    }


def get_vendor_expense_stats(
    conn: Connection[DictRow], event_id: uuid.UUID
) -> dict[uuid.UUID, dict[str, Any]]:
    rows = conn.execute(
        """
        select vendor_id, count(*) as cnt, coalesce(sum(amount), 0) as total_spent
        from public.expenses
        where event_id = %s
          and vendor_id is not null
          and not is_deleted
          and status <> 'cancelled'
        group by vendor_id
        """,
        (event_id,),
    ).fetchall()
    return {r["vendor_id"]: {"count": int(r["cnt"]), "total": Decimal(str(r["total_spent"]))} for r in rows}


def get_vendor_latest_quotes(
    conn: Connection[DictRow], event_id: uuid.UUID
) -> dict[uuid.UUID, dict[str, Any]]:
    rows = conn.execute(
        """
        select distinct on (q.vendor_id)
            q.vendor_id, q.amount, q.currency, q.created_at
        from public.vendor_quotes q
        join public.event_vendors v on v.id = q.vendor_id
        where v.event_id = %s
        order by q.vendor_id, q.created_at desc
        """,
        (event_id,),
    ).fetchall()
    return {r["vendor_id"]: {"amount": Decimal(str(r["amount"])), "currency": r["currency"]} for r in rows}

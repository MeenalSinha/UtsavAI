"""Database access for GiftCircle entities."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from psycopg import Connection
from psycopg.rows import DictRow

Row = dict[str, Any]


# ------------------------------------------------------------------ Registries
def get_registry_by_event(conn: Connection[DictRow], event_id: uuid.UUID) -> Row | None:
    return conn.execute(
        "select id, event_id, title, is_public, share_token_hash, allow_group_gifting, "
        "expires_at, revoked_at, created_at, updated_at "
        "from public.gift_registries where event_id = %s",
        (event_id,),
    ).fetchone()


def get_public_registry_by_token_hash(conn: Connection[DictRow], token_hash: str) -> Row | None:
    return conn.execute(
        "select id, event_id, title, is_public, allow_group_gifting, expires_at, revoked_at, created_at "
        "from public.gift_registries "
        "where share_token_hash = %s "
        "  and is_public = true "
        "  and revoked_at is null "
        "  and (expires_at is null or expires_at > now())",
        (token_hash,),
    ).fetchone()


def upsert_registry(
    conn: Connection[DictRow],
    *,
    event_id: uuid.UUID,
    title: str,
    is_public: bool,
    allow_group_gifting: bool,
    expires_at: datetime | None,
) -> Row:
    return conn.execute(
        "insert into public.gift_registries (event_id, title, is_public, allow_group_gifting, expires_at) "
        "values (%s, %s, %s, %s, %s) "
        "on conflict (event_id) do update set "
        "  title = excluded.title, "
        "  is_public = excluded.is_public, "
        "  allow_group_gifting = excluded.allow_group_gifting, "
        "  expires_at = excluded.expires_at, "
        "  updated_at = now() "
        "returning id, event_id, title, is_public, share_token_hash, allow_group_gifting, "
        "expires_at, revoked_at, created_at, updated_at",
        (event_id, title, is_public, allow_group_gifting, expires_at),
    ).fetchone()  # type: ignore[return-value]


def set_share_token_hash(
    conn: Connection[DictRow],
    *,
    event_id: uuid.UUID,
    token_hash: str,
    is_public: bool = True,
) -> Row:
    return conn.execute(
        "update public.gift_registries "
        "set share_token_hash = %s, is_public = %s, revoked_at = null, updated_at = now() "
        "where event_id = %s "
        "returning id, event_id, title, is_public, share_token_hash, allow_group_gifting, "
        "expires_at, revoked_at, created_at, updated_at",
        (token_hash, is_public, event_id),
    ).fetchone()  # type: ignore[return-value]


def revoke_share_token(conn: Connection[DictRow], event_id: uuid.UUID) -> bool:
    res = conn.execute(
        "update public.gift_registries "
        "set is_public = false, revoked_at = now(), updated_at = now() "
        "where event_id = %s and revoked_at is null",
        (event_id,),
    )
    return res.rowcount > 0


# ------------------------------------------------------------------ Items
def list_items(
    conn: Connection[DictRow],
    registry_id: uuid.UUID,
    include_inactive: bool = False,
) -> list[Row]:
    query = (
        "select id, registry_id, title, description, item_type, gift_mode, "
        "product_url, target_amount, currency, priority, display_order, is_active, "
        "created_at, updated_at "
        "from public.gift_items "
        "where registry_id = %s "
    )
    if not include_inactive:
        query += " and is_active = true "
    query += " order by display_order asc, created_at asc"
    return conn.execute(query, (registry_id,)).fetchall()


def get_item(conn: Connection[DictRow], registry_id: uuid.UUID, item_id: uuid.UUID) -> Row | None:
    return conn.execute(
        "select id, registry_id, title, description, item_type, gift_mode, "
        "product_url, target_amount, currency, priority, display_order, is_active, "
        "created_at, updated_at "
        "from public.gift_items where registry_id = %s and id = %s",
        (registry_id, item_id),
    ).fetchone()


def lock_item_for_update(conn: Connection[DictRow], item_id: uuid.UUID) -> Row | None:
    return conn.execute(
        "select id, registry_id, title, item_type, gift_mode, target_amount, currency, is_active "
        "from public.gift_items where id = %s for update",
        (item_id,),
    ).fetchone()


def create_item(
    conn: Connection[DictRow],
    *,
    registry_id: uuid.UUID,
    title: str,
    description: str | None,
    item_type: str,
    gift_mode: str,
    product_url: str | None,
    target_amount: Decimal | None,
    currency: str,
    priority: str,
    display_order: int = 0,
) -> Row:
    return conn.execute(
        "insert into public.gift_items "
        "(registry_id, title, description, item_type, gift_mode, product_url, target_amount, "
        " currency, priority, display_order, is_active) "
        "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true) "
        "returning id, registry_id, title, description, item_type, gift_mode, "
        "product_url, target_amount, currency, priority, display_order, is_active, "
        "created_at, updated_at",
        (
            registry_id,
            title,
            description,
            item_type,
            gift_mode,
            product_url,
            target_amount,
            currency,
            priority,
            display_order,
        ),
    ).fetchone()  # type: ignore[return-value]


def update_item(
    conn: Connection[DictRow],
    *,
    registry_id: uuid.UUID,
    item_id: uuid.UUID,
    title: str | None = None,
    description: str | None = None,
    item_type: str | None = None,
    gift_mode: str | None = None,
    product_url: str | None = None,
    target_amount: Decimal | None = None,
    currency: str | None = None,
    priority: str | None = None,
    display_order: int | None = None,
    is_active: bool | None = None,
) -> Row | None:
    sets: list[str] = ["updated_at = now()"]
    vals: list[Any] = []
    if title is not None:
        sets.append("title = %s")
        vals.append(title)
    if description is not None:
        sets.append("description = %s")
        vals.append(description)
    if item_type is not None:
        sets.append("item_type = %s")
        vals.append(item_type)
    if gift_mode is not None:
        sets.append("gift_mode = %s")
        vals.append(gift_mode)
    if product_url is not None:
        sets.append("product_url = %s")
        vals.append(product_url)
    if target_amount is not None:
        sets.append("target_amount = %s")
        vals.append(target_amount)
    if currency is not None:
        sets.append("currency = %s")
        vals.append(currency)
    if priority is not None:
        sets.append("priority = %s")
        vals.append(priority)
    if display_order is not None:
        sets.append("display_order = %s")
        vals.append(display_order)
    if is_active is not None:
        sets.append("is_active = %s")
        vals.append(is_active)

    vals.extend([registry_id, item_id])
    return conn.execute(
        f"update public.gift_items set {', '.join(sets)} "  # noqa: S608
        f"where registry_id = %s and id = %s "
        f"returning id, registry_id, title, description, item_type, gift_mode, "
        f"product_url, target_amount, currency, priority, display_order, is_active, "
        f"created_at, updated_at",
        tuple(vals),
    ).fetchone()


def deactivate_item(conn: Connection[DictRow], registry_id: uuid.UUID, item_id: uuid.UUID) -> bool:
    res = conn.execute(
        "update public.gift_items set is_active = false, updated_at = now() "
        "where registry_id = %s and id = %s",
        (registry_id, item_id),
    )
    return res.rowcount > 0


# ------------------------------------------------------------------ Reservations
def expire_stale_reservations(conn: Connection[DictRow], gift_item_id: uuid.UUID) -> int:
    res = conn.execute(
        "update public.gift_reservations set status = 'expired', updated_at = now() "
        "where gift_item_id = %s and status = 'reserved' and expires_at is not null and expires_at <= now()",
        (gift_item_id,),
    )
    return res.rowcount


def get_active_reservation(conn: Connection[DictRow], gift_item_id: uuid.UUID) -> Row | None:
    return conn.execute(
        "select id, gift_item_id, guest_alias, status, expires_at, created_at, updated_at "
        "from public.gift_reservations "
        "where gift_item_id = %s and status in ('reserved', 'fulfilled') "
        "limit 1",
        (gift_item_id,),
    ).fetchone()


def create_reservation(
    conn: Connection[DictRow],
    *,
    gift_item_id: uuid.UUID,
    guest_alias: str | None,
    cancellation_token_hash: str | None,
    expires_at: datetime | None,
    idempotency_key: str | None,
) -> Row:
    return conn.execute(
        "insert into public.gift_reservations "
        "(gift_item_id, guest_alias, status, cancellation_token_hash, expires_at, idempotency_key) "
        "values (%s, %s, 'reserved', %s, %s, %s) "
        "returning id, gift_item_id, guest_alias, status, cancellation_token_hash, "
        "expires_at, created_at, updated_at",
        (gift_item_id, guest_alias, cancellation_token_hash, expires_at, idempotency_key),
    ).fetchone()  # type: ignore[return-value]


def get_reservation_by_cancel_token(conn: Connection[DictRow], cancel_hash: str) -> Row | None:
    return conn.execute(
        "select id, gift_item_id, guest_alias, status, expires_at, created_at, updated_at "
        "from public.gift_reservations "
        "where cancellation_token_hash = %s and status = 'reserved'",
        (cancel_hash,),
    ).fetchone()


def update_reservation_status(
    conn: Connection[DictRow],
    reservation_id: uuid.UUID,
    new_status: str,
) -> Row | None:
    return conn.execute(
        "update public.gift_reservations set status = %s, updated_at = now() "
        "where id = %s "
        "returning id, gift_item_id, guest_alias, status, expires_at, created_at, updated_at",
        (new_status, reservation_id),
    ).fetchone()


def list_reservations_for_event(conn: Connection[DictRow], event_id: uuid.UUID) -> list[Row]:
    return conn.execute(
        "select r.id, r.gift_item_id, i.title as gift_item_title, r.guest_alias, "
        "r.status, r.expires_at, r.created_at, r.updated_at "
        "from public.gift_reservations r "
        "join public.gift_items i on i.id = r.gift_item_id "
        "join public.gift_registries reg on reg.id = i.registry_id "
        "where reg.event_id = %s "
        "order by r.created_at desc",
        (event_id,),
    ).fetchall()


# ------------------------------------------------------------------ Contributions
def get_contribution_accounting(conn: Connection[DictRow], gift_item_id: uuid.UUID) -> dict[str, Decimal]:
    rows = conn.execute(
        "select status, coalesce(sum(amount), 0) as total "
        "from public.gift_contributions "
        "where gift_item_id = %s and status in ('pledged', 'verified') "
        "group by status",
        (gift_item_id,),
    ).fetchall()
    pledged = Decimal("0.00")
    verified = Decimal("0.00")
    for r in rows:
        if r["status"] == "pledged":
            pledged = Decimal(str(r["total"]))
        elif r["status"] == "verified":
            verified = Decimal(str(r["total"]))
    return {"pledged": pledged, "verified": verified, "total": pledged + verified}


def create_contribution(
    conn: Connection[DictRow],
    *,
    gift_item_id: uuid.UUID,
    guest_alias: str | None,
    amount: Decimal,
    currency: str,
    idempotency_key: str | None,
) -> Row:
    return conn.execute(
        "insert into public.gift_contributions "
        "(gift_item_id, guest_alias, amount, currency, status, idempotency_key) "
        "values (%s, %s, %s, %s, 'pledged', %s) "
        "returning id, gift_item_id, guest_alias, amount, currency, status, "
        "verification_method, verified_at, verified_by, confirmation_note, created_at, updated_at",
        (gift_item_id, guest_alias, amount, currency, idempotency_key),
    ).fetchone()  # type: ignore[return-value]


def list_contributions_for_event(conn: Connection[DictRow], event_id: uuid.UUID) -> list[Row]:
    return conn.execute(
        "select c.id, c.gift_item_id, i.title as gift_item_title, c.guest_alias, "
        "c.amount, c.currency, c.status, c.verification_method, c.verified_at, "
        "c.verified_by, c.confirmation_note, c.created_at, c.updated_at "
        "from public.gift_contributions c "
        "join public.gift_items i on i.id = c.gift_item_id "
        "join public.gift_registries reg on reg.id = i.registry_id "
        "where reg.event_id = %s "
        "order by c.created_at desc",
        (event_id,),
    ).fetchall()


def get_contribution(conn: Connection[DictRow], contribution_id: uuid.UUID) -> Row | None:
    return conn.execute(
        "select c.id, c.gift_item_id, i.title as gift_item_title, c.guest_alias, "
        "c.amount, c.currency, c.status, c.verification_method, c.verified_at, "
        "c.verified_by, c.confirmation_note, c.created_at, c.updated_at, "
        "reg.event_id "
        "from public.gift_contributions c "
        "join public.gift_items i on i.id = c.gift_item_id "
        "join public.gift_registries reg on reg.id = i.registry_id "
        "where c.id = %s",
        (contribution_id,),
    ).fetchone()


def verify_contribution(
    conn: Connection[DictRow],
    *,
    contribution_id: uuid.UUID,
    verified_by: uuid.UUID,
    confirmation_note: str | None,
    verification_method: str = "host_manual_confirmation",
) -> Row | None:
    return conn.execute(
        "update public.gift_contributions "
        "set status = 'verified', "
        "    verified_at = now(), "
        "    verified_by = %s, "
        "    verification_method = %s, "
        "    confirmation_note = %s, "
        "    updated_at = now() "
        "where id = %s and status = 'pledged' "
        "returning id, gift_item_id, guest_alias, amount, currency, status, "
        "verification_method, verified_at, verified_by, confirmation_note, created_at, updated_at",
        (verified_by, verification_method, confirmation_note, contribution_id),
    ).fetchone()


# ------------------------------------------------------------------ Idempotency Records
def get_idempotency_record(conn: Connection[DictRow], scope: str, idempotency_key: str) -> Row | None:
    return conn.execute(
        "select id, scope, idempotency_key, request_hash, response_code, "
        "response_body, created_at, expires_at "
        "from public.idempotency_records "
        "where scope = %s and idempotency_key = %s and expires_at > now()",
        (scope, idempotency_key),
    ).fetchone()


def save_idempotency_record(
    conn: Connection[DictRow],
    *,
    scope: str,
    idempotency_key: str,
    request_hash: str,
    response_code: int,
    response_body: dict[str, Any],
) -> None:
    conn.execute(
        "insert into public.idempotency_records "
        "(scope, idempotency_key, request_hash, response_code, response_body) "
        "values (%s, %s, %s, %s, %s) "
        "on conflict (scope, idempotency_key) do nothing",
        (scope, idempotency_key, request_hash, response_code, json.dumps(response_body)),
    )


# ------------------------------------------------------------------ Aggregations & Context
def get_registry_metrics(conn: Connection[DictRow], registry_id: uuid.UUID) -> dict[str, Any]:
    items = list_items(conn, registry_id, include_inactive=False)
    total_items = len(items)
    reserved_items = 0
    group_items = 0
    available_items = 0

    item_ids = [it["id"] for it in items]
    if not item_ids:
        return {
            "total_items": 0,
            "available_items": 0,
            "reserved_items": 0,
            "group_gift_items": 0,
            "total_pledged_amount": Decimal("0.00"),
            "total_confirmed_amount": Decimal("0.00"),
        }

    # Query active reservations for these items
    res_rows = conn.execute(
        "select gift_item_id from public.gift_reservations "
        "where gift_item_id = any(%s) and status in ('reserved', 'fulfilled')",
        (item_ids,),
    ).fetchall()
    reserved_set = {r["gift_item_id"] for r in res_rows}

    # Query contribution totals
    contrib_rows = conn.execute(
        "select status, coalesce(sum(amount), 0) as total "
        "from public.gift_contributions "
        "where gift_item_id = any(%s) and status in ('pledged', 'verified') "
        "group by status",
        (item_ids,),
    ).fetchall()
    total_pledged = Decimal("0.00")
    total_confirmed = Decimal("0.00")
    for cr in contrib_rows:
        if cr["status"] == "pledged":
            total_pledged = Decimal(str(cr["total"]))
        elif cr["status"] == "verified":
            total_confirmed = Decimal(str(cr["total"]))

    for it in items:
        if it["gift_mode"] == "group":
            group_items += 1
        else:
            if it["id"] in reserved_set:
                reserved_items += 1
            else:
                available_items += 1

    return {
        "total_items": total_items,
        "available_items": available_items,
        "reserved_items": reserved_items,
        "group_gift_items": group_items,
        "total_pledged_amount": total_pledged,
        "total_confirmed_amount": total_confirmed,
    }

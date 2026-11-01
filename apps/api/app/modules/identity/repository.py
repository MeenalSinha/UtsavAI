from __future__ import annotations

import uuid
from typing import Any

from app.database.pool import Connection

_PROFILE_COLUMNS = "user_id, display_name, preferred_locale, timezone"
_UPDATABLE = ("display_name", "preferred_locale", "timezone")


def ensure_profile(conn: Connection, user_id: uuid.UUID, display_name: str | None) -> dict[str, Any]:
    """Idempotent provisioning from the verified JWT subject. RLS enforces user_id = caller."""
    conn.execute(
        "insert into public.profiles (user_id, display_name) values (%s, %s) "
        "on conflict (user_id) do nothing",
        (user_id, display_name),
    )
    row = get_profile(conn, user_id)
    if row is None:  # pragma: no cover - would indicate an RLS misconfiguration
        raise RuntimeError("profile provisioning failed")
    return row


def get_profile(conn: Connection, user_id: uuid.UUID) -> dict[str, Any] | None:
    return conn.execute(
        f"select {_PROFILE_COLUMNS} from public.profiles where user_id = %s",  # noqa: S608
        (user_id,),
    ).fetchone()


def update_profile(conn: Connection, user_id: uuid.UUID, fields: dict[str, Any]) -> dict[str, Any]:
    unknown = set(fields) - set(_UPDATABLE)
    if unknown:
        raise ValueError(f"fields not updatable: {sorted(unknown)}")
    assignments = ", ".join(f"{name} = %({name})s" for name in fields)  # names are allow-listed
    row = conn.execute(
        f"update public.profiles set {assignments} where user_id = %(user_id)s "  # noqa: S608
        f"returning {_PROFILE_COLUMNS}",
        {**fields, "user_id": user_id},
    ).fetchone()
    if row is None:  # pragma: no cover
        raise RuntimeError("profile update affected no rows")
    return row

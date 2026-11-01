"""Live Supabase gate (P1-14): proves the identity-context design on YOUR Supabase project.

Run this against the real runtime connection string (pooler or direct):

    cd apps/api && DATABASE_URL='postgresql://utsavai_app.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require' \
      SUPABASE_URL=https://<ref>.supabase.co uv run python ../../scripts/verify_supabase_live.py

It creates no data. Every check is read-only or transaction-local and rolled back.
Exit code 0 means every check passed; anything else means the gate is NOT satisfied.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api"))

from app.core.config import get_settings  # noqa: E402
from app.database.pool import Database  # noqa: E402

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        failures.append(name)


def main() -> int:
    settings = get_settings()
    db = Database(settings.model_copy(update={"db_pool_min_size": 1, "db_pool_max_size": 1}))
    db.open()
    try:
        with db.transaction(None, "verify") as conn:
            role = conn.execute(
                "select rolname, rolsuper, rolbypassrls from pg_roles where rolname = current_user"
            ).fetchone()
            check(
                "runtime role is NOSUPERUSER and NOBYPASSRLS",
                role is not None and not bool(role.get("rolsuper")) and not bool(role.get("rolbypassrls")),
                str(role.get("rolname") if role else "None"),
            )
            tables = {
                str(r["relname"]): bool(r["relrowsecurity"])
                for r in conn.execute(
                    "select c.relname, c.relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace "
                    "where n.nspname='public' and c.relname in ('profiles','events','event_members','audit_logs')"
                ).fetchall()
            }
            check(
                "all four tables exist with RLS enabled",
                len(tables) == 4 and all(tables.values()),
                str(tables),
            )
            fn = conn.execute("select to_regprocedure('app.current_user_id()') as f").fetchone()
            check(
                "app.current_user_id() exists (migrations applied)",
                fn is not None and fn.get("f") is not None,
            )

        user_a, user_b = uuid.uuid4(), uuid.uuid4()
        with db.transaction(user_a, "verify-a") as conn:
            row_p = conn.execute("select pg_backend_pid() as p").fetchone()
            pid_a = row_p["p"] if row_p else None
            row_u = conn.execute("select app.current_user_id()::text as u").fetchone()
            seen = row_u["u"] if row_u else None
            check("identity visible inside its own transaction", seen == str(user_a))
        with db.transaction(user_b, "verify-b") as conn:
            row_p = conn.execute("select pg_backend_pid() as p").fetchone()
            pid_b = row_p["p"] if row_p else None
            row_u = conn.execute("select app.current_user_id()::text as u").fetchone()
            seen = row_u["u"] if row_u else None
            check("second user sees only their own identity", seen == str(user_b))
        with db.transaction(None, "verify-none") as conn:
            row_u = conn.execute("select app.current_user_id() as u").fetchone()
            seen = row_u["u"] if row_u else None
            check("no identity leaks into a following anonymous transaction", seen is None)
        print(f"INFO backend pids: {pid_a}, {pid_b} (equal pids prove the session was reused)")
    finally:
        db.close()

    if failures:
        print(f"\nGATE NOT SATISFIED: {len(failures)} check(s) failed")
        return 1
    print("\nGATE SATISFIED: identity context behaves correctly on this connection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

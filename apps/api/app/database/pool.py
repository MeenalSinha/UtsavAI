"""Connection pool and transaction-scoped database identity.

Identity is applied with set_config(..., is_local => true), so PostgreSQL discards
it at COMMIT or ROLLBACK. That keeps it correct under Supabase's transaction-mode
pooler (Supavisor/pgbouncer) where a session may be shared between clients.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import DictRow, dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

from app.core.config import Settings
from app.core.errors import DependencyUnavailableError

logger = logging.getLogger(__name__)

Connection = psycopg.Connection[DictRow]


def _reset_connection(conn: psycopg.Connection[object]) -> None:
    """Defence in depth: clear every session setting before a connection is reused."""
    conn.execute("RESET ALL")
    conn.commit()


class Database:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        options = f"-c statement_timeout={settings.db_statement_timeout_ms}"
        self.pool: ConnectionPool[Connection] = ConnectionPool(
            conninfo=settings.database_url.get_secret_value(),
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            timeout=settings.db_pool_timeout_seconds,
            kwargs={
                "row_factory": dict_row,
                "autocommit": False,
                # No server-side prepared statements: required for pgbouncer transaction mode.
                "prepare_threshold": None,
                "options": options,
                "application_name": settings.app_name,
            },
            reset=_reset_connection,
            open=False,
            name="utsavai",
        )

    def open(self) -> None:
        self.pool.open(wait=True, timeout=self._settings.db_pool_timeout_seconds)

    def close(self) -> None:
        self.pool.close()

    @contextmanager
    def transaction(self, user_id: uuid.UUID | None, request_id: str) -> Iterator[Connection]:
        """One transaction with identity context. Commits on success, rolls back on error."""
        try:
            with self.pool.connection() as conn:
                # Bound parameters only. is_local=true scopes the values to this transaction.
                conn.execute(
                    "select set_config('app.user_id', %s, true), set_config('app.request_id', %s, true)",
                    (str(user_id) if user_id else "", request_id),
                )
                yield conn
        except PoolTimeout as exc:
            logger.error("db_pool_timeout")
            raise DependencyUnavailableError("The database is temporarily unavailable.") from exc
        except psycopg.OperationalError as exc:
            logger.error("db_operational_error", extra={"error_class": type(exc).__name__})
            raise DependencyUnavailableError("The database is temporarily unavailable.") from exc

    @contextmanager
    def public_transaction(self, share_token_hash: str, request_id: str) -> Iterator[Connection]:
        """Transaction with public registry capability context. Commits on success, rolls back on error."""
        try:
            with self.pool.connection() as conn:
                conn.execute(
                    "select set_config('app.user_id', '', true), "
                    "set_config('app.request_id', %s, true), "
                    "set_config('app.share_token_hash', %s, true)",
                    (request_id, share_token_hash),
                )
                yield conn
        except PoolTimeout as exc:
            logger.error("db_pool_timeout")
            raise DependencyUnavailableError("The database is temporarily unavailable.") from exc
        except psycopg.OperationalError as exc:
            logger.error("db_operational_error", extra={"error_class": type(exc).__name__})
            raise DependencyUnavailableError("The database is temporarily unavailable.") from exc

    def verify_runtime_role(self) -> None:
        """Refuse to run as a privileged role. Called at startup and by readiness."""
        with self.transaction(None, "startup") as conn:
            row = conn.execute(
                "select r.rolname, r.rolsuper, r.rolbypassrls "
                "from pg_catalog.pg_roles r where r.rolname = current_user"
            ).fetchone()
        if row is None or row["rolsuper"] or row["rolbypassrls"]:
            raise RuntimeError(
                "The database runtime role must be NOSUPERUSER and NOBYPASSRLS "
                "(use the dedicated utsavai_app role)."
            )

    def ping(self) -> None:
        with self.transaction(None, "readiness") as conn:
            conn.execute("select 1").fetchone()

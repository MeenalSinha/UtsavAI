"""Per-request context (correlation id, actor) available to logging."""

from __future__ import annotations

from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
actor_id_var: ContextVar[str] = ContextVar("actor_id", default="-")

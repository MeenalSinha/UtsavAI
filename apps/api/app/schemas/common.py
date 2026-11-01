from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


def to_utc_z(value: datetime) -> str:
    """Serialise as ISO 8601 UTC with a trailing Z (docs/API_SPECIFICATION.md 1.3)."""
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any]
    request_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class StrictModel(BaseModel):
    """Base for request bodies: unknown fields (e.g. owner_user_id) are rejected."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

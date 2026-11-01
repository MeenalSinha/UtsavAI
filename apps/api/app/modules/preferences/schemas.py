"""Schemas for event preferences."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    style_tags: list[str] = Field(default_factory=list, max_length=20)
    cultural_context: dict[str, Any] = Field(default_factory=dict)
    priorities: dict[str, Any] = Field(default_factory=dict)
    accessibility_notes: dict[str, Any] = Field(default_factory=dict)
    schema_version: int = Field(default=1, ge=1, le=10)


class PreferencesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: uuid.UUID
    style_tags: list[str]
    cultural_context: dict[str, Any]
    priorities: dict[str, Any]
    accessibility_notes: dict[str, Any]
    schema_version: int
    updated_at: datetime

"""Schemas for event functions."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FunctionBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location_name: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)
    sort_order: int = Field(default=0, ge=-1000, le=1000)

    @model_validator(mode="after")
    def _validate_dates(self) -> Self:
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Function end time cannot be before start time.")
        return self


class FunctionCreate(FunctionBase):
    pass


class FunctionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location_name: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=4000)
    sort_order: int | None = Field(default=None, ge=-1000, le=1000)

    @model_validator(mode="after")
    def _validate_dates(self) -> Self:
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("Function end time cannot be before start time.")
        return self


class FunctionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location_name: str | None = None
    notes: str | None = None
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

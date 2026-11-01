from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    Field,
    StrictInt,
    field_serializer,
    field_validator,
    model_validator,
)

from app.core.domain import (
    ENABLED_EVENT_TYPES,
    MAX_GUEST_COUNT,
    MAX_LOCATION_NAME_LENGTH,
    MAX_LOCATION_PART_LENGTH,
    MAX_TITLE_LENGTH,
    PATCHABLE_STATUSES,
    SUPPORTED_CURRENCIES,
    EventStatus,
    MemberRole,
)
from app.modules.identity.schemas import validate_iana_timezone
from app.schemas.common import StrictModel, to_utc_z

DATE_RANGE_MESSAGE = "The event date range is invalid."
_COUNTRY = re.compile(r"^[A-Z]{2}$")

GuestCount = Annotated[StrictInt, Field(ge=0, le=MAX_GUEST_COUNT)]


def _blank_to_none(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


class LocationIn(StrictModel):
    name: str | None = Field(default=None, max_length=MAX_LOCATION_NAME_LENGTH)
    city: str | None = Field(default=None, max_length=MAX_LOCATION_PART_LENGTH)
    region: str | None = Field(default=None, max_length=MAX_LOCATION_PART_LENGTH)
    country_code: str | None = None

    @field_validator("name", "city", "region", "country_code", mode="before")
    @classmethod
    def _blank(cls, value: Any) -> Any:
        return _blank_to_none(value)

    @field_validator("country_code")
    @classmethod
    def _country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.upper()
        if not _COUNTRY.match(value):
            raise ValueError("The country code must be a two-letter ISO 3166-1 code.")
        return value


class LocationOut(BaseModel):
    name: str | None
    city: str | None
    region: str | None
    country_code: str | None


def _check_currency(value: str) -> str:
    value = value.upper()
    if value not in SUPPORTED_CURRENCIES:
        raise ValueError("The currency is not supported.")
    return value


class EventCreate(StrictModel):
    event_type: str = "wedding"
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    start_at: AwareDatetime
    end_at: AwareDatetime
    timezone: str
    location: LocationIn = Field(default_factory=LocationIn)
    expected_guest_count: GuestCount = 0
    currency: str = "INR"

    @field_validator("event_type")
    @classmethod
    def _event_type(cls, value: str) -> str:
        value = value.lower()
        if value not in ENABLED_EVENT_TYPES:
            raise ValueError("The event category is not available.")
        return value

    @field_validator("timezone")
    @classmethod
    def _timezone(cls, value: str) -> str:
        return validate_iana_timezone(value)

    @field_validator("currency")
    @classmethod
    def _currency(cls, value: str) -> str:
        return _check_currency(value)

    @model_validator(mode="after")
    def _range(self) -> Self:
        if self.end_at < self.start_at:
            raise ValueError(DATE_RANGE_MESSAGE)
        return self


class EventUpdate(StrictModel):
    """Only permitted fields. Provided-but-null is rejected for required columns."""

    title: str | None = Field(default=None, min_length=1, max_length=MAX_TITLE_LENGTH)
    start_at: AwareDatetime | None = None
    end_at: AwareDatetime | None = None
    timezone: str | None = None
    location: LocationIn | None = None
    expected_guest_count: GuestCount | None = None
    currency: str | None = None
    status: EventStatus | None = None

    @field_validator("timezone")
    @classmethod
    def _timezone(cls, value: str | None) -> str | None:
        return None if value is None else validate_iana_timezone(value)

    @field_validator("currency")
    @classmethod
    def _currency(cls, value: str | None) -> str | None:
        return None if value is None else _check_currency(value)

    @field_validator("status")
    @classmethod
    def _status(cls, value: EventStatus | None) -> EventStatus | None:
        if value is not None and value not in PATCHABLE_STATUSES:
            raise ValueError("Use DELETE to archive an event.")
        return value

    @model_validator(mode="after")
    def _shape(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        required = ("title", "start_at", "end_at", "timezone", "expected_guest_count", "currency")
        for name in (*required, "status"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null.")
        if self.start_at is not None and self.end_at is not None and self.end_at < self.start_at:
            raise ValueError(DATE_RANGE_MESSAGE)
        return self


class EventOut(BaseModel):
    id: uuid.UUID
    event_type: str
    title: str
    start_at: datetime
    end_at: datetime
    timezone: str
    location: LocationOut
    expected_guest_count: int
    currency: str
    status: EventStatus
    revision: int
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    my_role: MemberRole

    @field_serializer("start_at", "end_at", "created_at", "updated_at")
    def _ser(self, value: datetime) -> str:
        return to_utc_z(value)

    @field_serializer("archived_at")
    def _ser_optional(self, value: datetime | None) -> str | None:
        return None if value is None else to_utc_z(value)


class EventPage(BaseModel):
    data: list[EventOut]
    next_cursor: str | None = None

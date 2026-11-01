from __future__ import annotations

from typing import Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.domain import MAX_DISPLAY_NAME_LENGTH, SUPPORTED_LOCALES
from app.schemas.common import StrictModel


def validate_iana_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, OSError) as exc:
        raise ValueError("The time zone is not a valid IANA time zone.") from exc
    if "/" not in value and value != "UTC":
        raise ValueError("The time zone is not a valid IANA time zone.")
    return value


class ProfileOut(BaseModel):
    user_id: str
    display_name: str | None
    preferred_locale: str
    timezone: str | None
    email: str | None = None


class ProfileUpdate(StrictModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=MAX_DISPLAY_NAME_LENGTH)
    preferred_locale: str | None = None
    timezone: str | None = None

    @field_validator("preferred_locale")
    @classmethod
    def _locale(cls, value: str | None) -> str | None:
        if value is not None and value not in SUPPORTED_LOCALES:
            raise ValueError("The locale is not supported.")
        return value

    @field_validator("timezone")
    @classmethod
    def _timezone(cls, value: str | None) -> str | None:
        return None if value is None else validate_iana_timezone(value)

    @model_validator(mode="after")
    def _at_least_one(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        if "preferred_locale" in self.model_fields_set and self.preferred_locale is None:
            raise ValueError("The locale cannot be cleared.")
        return self

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core import domain

router = APIRouter(tags=["meta"])


class EventTypeOut(BaseModel):
    key: str
    label: str
    enabled: bool


class MetaOut(BaseModel):
    event_types: list[EventTypeOut]
    default_event_type: str
    currencies: list[str]
    default_currency: str
    event_statuses: list[str]
    patchable_statuses: list[str]
    status_transitions: dict[str, list[str]]
    locales: list[str]
    default_locale: str
    default_timezone: str
    default_country_code: str
    suggested_country_codes: list[str]
    limits: dict[str, int]


@router.get("/meta", response_model=MetaOut, summary="Public, non-secret application configuration")
def meta() -> MetaOut:
    return MetaOut(
        event_types=[EventTypeOut(key=t.key, label=t.label, enabled=t.enabled) for t in domain.EVENT_TYPES],
        default_event_type=domain.DEFAULT_EVENT_TYPE,
        currencies=list(domain.SUPPORTED_CURRENCIES),
        default_currency=domain.DEFAULT_CURRENCY,
        event_statuses=[s.value for s in domain.EventStatus],
        patchable_statuses=sorted(s.value for s in domain.PATCHABLE_STATUSES),
        status_transitions={
            k.value: sorted(v.value for v in vs) for k, vs in domain.STATUS_TRANSITIONS.items()
        },
        locales=list(domain.SUPPORTED_LOCALES),
        default_locale=domain.DEFAULT_LOCALE,
        default_timezone=domain.DEFAULT_TIMEZONE,
        default_country_code=domain.DEFAULT_COUNTRY_CODE,
        suggested_country_codes=list(domain.SUGGESTED_COUNTRY_CODES),
        limits={
            "title_max": domain.MAX_TITLE_LENGTH,
            "location_name_max": domain.MAX_LOCATION_NAME_LENGTH,
            "location_part_max": domain.MAX_LOCATION_PART_LENGTH,
            "guest_count_max": domain.MAX_GUEST_COUNT,
            "display_name_max": domain.MAX_DISPLAY_NAME_LENGTH,
            "page_size_default": domain.DEFAULT_PAGE_SIZE,
            "page_size_max": domain.MAX_PAGE_SIZE,
        },
    )

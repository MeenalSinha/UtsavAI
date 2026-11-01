import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.domain import (
    ENABLED_EVENT_TYPES,
    ROLE_PERMISSIONS,
    STATUS_TRANSITIONS,
    EventSort,
    EventStatus,
    MemberRole,
    Permission,
    role_allows,
)
from app.core.errors import InvalidRequestError, PreconditionRequiredError
from app.modules.events.preconditions import etag, parse_if_match
from app.modules.events.repository import decode_cursor, encode_cursor
from app.modules.events.schemas import EventCreate, EventUpdate
from app.modules.identity.schemas import ProfileUpdate


def valid(**kw):
    body = {
        "title": "My Wedding",
        "start_at": "2027-02-12T10:00:00+05:30",
        "end_at": "2027-02-14T22:00:00+05:30",
        "timezone": "Asia/Kolkata",
    }
    body.update(kw)
    return body


def test_valid_event_defaults():
    e = EventCreate(**valid())
    assert e.event_type == "wedding" and e.currency == "INR" and e.expected_guest_count == 0
    assert e.location.country_code is None


def test_end_before_start_rejected_with_documented_message():
    with pytest.raises(ValidationError, match="The event date range is invalid"):
        EventCreate(**valid(end_at="2027-02-11T10:00:00+05:30"))


def test_equal_start_and_end_allowed():
    EventCreate(**valid(end_at="2027-02-12T10:00:00+05:30"))


def test_naive_datetime_rejected():
    with pytest.raises(ValidationError):
        EventCreate(**valid(start_at="2027-02-12T10:00:00"))


@pytest.mark.parametrize("count", [-1, 100_001, 1.5, "300", True])
def test_guest_count_validation(count):
    with pytest.raises(ValidationError):
        EventCreate(**valid(expected_guest_count=count))


def test_zero_guest_count_allowed():
    assert EventCreate(**valid(expected_guest_count=0)).expected_guest_count == 0


@pytest.mark.parametrize("category", ["nonsense", "", "space_mission", "unsupported_event"])
def test_only_enabled_categories_accepted(category):
    with pytest.raises(ValidationError):
        EventCreate(**valid(event_type=category))


@pytest.mark.parametrize("category", ["wedding", "birthday", "community", "anniversary"])
def test_enabled_categories_accepted(category):
    assert EventCreate(**valid(event_type=category)).event_type == category


def test_wedding_category_enabled():
    assert "wedding" in ENABLED_EVENT_TYPES


@pytest.mark.parametrize("tz", ["Mars/Phobos", "../etc/passwd", "IST", ""])
def test_invalid_timezone_rejected(tz):
    with pytest.raises(ValidationError):
        EventCreate(**valid(timezone=tz))


def test_currency_normalised_and_validated():
    assert EventCreate(**valid(currency="usd")).currency == "USD"
    with pytest.raises(ValidationError):
        EventCreate(**valid(currency="XXX"))


def test_owner_user_id_is_never_accepted():
    with pytest.raises(ValidationError, match="Extra inputs"):
        EventCreate(**valid(owner_user_id=str(uuid.uuid4())))


def test_blank_location_parts_become_none_and_country_validated():
    e = EventCreate(**valid(location={"name": "  ", "city": " Jaipur ", "country_code": "in"}))
    assert e.location.name is None and e.location.city == "Jaipur" and e.location.country_code == "IN"
    with pytest.raises(ValidationError):
        EventCreate(**valid(location={"country_code": "IND"}))


def test_title_trimmed_and_required():
    assert EventCreate(**valid(title="  Spaced  ")).title == "Spaced"
    with pytest.raises(ValidationError):
        EventCreate(**valid(title="   "))
    with pytest.raises(ValidationError):
        EventCreate(**valid(title="x" * 161))


def test_update_requires_a_field_and_forbids_null_for_required():
    with pytest.raises(ValidationError, match="at least one field"):
        EventUpdate()
    with pytest.raises(ValidationError, match="cannot be null"):
        EventUpdate(title=None)


def test_update_cannot_archive_or_change_owner_or_type():
    with pytest.raises(ValidationError, match="DELETE"):
        EventUpdate(status="archived")
    with pytest.raises(ValidationError, match="Extra inputs"):
        EventUpdate(owner_user_id=str(uuid.uuid4()))  # type: ignore[call-arg]
    with pytest.raises(ValidationError, match="Extra inputs"):
        EventUpdate(event_type="birthday")  # type: ignore[call-arg]
    with pytest.raises(ValidationError, match="Extra inputs"):
        EventUpdate(revision=99)  # type: ignore[call-arg]


def test_update_partial_location_tracks_provided_fields():
    u = EventUpdate(location={"city": "Udaipur"})
    assert u.location is not None and u.location.model_fields_set == {"city"}


def test_profile_update_rules():
    with pytest.raises(ValidationError, match="at least one field"):
        ProfileUpdate()
    with pytest.raises(ValidationError):
        ProfileUpdate(preferred_locale="xx-YY")
    with pytest.raises(ValidationError):
        ProfileUpdate(timezone="Nowhere/Land")
    assert ProfileUpdate(display_name="  Meera ").display_name == "Meera"
    with pytest.raises(ValidationError, match="Extra inputs"):
        ProfileUpdate(user_id=str(uuid.uuid4()))  # type: ignore[call-arg]


def test_status_lifecycle_is_documented_and_archived_is_terminal():
    assert STATUS_TRANSITIONS[EventStatus.DRAFT] == {EventStatus.PLANNING}
    assert EventStatus.COMPLETED in STATUS_TRANSITIONS[EventStatus.PLANNING]
    assert STATUS_TRANSITIONS[EventStatus.ARCHIVED] == frozenset()
    assert {s.value for s in EventStatus} == {"draft", "planning", "completed", "archived"}


def test_role_permissions_matrix():
    assert role_allows(MemberRole.OWNER, Permission.EVENT_ARCHIVE)
    assert role_allows(MemberRole.EDITOR, Permission.EVENT_UPDATE)
    assert not role_allows(MemberRole.EDITOR, Permission.EVENT_ARCHIVE)
    assert not role_allows(MemberRole.EDITOR, Permission.MEMBER_MANAGE)
    assert role_allows(MemberRole.VIEWER, Permission.EVENT_READ)
    assert not role_allows(MemberRole.VIEWER, Permission.EVENT_UPDATE)
    assert set(ROLE_PERMISSIONS) == set(MemberRole)


@pytest.mark.parametrize("header,expected", [('"4"', 4), ('W/"7"', 7), ("12", 12)])
def test_if_match_parsing(header, expected):
    assert parse_if_match(header) == expected
    assert etag(expected) == f'"{expected}"'


def test_if_match_missing_or_malformed():
    with pytest.raises(PreconditionRequiredError):
        parse_if_match(None)
    with pytest.raises(InvalidRequestError):
        parse_if_match("abc")
    with pytest.raises(InvalidRequestError):
        parse_if_match("*")


def test_cursor_roundtrip_and_tamper_detection():
    ts, eid = datetime(2027, 1, 1, tzinfo=UTC), uuid.uuid4()
    cur = encode_cursor(EventSort.START_ASC, ts, eid)
    assert decode_cursor(cur, EventSort.START_ASC) == (ts, eid)
    with pytest.raises(InvalidRequestError):
        decode_cursor(cur, EventSort.CREATED_DESC)
    with pytest.raises(InvalidRequestError):
        decode_cursor("%%%garbage", EventSort.START_ASC)

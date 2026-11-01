"""Event use cases: authorization, validation, persistence and audit in one transaction."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import psycopg.errors

from app.core.domain import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    STATUS_TRANSITIONS,
    EventSort,
    EventStatus,
    MemberRole,
    Permission,
)
from app.core.errors import (
    ForbiddenError,
    InvalidRequestError,
    InvalidStateTransitionError,
    NotFoundError,
    RevisionConflictError,
    ValidationFailedError,
)
from app.core.security import Principal
from app.database.pool import Connection, Database
from app.modules.audit import repository as audit
from app.modules.events import repository
from app.modules.events.permissions import require_permission
from app.modules.events.schemas import (
    DATE_RANGE_MESSAGE,
    EventCreate,
    EventOut,
    EventPage,
    EventUpdate,
    LocationOut,
)
from app.modules.identity import repository as identity_repository

logger = logging.getLogger(__name__)

_ARCHIVED_MESSAGE = "Archived events are read-only."


def _to_out(row: dict[str, Any]) -> EventOut:
    return EventOut(
        id=row["id"],
        event_type=row["event_type"],
        title=row["title"],
        start_at=row["start_at"],
        end_at=row["end_at"],
        timezone=row["timezone"],
        location=LocationOut(
            name=row["location_name"],
            city=row["city"],
            region=row["region"],
            country_code=row["country_code"],
        ),
        expected_guest_count=row["expected_guest_count"],
        currency=row["currency"].strip() if isinstance(row["currency"], str) else row["currency"],
        status=EventStatus(row["status"]),
        revision=row["revision"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        archived_at=row["archived_at"],
        my_role=MemberRole(row["my_role"]),
    )


def _db_values_from_create(payload: EventCreate) -> dict[str, Any]:
    return {
        "event_type": payload.event_type,
        "title": payload.title,
        "start_at": payload.start_at,
        "end_at": payload.end_at,
        "timezone": payload.timezone,
        "location_name": payload.location.name,
        "city": payload.location.city,
        "region": payload.location.region,
        "country_code": payload.location.country_code,
        "expected_guest_count": payload.expected_guest_count,
        "currency": payload.currency,
    }


class EventService:
    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------ create
    def create(self, principal: Principal, payload: EventCreate, request_id: str) -> EventOut:
        with self._db.transaction(principal.user_id, request_id) as conn:
            identity_repository.ensure_profile(conn, principal.user_id, principal.display_name_hint)
            # Single transaction: the deferred owner-membership trigger rejects the
            # commit if either statement is missing.
            event_id = repository.insert_event(conn, principal.user_id, _db_values_from_create(payload))
            repository.insert_owner_membership(conn, event_id, principal.user_id)
            audit.record(
                conn,
                event_id=event_id,
                actor_user_id=principal.user_id,
                action="event.created",
                entity_type="event",
                entity_id=event_id,
                request_id=request_id,
                metadata={"event_type": payload.event_type},
            )
            row = repository.get_event(conn, event_id)
        assert row is not None
        logger.info("event_created", extra={"event_id": str(event_id)})
        return _to_out(row)

    # -------------------------------------------------------------------- read
    def get(self, principal: Principal, event_id: uuid.UUID, request_id: str) -> EventOut:
        with self._db.transaction(principal.user_id, request_id) as conn:
            row = self._load_authorized(conn, event_id, Permission.EVENT_READ)
        return _to_out(row)

    def list(
        self,
        principal: Principal,
        *,
        statuses: list[EventStatus] | None,
        include_archived: bool,
        sort: EventSort,
        limit: int,
        cursor: str | None,
        request_id: str,
    ) -> EventPage:
        limit = max(1, min(limit or DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE))
        if statuses:
            chosen = {s.value for s in statuses}
        else:
            chosen = {s.value for s in EventStatus if s is not EventStatus.ARCHIVED}
            if include_archived:
                chosen.add(EventStatus.ARCHIVED.value)
        decoded = repository.decode_cursor(cursor, sort) if cursor else None

        with self._db.transaction(principal.user_id, request_id) as conn:
            rows = repository.list_events(
                conn, statuses=sorted(chosen), sort=sort, limit=limit, cursor=decoded
            )

        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            last = rows[-1]
            key = last["start_at"] if sort is EventSort.START_ASC else last["created_at"]
            next_cursor = repository.encode_cursor(sort, key, last["id"])
        return EventPage(data=[_to_out(r) for r in rows], next_cursor=next_cursor)

    # ------------------------------------------------------------------ update
    def update(
        self,
        principal: Principal,
        event_id: uuid.UUID,
        payload: EventUpdate,
        expected_revision: int,
        request_id: str,
    ) -> EventOut:
        with self._db.transaction(principal.user_id, request_id) as conn:
            current = self._load_authorized(conn, event_id, Permission.EVENT_UPDATE)
            if current["status"] == EventStatus.ARCHIVED.value:
                raise InvalidStateTransitionError(_ARCHIVED_MESSAGE)
            if current["revision"] != expected_revision:
                raise self._conflict(current["revision"])

            changes = self._compute_changes(current, payload)
            if not changes:
                return _to_out(current)  # nothing material changed: no new revision

            try:
                applied = repository.update_event(conn, event_id, expected_revision, changes)
            except psycopg.errors.InsufficientPrivilege as exc:
                raise ForbiddenError("You do not have permission to perform this action.") from exc
            except psycopg.errors.CheckViolation as exc:
                raise InvalidStateTransitionError(_ARCHIVED_MESSAGE) from exc

            if not applied:
                latest = repository.get_event(conn, event_id)
                if latest is None:
                    raise NotFoundError("The event was not found.")
                raise self._conflict(latest["revision"])

            audit.record(
                conn,
                event_id=event_id,
                actor_user_id=principal.user_id,
                action="event.updated",
                entity_type="event",
                entity_id=event_id,
                request_id=request_id,
                metadata={
                    "changed_fields": sorted(changes),
                    "from_revision": expected_revision,
                },
            )
            row = repository.get_event(conn, event_id)
        assert row is not None
        return _to_out(row)

    # ----------------------------------------------------------------- archive
    def archive(self, principal: Principal, event_id: uuid.UUID, request_id: str) -> None:
        with self._db.transaction(principal.user_id, request_id) as conn:
            current = self._load_authorized(conn, event_id, Permission.EVENT_ARCHIVE)
            if current["status"] == EventStatus.ARCHIVED.value:
                return  # idempotent
            try:
                archived = repository.archive_event(conn, event_id)
            except psycopg.errors.InsufficientPrivilege as exc:
                raise ForbiddenError("You do not have permission to perform this action.") from exc
            if archived:
                audit.record(
                    conn,
                    event_id=event_id,
                    actor_user_id=principal.user_id,
                    action="event.archived",
                    entity_type="event",
                    entity_id=event_id,
                    request_id=request_id,
                    metadata={"from_status": current["status"]},
                )

    # ---------------------------------------------------------------- internals
    @staticmethod
    def _load_authorized(conn: Connection, event_id: uuid.UUID, permission: Permission) -> dict[str, Any]:
        row = repository.get_event(conn, event_id)
        if row is None:
            # Not a member (or unknown id): never reveal whether the event exists.
            raise NotFoundError("The event was not found.")
        require_permission(MemberRole(row["my_role"]), permission)
        return row

    @staticmethod
    def _conflict(current_revision: int) -> RevisionConflictError:
        return RevisionConflictError(
            "The event was changed by someone else. Reload and try again.",
            details={"current_revision": current_revision},
        )

    @staticmethod
    def _compute_changes(current: dict[str, Any], payload: EventUpdate) -> dict[str, Any]:
        provided = payload.model_fields_set
        candidate: dict[str, Any] = {}

        for name in ("title", "start_at", "end_at", "timezone", "expected_guest_count"):
            if name in provided:
                candidate[name] = getattr(payload, name)
        if "currency" in provided:
            candidate["currency"] = payload.currency
        if "status" in provided and payload.status is not None:
            candidate["status"] = payload.status.value
        if "location" in provided and payload.location is not None:
            mapping = {
                "name": "location_name",
                "city": "city",
                "region": "region",
                "country_code": "country_code",
            }
            for field_name in payload.location.model_fields_set:
                candidate[mapping[field_name]] = getattr(payload.location, field_name)

        start = candidate.get("start_at", current["start_at"])
        end = candidate.get("end_at", current["end_at"])
        if end < start:
            raise ValidationFailedError(DATE_RANGE_MESSAGE)

        new_status = candidate.get("status")
        if new_status is not None and new_status != current["status"]:
            allowed = STATUS_TRANSITIONS[EventStatus(current["status"])]
            if EventStatus(new_status) not in allowed:
                raise InvalidStateTransitionError(
                    f"An event cannot move from {current['status']} to {new_status}.",
                    details={"from": current["status"], "to": new_status},
                )

        def same(name: str, value: Any) -> bool:
            existing = current[name]
            if isinstance(existing, str) and isinstance(value, str):
                return existing.strip() == value.strip()
            return bool(existing == value)

        changes = {k: v for k, v in candidate.items() if not same(k, v)}
        if not changes and not candidate:
            raise InvalidRequestError("Provide at least one field to update.")
        return changes

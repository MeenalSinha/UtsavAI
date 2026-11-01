"""Shared event context service and schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.domain import MemberRole, Permission, role_allows
from app.core.errors import NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.functions import repository as functions_repo
from app.modules.functions.schemas import FunctionOut
from app.modules.preferences import repository as preferences_repo


class ContextLocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    city: str | None = None
    region: str | None = None
    country_code: str | None = None


class ContextEventSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_type: str
    title: str
    start_at: datetime
    end_at: datetime
    timezone: str
    location: ContextLocation
    expected_guest_count: int
    currency: str
    revision: int
    status: str


class ContextPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style_tags: list[str] = []
    cultural_context: dict[str, Any] = {}
    priorities: dict[str, Any] = {}
    accessibility_notes: dict[str, Any] = {}
    schema_version: int = 1


class ContextPermissions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str
    can_edit: bool
    can_generate_plan: bool
    can_archive: bool


class SharedEventContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: ContextEventSummary
    preferences: ContextPreferences
    functions: list[FunctionOut]
    permissions: ContextPermissions


def build_event_context(db: Database, principal: Principal, event_id: uuid.UUID) -> SharedEventContext:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(event["my_role"], Permission.EVENT_READ)

        role = MemberRole(event["my_role"])
        can_edit = role_allows(role, Permission.EVENT_UPDATE) and event["status"] != "archived"
        can_generate_plan = role_allows(role, Permission.PLAN_GENERATE) and event["status"] != "archived"
        can_archive = role_allows(role, Permission.EVENT_ARCHIVE) and event["status"] != "archived"

        pref_row = preferences_repo.get_preferences(conn, event_id)
        func_rows = functions_repo.list_functions(conn, event_id)

        preferences = (
            ContextPreferences(
                style_tags=pref_row["style_tags"] or [],
                cultural_context=pref_row["cultural_context"] or {},
                priorities=pref_row["priorities"] or {},
                accessibility_notes=pref_row["accessibility_notes"] or {},
                schema_version=pref_row["schema_version"],
            )
            if pref_row
            else ContextPreferences()
        )

        functions = [FunctionOut(**r) for r in func_rows]

        event_summary = ContextEventSummary(
            id=event["id"],
            event_type=event["event_type"],
            title=event["title"],
            start_at=event["start_at"],
            end_at=event["end_at"],
            timezone=event["timezone"],
            location=ContextLocation(
                name=event["location_name"],
                city=event["city"],
                region=event["region"],
                country_code=event["country_code"],
            ),
            expected_guest_count=event["expected_guest_count"],
            currency=event["currency"],
            revision=event["revision"],
            status=event["status"],
        )

        permissions = ContextPermissions(
            role=role.value,
            can_edit=can_edit,
            can_generate_plan=can_generate_plan,
            can_archive=can_archive,
        )

        return SharedEventContext(
            event=event_summary,
            preferences=preferences,
            functions=functions,
            permissions=permissions,
        )

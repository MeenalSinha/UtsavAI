"""Shared event context service and schema."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.domain import ExpenseStatus, MemberRole, Permission, TaskStatus, role_allows
from app.core.errors import NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.budget import repository as budget_repo
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.functions import repository as functions_repo
from app.modules.functions.schemas import FunctionOut
from app.modules.gifts.schemas import ContextGiftSummary
from app.modules.preferences import repository as preferences_repo
from app.modules.tasks import repository as tasks_repo
from app.modules.vendors import repository as vendors_repo


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


class ContextBudgetSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_limit: Decimal
    total_allocated: Decimal
    unallocated_amount: Decimal
    planned_expenses: Decimal
    committed_expenses: Decimal
    paid_expenses: Decimal
    projected_total: Decimal
    remaining_after_committed: Decimal
    projected_headroom: Decimal


class ContextTimelineSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    overdue_tasks: int
    completion_percentage: float


class ContextVendorCategorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    vendor_count: int
    quoted_count: int
    shortlisted_count: int
    booked_count: int


class ContextVendorSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_vendors: int
    categories: list[ContextVendorCategorySummary]
    quote_count: int
    pending_decisions: int


class SharedEventContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: ContextEventSummary
    preferences: ContextPreferences
    functions: list[FunctionOut]
    permissions: ContextPermissions
    budget: ContextBudgetSummary | None = None
    timeline: ContextTimelineSummary | None = None
    vendor_summary: ContextVendorSummary | None = None
    gift_summary: ContextGiftSummary | None = None


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

        # Build Budget context summary
        budget_row = budget_repo.get_budget(conn, event_id)
        context_budget: ContextBudgetSummary | None = None
        if budget_row:
            total_limit = Decimal(str(budget_row["total_limit"]))
            categories = budget_repo.list_categories(conn, budget_row["id"])
            expenses = budget_repo.list_expenses(conn, event_id)

            zero = Decimal("0")
            total_allocated = sum((Decimal(str(c["planned_amount"])) for c in categories), start=zero)
            planned_exp = sum(
                (Decimal(str(e["amount"])) for e in expenses if e["status"] == ExpenseStatus.PLANNED.value),
                start=zero,
            )
            committed_exp = sum(
                (Decimal(str(e["amount"])) for e in expenses if e["status"] == ExpenseStatus.COMMITTED.value),
                start=zero,
            )
            paid_exp = sum(
                (Decimal(str(e["amount"])) for e in expenses if e["status"] == ExpenseStatus.PAID.value),
                start=zero,
            )

            context_budget = ContextBudgetSummary(
                total_limit=total_limit,
                total_allocated=total_allocated,
                unallocated_amount=total_limit - total_allocated,
                planned_expenses=planned_exp,
                committed_expenses=committed_exp,
                paid_expenses=paid_exp,
                projected_total=planned_exp + committed_exp + paid_exp,
                remaining_after_committed=total_limit - (committed_exp + paid_exp),
                projected_headroom=total_limit - (planned_exp + committed_exp + paid_exp),
            )

        # Build Timeline context summary
        tasks = tasks_repo.list_tasks(conn, event_id)
        context_timeline: ContextTimelineSummary | None = None
        if tasks:
            from datetime import UTC, datetime

            now = datetime.now(UTC)
            total_t = len(tasks)
            completed_t = sum(1 for t in tasks if t["status"] == TaskStatus.DONE.value)
            pending_t = sum(1 for t in tasks if t["status"] == TaskStatus.TODO.value)
            in_prog_t = sum(1 for t in tasks if t["status"] == TaskStatus.IN_PROGRESS.value)
            blocked_t = sum(1 for t in tasks if t["status"] == TaskStatus.BLOCKED.value)
            cancelled_t = sum(1 for t in tasks if t["status"] == TaskStatus.CANCELLED.value)
            overdue_t = sum(
                1
                for t in tasks
                if t["due_at"] is not None
                and t["due_at"] < now
                and t["status"] not in (TaskStatus.DONE.value, TaskStatus.CANCELLED.value)
            )
            active_t = total_t - cancelled_t
            pct = round((completed_t / active_t) * 100, 1) if active_t > 0 else 0.0

            context_timeline = ContextTimelineSummary(
                total_tasks=total_t,
                completed_tasks=completed_t,
                pending_tasks=pending_t,
                in_progress_tasks=in_prog_t,
                blocked_tasks=blocked_t,
                overdue_tasks=overdue_t,
                completion_percentage=pct,
            )

        # Build Vendor context summary
        vendor_metrics = vendors_repo.get_vendor_metrics(conn, event_id)
        context_vendor: ContextVendorSummary | None = None
        if vendor_metrics["total_vendors"] > 0:
            context_vendor = ContextVendorSummary(
                total_vendors=vendor_metrics["total_vendors"],
                quote_count=vendor_metrics["quote_count"],
                pending_decisions=vendor_metrics["pending_decisions"],
                categories=[
                    ContextVendorCategorySummary(
                        category=c["category"],
                        vendor_count=c["vendor_count"],
                        quoted_count=c["quoted_count"],
                        shortlisted_count=c["shortlisted_count"],
                        booked_count=c["booked_count"],
                    )
                    for c in vendor_metrics["categories"]
                ],
            )

        # Build GiftCircle summary
        from app.modules.gifts import service as gifts_service

        context_gift = gifts_service.get_event_gift_summary(conn, event_id)

        return SharedEventContext(
            event=event_summary,
            preferences=preferences,
            functions=functions,
            permissions=permissions,
            budget=context_budget,
            timeline=context_timeline,
            vendor_summary=context_vendor,
            gift_summary=context_gift if context_gift.registry_exists else None,
        )

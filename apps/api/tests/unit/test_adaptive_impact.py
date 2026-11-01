"""Unit tests for Phase 6 Adaptive Planning deterministic impact calculations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.adaptive.impact_engine import calculate_impact
from app.modules.adaptive.schemas import (
    BudgetChangeItem,
    EventChangeItem,
    FunctionChangeItem,
    TypedChangeRequest,
)
from app.modules.events.context import (
    ContextBudgetSummary,
    ContextEventSummary,
    ContextLocation,
    ContextPermissions,
    ContextPreferences,
    ContextTimelineSummary,
    SharedEventContext,
)
from app.modules.functions.schemas import FunctionOut


def _make_context(
    guest_count: int = 200,
    total_limit: Decimal = Decimal("2000000.00"),
    committed: Decimal = Decimal("800000.00"),
    paid: Decimal = Decimal("300000.00"),
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> SharedEventContext:
    if start_at is None:
        start_at = datetime(2027, 2, 10, 10, 0, tzinfo=UTC)
    if end_at is None:
        end_at = datetime(2027, 2, 12, 10, 0, tzinfo=UTC)

    event_id = uuid.uuid4()
    return SharedEventContext(
        event=ContextEventSummary(
            id=event_id,
            event_type="wedding",
            title="Aarav & Meera Wedding",
            start_at=start_at,
            end_at=end_at,
            timezone="Asia/Kolkata",
            location=ContextLocation(name="Jaipur Palace", city="Jaipur", country_code="IN"),
            expected_guest_count=guest_count,
            currency="INR",
            revision=3,
            status="planning",
        ),
        preferences=ContextPreferences(),
        functions=[
            FunctionOut(
                id=uuid.uuid4(),
                event_id=event_id,
                name="Sangeet Night",
                starts_at=start_at,
                ends_at=end_at,
                location_name="Grand Ballroom",
                sort_order=0,
                created_at=start_at,
                updated_at=start_at,
            )
        ],
        permissions=ContextPermissions(
            role="owner",
            can_edit=True,
            can_generate_plan=True,
            can_archive=True,
        ),
        budget=ContextBudgetSummary(
            total_limit=total_limit,
            total_allocated=Decimal("1500000.00"),
            unallocated_amount=Decimal("500000.00"),
            planned_expenses=Decimal("400000.00"),
            committed_expenses=committed,
            paid_expenses=paid,
            projected_total=committed + paid + Decimal("400000.00"),
            remaining_after_committed=total_limit - (committed + paid),
            projected_headroom=total_limit - (committed + paid + Decimal("400000.00")),
        ),
        timeline=ContextTimelineSummary(
            total_tasks=5,
            completed_tasks=1,
            pending_tasks=4,
            in_progress_tasks=0,
            blocked_tasks=0,
            overdue_tasks=0,
            completion_percentage=20.0,
        ),
    )


def test_guest_count_increase_impact():
    ctx = _make_context(guest_count=200)
    req = TypedChangeRequest(
        schema_version=1,
        base_revision=3,
        request_text="Increase guest count to 350",
        event_changes=EventChangeItem(expected_guest_count=350),
    )

    impact = calculate_impact(ctx, req, [], [], None)
    assert impact.severity == "high"
    assert "event" in impact.affected_modules
    assert "budget" in impact.affected_modules

    guest_calc = next(c for c in impact.calculations if c.metric == "Guest Count")
    assert guest_calc.before_value == "200"
    assert guest_calc.after_value == "350"
    assert guest_calc.delta == "+150"

    warning = next(w for w in impact.warnings if w.code == "WARN_EVENT_GUEST_CAPACITY_SHIFT")
    assert warning.severity == "high"

    # Verifies suggested option to flag budget categories
    assert any(opt.id == "opt_flag_budget_for_review" for opt in impact.suggested_options)


def test_budget_below_committed_is_critical():
    # Committed + paid is 800k + 300k = 1,100,000 INR
    ctx = _make_context(committed=Decimal("800000.00"), paid=Decimal("300000.00"))
    req = TypedChangeRequest(
        schema_version=1,
        base_revision=3,
        request_text="Reduce budget to 1,000,000",
        budget_changes=BudgetChangeItem(total_limit=Decimal("1000000.00")),
    )

    impact = calculate_impact(ctx, req, [], [], None)
    assert impact.severity == "critical"
    crit_warning = next(w for w in impact.warnings if w.code == "ERR_BUDGET_BELOW_COMMITTED")
    assert crit_warning.severity == "critical"
    assert "1,100,000.00" in crit_warning.message


def test_event_date_shift_reschedules_tasks():
    ctx = _make_context()
    shifted_start = datetime(2027, 2, 15, 10, 0, tzinfo=UTC)
    shifted_end = datetime(2027, 2, 17, 10, 0, tzinfo=UTC)

    req = TypedChangeRequest(
        schema_version=1,
        base_revision=3,
        request_text="Postpone wedding by 5 days",
        event_changes=EventChangeItem(start_at=shifted_start, end_at=shifted_end),
    )

    tasks = [
        {
            "id": uuid.uuid4(),
            "title": "Send Invitation Cards",
            "due_at": datetime(2027, 2, 1, 10, 0, tzinfo=UTC),
            "status": "todo",
        }
    ]

    impact = calculate_impact(ctx, req, tasks, [], None)
    assert "event" in impact.affected_modules
    assert "timeline" in impact.affected_modules
    assert any(opt.id == "opt_reschedule_tasks" for opt in impact.suggested_options)


def test_vendor_quote_expiry_and_guest_scaling():
    ctx = _make_context(guest_count=200)
    shifted_start = datetime(2027, 2, 15, 10, 0, tzinfo=UTC)

    req = TypedChangeRequest(
        schema_version=1,
        base_revision=3,
        request_text="Postpone wedding by 5 days and add 50 guests",
        event_changes=EventChangeItem(expected_guest_count=250, start_at=shifted_start),
    )

    quotes = [
        {
            "quote_id": uuid.uuid4(),
            "vendor_name": "Royal Caterers",
            "category": "Catering",
            "quote_status": "accepted",
            "valid_until": datetime(2027, 2, 12, tzinfo=UTC).date(),
        }
    ]

    impact = calculate_impact(ctx, req, [], quotes, None)
    assert "vendors" in impact.affected_modules
    assert any(w.code == "WARN_VENDOR_QUOTE_EXPIRED" for w in impact.warnings)
    assert any(w.code == "WARN_VENDOR_GUEST_CAPACITY" for w in impact.warnings)
    assert any(opt.id == "opt_mark_vendor_quotes_review" for opt in impact.suggested_options)


def test_gift_registry_early_expiry_extension():
    ctx = _make_context()
    shifted_end = datetime(2027, 2, 20, 10, 0, tzinfo=UTC)

    req = TypedChangeRequest(
        schema_version=1,
        base_revision=3,
        request_text="Extend wedding",
        event_changes=EventChangeItem(end_at=shifted_end),
    )

    reg_id = uuid.uuid4()
    registry_row = {
        "id": reg_id,
        "title": "Aarav & Meera Registry",
        "expires_at": datetime(2027, 2, 15, 10, 0, tzinfo=UTC),
    }

    impact = calculate_impact(ctx, req, [], [], registry_row)
    assert "giftcircle" in impact.affected_modules
    assert any(w.code == "WARN_GIFT_REGISTRY_EARLY_EXPIRY" for w in impact.warnings)
    assert any(opt.id == "opt_extend_gift_registry" for opt in impact.suggested_options)


def test_impact_engine_determinism():
    ctx = _make_context()
    req = TypedChangeRequest(
        schema_version=1,
        base_revision=3,
        request_text="Deterministic verification change",
        event_changes=EventChangeItem(expected_guest_count=280),
        budget_changes=BudgetChangeItem(total_limit=Decimal("2500000.00")),
        function_changes=[FunctionChangeItem(action="add", name="Haldi Celebration")],
    )

    impact_1 = calculate_impact(ctx, req, [], [], None)
    impact_2 = calculate_impact(ctx, req, [], [], None)

    assert impact_1.model_dump(mode="json") == impact_2.model_dump(mode="json")

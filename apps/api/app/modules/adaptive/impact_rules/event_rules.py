"""Deterministic rules for Event and Function changes."""

from __future__ import annotations

from app.modules.adaptive.schemas import (
    AffectedRecord,
    CalculationItem,
    TypedChangeRequest,
    WarningItem,
)
from app.modules.events.context import SharedEventContext


def evaluate_event_rules(
    context: SharedEventContext,
    request: TypedChangeRequest,
) -> tuple[list[AffectedRecord], list[CalculationItem], list[WarningItem]]:
    records: list[AffectedRecord] = []
    calcs: list[CalculationItem] = []
    warnings: list[WarningItem] = []

    # Guest count changes
    if request.event_changes and request.event_changes.expected_guest_count is not None:
        old_count = context.event.expected_guest_count
        new_count = request.event_changes.expected_guest_count
        delta = new_count - old_count

        calcs.append(
            CalculationItem(
                metric="Guest Count",
                before_value=str(old_count),
                after_value=str(new_count),
                delta=f"{'+' if delta >= 0 else ''}{delta}",
                unit="guests",
            )
        )

        if delta != 0:
            records.append(
                AffectedRecord(
                    module="event",
                    entity_type="event",
                    entity_id=str(context.event.id),
                    entity_name=context.event.title,
                    change_nature="guest_count_updated",
                    details=f"Expected guest count altered from {old_count} to {new_count}",
                )
            )

        pct_change = (abs(delta) / old_count * 100) if old_count > 0 else 100.0
        if pct_change >= 25.0:
            warnings.append(
                WarningItem(
                    code="WARN_EVENT_GUEST_CAPACITY_SHIFT",
                    message=(
                        f"Guest count change of {pct_change:.1f}% ({delta:+d} guests) significantly alters "
                        "catering, seating, and venue capacity requirements."
                    ),
                    severity="high" if pct_change >= 50.0 else "medium",
                    recommended_action=("Review vendor quotes and catering allocations to ensure scaling."),
                )
            )

    # Date / Time changes
    if request.event_changes and (request.event_changes.start_at or request.event_changes.end_at):
        new_start = request.event_changes.start_at or context.event.start_at
        new_end = request.event_changes.end_at or context.event.end_at

        if new_end < new_start:
            warnings.append(
                WarningItem(
                    code="ERR_EVENT_INVALID_DATE_RANGE",
                    message="Event end time cannot be earlier than start time.",
                    severity="critical",
                    recommended_action="Correct event start and end timestamps so that end follows start.",
                )
            )

        start_delta = (new_start - context.event.start_at).total_seconds() / 86400.0
        if abs(start_delta) > 0.01:
            calcs.append(
                CalculationItem(
                    metric="Event Schedule Shift",
                    before_value=context.event.start_at.strftime("%Y-%m-%d %H:%M"),
                    after_value=new_start.strftime("%Y-%m-%d %H:%M"),
                    delta=f"{'+' if start_delta >= 0 else ''}{start_delta:.1f}",
                    unit="days",
                )
            )
            records.append(
                AffectedRecord(
                    module="event",
                    entity_type="event",
                    entity_id=str(context.event.id),
                    entity_name=context.event.title,
                    change_nature="dates_shifted",
                    details=f"Event dates shifted by {start_delta:+.1f} days",
                )
            )
            warnings.append(
                WarningItem(
                    code="WARN_EVENT_DATE_SHIFT",
                    message=(
                        f"Event dates moved by {start_delta:+.1f} days. Downstream task deadlines, "
                        "vendor quotes, and registry expiration must be reconciled."
                    ),
                    severity="high" if abs(start_delta) > 7 else "medium",
                    recommended_action=(
                        "Reschedule timeline tasks and notify vendors regarding revised event dates."
                    ),
                )
            )

    # Location changes
    if request.event_changes and (
        request.event_changes.location_name
        or request.event_changes.city
        or request.event_changes.region
        or request.event_changes.country_code
    ):
        loc_parts: list[str] = []
        if request.event_changes.location_name:
            loc_parts.append(request.event_changes.location_name)
        if request.event_changes.city:
            loc_parts.append(request.event_changes.city)
        new_loc_desc = ", ".join(loc_parts) or "Updated Location"

        records.append(
            AffectedRecord(
                module="event",
                entity_type="event",
                entity_id=str(context.event.id),
                entity_name=context.event.title,
                change_nature="location_changed",
                details=f"Event location changed to {new_loc_desc}",
            )
        )
        warnings.append(
            WarningItem(
                code="WARN_EVENT_LOCATION_CHANGED",
                message=(
                    f"Event location modified to '{new_loc_desc}'. Local vendor travel, delivery, and venue "
                    "contracts may be affected."
                ),
                severity="medium",
                recommended_action="Verify venue confirmation and notify vendors about the location update.",
            )
        )

    # Function changes
    if request.function_changes:
        for f_chg in request.function_changes:
            if f_chg.action == "add":
                records.append(
                    AffectedRecord(
                        module="plan_ai",
                        entity_type="event_function",
                        entity_name=f_chg.name or "New Function",
                        change_nature="function_added",
                        details=f"New celebration function '{f_chg.name}' proposed",
                    )
                )
            elif f_chg.action == "archive":
                target_func = next((f for f in context.functions if f.id == f_chg.function_id), None)
                fname = target_func.name if target_func else (f_chg.name or "Function")
                records.append(
                    AffectedRecord(
                        module="plan_ai",
                        entity_type="event_function",
                        entity_id=str(f_chg.function_id) if f_chg.function_id else None,
                        entity_name=fname,
                        change_nature="function_archived",
                        details=f"Function '{fname}' scheduled for archival",
                    )
                )
                warnings.append(
                    WarningItem(
                        code="WARN_FUNCTION_ARCHIVED",
                        message=(f"Archiving '{fname}' will orphan timeline tasks dedicated to it."),
                        severity="medium",
                        recommended_action=(
                            f"Review tasks associated with '{fname}' before completing proposal acceptance."
                        ),
                    )
                )
            elif f_chg.action == "update":
                target_func = next((f for f in context.functions if f.id == f_chg.function_id), None)
                fname = target_func.name if target_func else (f_chg.name or "Function")
                records.append(
                    AffectedRecord(
                        module="plan_ai",
                        entity_type="event_function",
                        entity_id=str(f_chg.function_id) if f_chg.function_id else None,
                        entity_name=fname,
                        change_nature="function_updated",
                        details=f"Function '{fname}' details updated",
                    )
                )

    return records, calcs, warnings

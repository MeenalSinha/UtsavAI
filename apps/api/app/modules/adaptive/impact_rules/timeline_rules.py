"""Deterministic rules for TimelineAI task alignment and scheduling."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from app.modules.adaptive.schemas import (
    AffectedRecord,
    CalculationItem,
    ProposedOperation,
    SuggestedOption,
    TypedChangeRequest,
    WarningItem,
)
from app.modules.events.context import SharedEventContext


def evaluate_timeline_rules(
    context: SharedEventContext,
    request: TypedChangeRequest,
    task_rows: list[dict[str, Any]],
) -> tuple[list[AffectedRecord], list[CalculationItem], list[WarningItem], list[SuggestedOption]]:
    records: list[AffectedRecord] = []
    calcs: list[CalculationItem] = []
    warnings: list[WarningItem] = []
    options: list[SuggestedOption] = []

    if not task_rows:
        return records, calcs, warnings, options

    # 1. Date shift evaluation
    if request.event_changes and (request.event_changes.start_at or request.event_changes.end_at):
        new_start = request.event_changes.start_at or context.event.start_at
        new_end = request.event_changes.end_at or context.event.end_at
        date_shift = new_start - context.event.start_at
        shift_days = date_shift.total_seconds() / 86400.0

        misaligned_tasks: list[dict[str, Any]] = []
        for task in task_rows:
            due_at = task.get("due_at")
            if due_at and (due_at > new_end or due_at < new_start - timedelta(days=365)):
                misaligned_tasks.append(task)

        if misaligned_tasks:
            warnings.append(
                WarningItem(
                    code="WARN_TIMELINE_TASK_DEADLINE_OUT_OF_BOUNDS",
                    message=(
                        f"{len(misaligned_tasks)} task deadline(s) fall outside the revised event window."
                    ),
                    severity="high",
                    recommended_action="Reschedule deadlines to align with the revised event timeframe.",
                )
            )

        if abs(shift_days) > 0.01:
            tasks_with_due_dates = [t for t in task_rows if t.get("due_at") is not None]
            calcs.append(
                CalculationItem(
                    metric="Timeline Tasks To Shift",
                    before_value=str(len(tasks_with_due_dates)),
                    after_value=str(len(tasks_with_due_dates)),
                    delta=f"{'+' if shift_days >= 0 else ''}{shift_days:.1f}d shift",
                    unit="tasks",
                )
            )

            for t in tasks_with_due_dates[:10]:  # Highlight top 10 in affected records
                d_str = t["due_at"].strftime("%Y-%m-%d")
                records.append(
                    AffectedRecord(
                        module="timeline",
                        entity_type="task",
                        entity_id=str(t["id"]),
                        entity_name=t["title"],
                        change_nature="due_date_shift_suggested",
                        details=f"Current due date {d_str} should shift by {shift_days:+.1f} days",
                    )
                )

            options.append(
                SuggestedOption(
                    id="opt_reschedule_tasks",
                    title="Reschedule Active Task Deadlines",
                    description=(
                        f"Automatically shift all {len(tasks_with_due_dates)} task deadlines by "
                        f"{shift_days:+.1f} days to match the revised event dates."
                    ),
                    operations=[
                        ProposedOperation(
                            op_code="op_shift_task_due_dates",
                            target_module="timeline",
                            description=(
                                f"Shift {len(tasks_with_due_dates)} task deadlines by {shift_days:+.1f} days"
                            ),
                            payload={"shift_seconds": int(date_shift.total_seconds())},
                        )
                    ],
                    selected_by_default=True,
                )
            )

    # 2. Function archive evaluation
    if request.function_changes:
        archived_ids = {
            f.function_id for f in request.function_changes if f.action == "archive" and f.function_id
        }
        if archived_ids:
            orphaned = [t for t in task_rows if t.get("function_id") in archived_ids]
            if orphaned:
                for t in orphaned:
                    records.append(
                        AffectedRecord(
                            module="timeline",
                            entity_type="task",
                            entity_id=str(t["id"]),
                            entity_name=t["title"],
                            change_nature="function_archived_dependency",
                            details="Task is associated with a celebration function marked for archival",
                        )
                    )
                warnings.append(
                    WarningItem(
                        code="WARN_TIMELINE_ORPHANED_TASKS",
                        message=(
                            f"{len(orphaned)} task(s) are linked to celebration functions scheduled for "
                            "archival."
                        ),
                        severity="medium",
                        recommended_action="Unlink or reassign tasks associated with the archived functions.",
                    )
                )

    return records, calcs, warnings, options

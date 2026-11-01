"""Deterministic rules for BudgetAI and financial headroom."""

from __future__ import annotations

from decimal import Decimal

from app.modules.adaptive.schemas import (
    AffectedRecord,
    CalculationItem,
    ProposedOperation,
    SuggestedOption,
    TypedChangeRequest,
    WarningItem,
)
from app.modules.events.context import SharedEventContext


def evaluate_budget_rules(
    context: SharedEventContext,
    request: TypedChangeRequest,
) -> tuple[list[AffectedRecord], list[CalculationItem], list[WarningItem], list[SuggestedOption]]:
    records: list[AffectedRecord] = []
    calcs: list[CalculationItem] = []
    warnings: list[WarningItem] = []
    options: list[SuggestedOption] = []

    budget = context.budget
    if not budget:
        # No budget active on this event
        return records, calcs, warnings, options

    currency = context.event.currency
    curr_limit = budget.total_limit
    committed_paid = budget.committed_expenses + budget.paid_expenses
    curr_projected = budget.projected_total

    new_limit: Decimal | None = None
    if request.budget_changes and request.budget_changes.total_limit is not None:
        new_limit = request.budget_changes.total_limit
        limit_delta = new_limit - curr_limit

        calcs.append(
            CalculationItem(
                metric="Budget Total Limit",
                before_value=f"{currency} {curr_limit:,.2f}",
                after_value=f"{currency} {new_limit:,.2f}",
                delta=f"{'+' if limit_delta >= Decimal('0.00') else ''}{currency} {limit_delta:,.2f}",
                unit=currency,
            )
        )

        records.append(
            AffectedRecord(
                module="budget",
                entity_type="budget",
                entity_name="Overall Budget Limit",
                change_nature="limit_adjusted",
                details=(
                    f"Budget ceiling changed from {currency} {curr_limit:,.2f} to {currency} {new_limit:,.2f}"
                ),
            )
        )

        # Check committed expenses vs new limit
        if new_limit < committed_paid:
            deficit = committed_paid - new_limit
            warnings.append(
                WarningItem(
                    code="ERR_BUDGET_BELOW_COMMITTED",
                    message=(
                        f"Proposed budget limit ({currency} {new_limit:,.2f}) is strictly less than already "
                        f"committed & paid expenses ({currency} {committed_paid:,.2f}). "
                        f"Deficit of {currency} {deficit:,.2f}."
                    ),
                    severity="critical",
                    recommended_action=(
                        f"Increase the budget limit to at least {currency} {committed_paid:,.2f} "
                        "or cancel committed vendor contracts."
                    ),
                )
            )
        elif new_limit < curr_projected:
            shortfall = curr_projected - new_limit
            warnings.append(
                WarningItem(
                    code="WARN_BUDGET_BELOW_PROJECTED",
                    message=(
                        f"Proposed budget limit ({currency} {new_limit:,.2f}) is below projected total "
                        f"expenses ({currency} {curr_projected:,.2f}) by {currency} {shortfall:,.2f}."
                    ),
                    severity="high",
                    recommended_action="Review planned expenses and allocations to prevent budget overruns.",
                )
            )

        new_headroom = new_limit - curr_projected
        headroom_delta = new_headroom - budget.projected_headroom
        sign = "+" if headroom_delta >= Decimal("0.00") else ""
        calcs.append(
            CalculationItem(
                metric="Projected Headroom",
                before_value=f"{currency} {budget.projected_headroom:,.2f}",
                after_value=f"{currency} {new_headroom:,.2f}",
                delta=f"{sign}{currency} {headroom_delta:,.2f}",
                unit=currency,
            )
        )

    # Guest count impact on budget
    if request.event_changes and request.event_changes.expected_guest_count is not None:
        old_count = context.event.expected_guest_count
        new_count = request.event_changes.expected_guest_count
        if new_count > old_count and old_count > 0:
            # Estimate per-guest budget pressure if limit was not raised
            if new_limit is None or new_limit <= curr_limit:
                curr_per_guest = curr_limit / Decimal(old_count)
                new_per_guest = curr_limit / Decimal(new_count)
                warnings.append(
                    WarningItem(
                        code="WARN_BUDGET_GUEST_PRESSURE",
                        message=(
                            f"Guest count increased from {old_count} to {new_count} "
                            f"(+{new_count - old_count}) without a proportional budget increase. "
                            f"Per-guest allocation drops from {currency} {curr_per_guest:,.2f} "
                            f"to {currency} {new_per_guest:,.2f}."
                        ),
                        severity="medium",
                        recommended_action=(
                            "Consider raising the budget ceiling or reallocating from non-guest categories."
                        ),
                    )
                )
                records.append(
                    AffectedRecord(
                        module="budget",
                        entity_type="budget",
                        entity_name="Per-Guest Budget Ratio",
                        change_nature="guest_pressure",
                        details=(
                            f"Per-guest allocation decreases from {currency} {curr_per_guest:,.2f} "
                            f"to {currency} {new_per_guest:,.2f}."
                        ),
                    )
                )

            options.append(
                SuggestedOption(
                    id="opt_flag_budget_for_review",
                    title="Flag Budget Categories for Guest Scale Review",
                    description=(
                        "Record an audit checkpoint and flag guest-sensitive categories (Catering, Venue) "
                        "to review per-guest estimates."
                    ),
                    operations=[
                        ProposedOperation(
                            op_code="op_flag_budget_for_review",
                            target_module="budget",
                            description=(
                                f"Flag guest categories for re-estimation due to {new_count - old_count} "
                                "guest expansion"
                            ),
                            payload={"reason": f"Guest expansion from {old_count} to {new_count}"},
                        )
                    ],
                    selected_by_default=True,
                )
            )

    return records, calcs, warnings, options

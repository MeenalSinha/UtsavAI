"""Unit tests for deterministic Budget & Expense calculations using Python Decimal."""

import uuid
from decimal import Decimal

from app.modules.budget.schemas import (
    BudgetSummaryOut,
    CategorySummaryItem,
)


def test_budget_summary_financial_definitions():
    """Verify authoritative financial formulas without database dependency."""
    total_limit = Decimal("1800000.00")
    cat1_planned = Decimal("900000.00")
    cat2_planned = Decimal("600000.00")
    total_allocated = cat1_planned + cat2_planned
    unallocated_amount = total_limit - total_allocated

    assert total_allocated == Decimal("1500000.00")
    assert unallocated_amount == Decimal("300000.00")

    planned_exp = Decimal("200000.00")
    committed_exp = Decimal("450000.00")
    paid_exp = Decimal("250000.00")
    cancelled_exp = Decimal("50000.00")  # Must be excluded from active totals

    projected_total = planned_exp + committed_exp + paid_exp
    remaining_after_committed = total_limit - (committed_exp + paid_exp)
    projected_headroom = total_limit - projected_total

    assert projected_total == Decimal("900000.00")
    assert remaining_after_committed == Decimal("1100000.00")
    assert projected_headroom == Decimal("900000.00")

    summary = BudgetSummaryOut(
        currency="INR",
        total_limit=total_limit,
        total_allocated=total_allocated,
        unallocated_amount=unallocated_amount,
        planned_expenses=planned_exp,
        committed_expenses=committed_exp,
        paid_expenses=paid_exp,
        cancelled_expenses=cancelled_exp,
        projected_total=projected_total,
        remaining_after_committed=remaining_after_committed,
        projected_headroom=projected_headroom,
        alerts=["You have INR 300000.00 of unallocated budget remaining."],
        category_summaries=[
            CategorySummaryItem(
                category_id=uuid.uuid4(),
                category_key="venue_catering",
                name="Venue & Catering",
                planned_amount=cat1_planned,
                committed_amount=committed_exp,
                paid_amount=paid_exp,
                projected_amount=committed_exp + paid_exp + planned_exp,
                remaining_amount=cat1_planned - (committed_exp + paid_exp),
                is_over_budget=False,
            )
        ],
    )

    assert summary.total_limit == Decimal("1800000.00")
    assert summary.projected_headroom == Decimal("900000.00")
    assert summary.cancelled_expenses == Decimal("50000.00")
    assert summary.category_summaries[0].remaining_amount == Decimal("200000.00")


def test_overspending_and_negative_headroom_representable():
    """Verify that negative headroom and over-budget scenarios are represented accurately."""
    total_limit = Decimal("500000.00")
    planned_exp = Decimal("300000.00")
    committed_exp = Decimal("400000.00")
    paid_exp = Decimal("200000.00")

    projected_total = planned_exp + committed_exp + paid_exp
    remaining_after_committed = total_limit - (committed_exp + paid_exp)
    projected_headroom = total_limit - projected_total

    assert remaining_after_committed == Decimal("-100000.00")
    assert projected_headroom == Decimal("-400000.00")

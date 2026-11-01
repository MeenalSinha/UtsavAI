"""Deterministic Impact Analysis Engine orchestrating cross-module evaluation."""

from __future__ import annotations

from typing import Any, Literal

from app.modules.adaptive.impact_rules.budget_rules import evaluate_budget_rules
from app.modules.adaptive.impact_rules.event_rules import evaluate_event_rules
from app.modules.adaptive.impact_rules.gift_rules import evaluate_gift_rules
from app.modules.adaptive.impact_rules.timeline_rules import evaluate_timeline_rules
from app.modules.adaptive.impact_rules.vendor_rules import evaluate_vendor_rules
from app.modules.adaptive.schemas import (
    AffectedRecord,
    CalculationItem,
    ImpactResult,
    SuggestedOption,
    TypedChangeRequest,
    WarningItem,
)
from app.modules.events.context import SharedEventContext

ENGINE_RULES_VERSION = "1.0.0"


def calculate_impact(
    context: SharedEventContext,
    request: TypedChangeRequest,
    task_rows: list[dict[str, Any]],
    quote_rows: list[dict[str, Any]],
    registry_row: dict[str, Any] | None,
) -> ImpactResult:
    all_records: list[AffectedRecord] = []
    all_calcs: list[CalculationItem] = []
    all_warnings: list[WarningItem] = []
    all_options: list[SuggestedOption] = []

    # 1. Event & PlanAI rules
    e_records, e_calcs, e_warnings = evaluate_event_rules(context, request)
    all_records.extend(e_records)
    all_calcs.extend(e_calcs)
    all_warnings.extend(e_warnings)

    # 2. BudgetAI rules
    b_records, b_calcs, b_warnings, b_options = evaluate_budget_rules(context, request)
    all_records.extend(b_records)
    all_calcs.extend(b_calcs)
    all_warnings.extend(b_warnings)
    all_options.extend(b_options)

    # 3. TimelineAI rules
    t_records, t_calcs, t_warnings, t_options = evaluate_timeline_rules(context, request, task_rows)
    all_records.extend(t_records)
    all_calcs.extend(t_calcs)
    all_warnings.extend(t_warnings)
    all_options.extend(t_options)

    # 4. VendorConnect rules
    v_records, v_calcs, v_warnings, v_options = evaluate_vendor_rules(context, request, quote_rows)
    all_records.extend(v_records)
    all_calcs.extend(v_calcs)
    all_warnings.extend(v_warnings)
    all_options.extend(v_options)

    # 5. GiftCircle rules
    g_records, g_calcs, g_warnings, g_options = evaluate_gift_rules(context, request, registry_row)
    all_records.extend(g_records)
    all_calcs.extend(g_calcs)
    all_warnings.extend(g_warnings)
    all_options.extend(g_options)

    # Determine overall severity
    severity: Literal["low", "medium", "high", "critical"] = "low"
    severities = {w.severity for w in all_warnings}
    if "critical" in severities:
        severity = "critical"
    elif "high" in severities:
        severity = "high"
    elif "medium" in severities or all_records:
        severity = "medium"
    elif all_warnings:
        severity = "low"

    # Identify distinct affected modules
    affected_modules = sorted({r.module for r in all_records})

    return ImpactResult(
        rules_version=ENGINE_RULES_VERSION,
        severity=severity,
        affected_modules=affected_modules,
        affected_records=all_records,
        calculations=all_calcs,
        warnings=all_warnings,
        suggested_options=all_options,
    )

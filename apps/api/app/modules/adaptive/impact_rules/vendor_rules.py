"""Deterministic rules for VendorConnect quotations and contracts."""

from __future__ import annotations

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


def evaluate_vendor_rules(
    context: SharedEventContext,
    request: TypedChangeRequest,
    quote_rows: list[dict[str, Any]],
) -> tuple[list[AffectedRecord], list[CalculationItem], list[WarningItem], list[SuggestedOption]]:
    records: list[AffectedRecord] = []
    calcs: list[CalculationItem] = []
    warnings: list[WarningItem] = []
    options: list[SuggestedOption] = []

    if not quote_rows:
        return records, calcs, warnings, options

    # 1. Quotation validity vs revised event date
    if request.event_changes and (request.event_changes.start_at or request.event_changes.end_at):
        new_start = request.event_changes.start_at or context.event.start_at
        new_start_date = new_start.date()

        expired_quotes: list[dict[str, Any]] = []
        for q in quote_rows:
            valid_until = q.get("valid_until")
            q_status = q.get("quote_status")
            if (
                valid_until
                and q_status in ("received", "shortlisted", "accepted")
                and valid_until < new_start_date
            ):
                expired_quotes.append(q)
                records.append(
                    AffectedRecord(
                        module="vendors",
                        entity_type="vendor_quote",
                        entity_id=str(q["quote_id"]),
                        entity_name=f"{q.get('vendor_name', 'Vendor')} Quote",
                        change_nature="quote_expired_for_date",
                        details=(
                            f"Quote expired on {valid_until} before revised event start date {new_start_date}"
                        ),
                    )
                )

        if expired_quotes:
            warnings.append(
                WarningItem(
                    code="WARN_VENDOR_QUOTE_EXPIRED",
                    message=(
                        f"{len(expired_quotes)} vendor quotation(s) will expire or have expired "
                        f"before the revised event start date ({new_start_date})."
                    ),
                    severity="high",
                    recommended_action=(
                        "Request revised validity dates or re-negotiate quotes with the affected vendors."
                    ),
                )
            )
            calcs.append(
                CalculationItem(
                    metric="Expiring Vendor Quotes",
                    before_value="0",
                    after_value=str(len(expired_quotes)),
                    delta=f"+{len(expired_quotes)}",
                    unit="quotes",
                )
            )

    # 2. Guest count scale on catering/venue vendors
    if request.event_changes and request.event_changes.expected_guest_count is not None:
        old_count = context.event.expected_guest_count
        new_count = request.event_changes.expected_guest_count
        if abs(new_count - old_count) >= 25:
            # Find catering or venue quotes
            scale_quotes = [
                q
                for q in quote_rows
                if q.get("category", "").lower() in ("catering", "venue", "food & beverage", "banquet")
            ]
            if scale_quotes:
                for q in scale_quotes[:5]:
                    records.append(
                        AffectedRecord(
                            module="vendors",
                            entity_type="vendor_quote",
                            entity_id=str(q["quote_id"]),
                            entity_name=f"{q.get('vendor_name', 'Vendor')} ({q.get('category')})",
                            change_nature="guest_scale_impact",
                            details=(
                                f"Quote scope was based on earlier attendee count; guest delta is "
                                f"{new_count - old_count:+d}"
                            ),
                        )
                    )
                warnings.append(
                    WarningItem(
                        code="WARN_VENDOR_GUEST_CAPACITY",
                        message=(
                            f"{len(scale_quotes)} guest-sensitive vendor quotation(s) (catering/venue) "
                            "may require updated headcount pricing."
                        ),
                        severity="medium",
                        recommended_action=(
                            "Contact catering and venue vendors to update headcount in formal quotations."
                        ),
                    )
                )

    if records:
        options.append(
            SuggestedOption(
                id="opt_mark_vendor_quotes_review",
                title="Flag Affected Vendor Quotes for Reconfirmation",
                description=(
                    "Record audit notifications on affected vendor quotes so the team re-verifies "
                    "availability and rates for the revised event."
                ),
                operations=[
                    ProposedOperation(
                        op_code="op_mark_vendor_quotes_review",
                        target_module="vendors",
                        description=f"Flag {len(records)} quotation records for re-confirmation",
                        payload={"affected_quote_count": len(records)},
                    )
                ],
                selected_by_default=True,
            )
        )

    return records, calcs, warnings, options

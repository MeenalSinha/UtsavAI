"""Deterministic rules for GiftCircle wedding gift registry."""

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


def evaluate_gift_rules(
    context: SharedEventContext,
    request: TypedChangeRequest,
    registry_row: dict[str, Any] | None,
) -> tuple[list[AffectedRecord], list[CalculationItem], list[WarningItem], list[SuggestedOption]]:
    records: list[AffectedRecord] = []
    calcs: list[CalculationItem] = []
    warnings: list[WarningItem] = []
    options: list[SuggestedOption] = []

    if not registry_row:
        return records, calcs, warnings, options

    # Date shift evaluation on registry expiry
    if request.event_changes and (request.event_changes.start_at or request.event_changes.end_at):
        new_end = request.event_changes.end_at or context.event.end_at
        current_expiry = registry_row.get("expires_at")

        if current_expiry and current_expiry < new_end:
            records.append(
                AffectedRecord(
                    module="giftcircle",
                    entity_type="gift_registry",
                    entity_id=str(registry_row["id"]),
                    entity_name=registry_row.get("title", "Gift Registry"),
                    change_nature="registry_expires_before_event_end",
                    details=(
                        f"Registry expires on {current_expiry.strftime('%Y-%m-%d')} before "
                        f"new event end {new_end.strftime('%Y-%m-%d')}"
                    ),
                )
            )

            warnings.append(
                WarningItem(
                    code="WARN_GIFT_REGISTRY_EARLY_EXPIRY",
                    message=(
                        "Gift registry expiration date falls before the revised celebration end date. "
                        "Guests will be unable to view or contribute toward gifts."
                    ),
                    severity="high",
                    recommended_action=(
                        "Extend the gift registry expiry date to remain open after celebration."
                    ),
                )
            )

            suggested_new_expiry = new_end + timedelta(days=14)
            calcs.append(
                CalculationItem(
                    metric="Gift Registry Expiry",
                    before_value=current_expiry.strftime("%Y-%m-%d"),
                    after_value=suggested_new_expiry.strftime("%Y-%m-%d"),
                    delta=f"+{(suggested_new_expiry - current_expiry).days}d",
                    unit="days",
                )
            )

            exp_str = suggested_new_expiry.strftime("%Y-%m-%d")
            options.append(
                SuggestedOption(
                    id="opt_extend_gift_registry",
                    title="Extend Gift Registry Expiration",
                    description=(
                        f"Extend public gift registry access until {exp_str} (event end + 14 days buffer). "
                        "All existing pledges and reservations remain intact."
                    ),
                    operations=[
                        ProposedOperation(
                            op_code="op_extend_gift_registry_expiry",
                            target_module="giftcircle",
                            description="Extend gift registry expiration to event end + 14 days",
                            payload={
                                "registry_id": str(registry_row["id"]),
                                "new_expires_at": suggested_new_expiry.isoformat(),
                            },
                        )
                    ],
                    selected_by_default=True,
                )
            )

    return records, calcs, warnings, options

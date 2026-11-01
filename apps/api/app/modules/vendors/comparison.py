"""Deterministic quotation comparison engine for VendorConnect."""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from psycopg.rows import DictRow

from app.core.domain import QuoteStatus, VendorStatus
from app.modules.vendors.schemas import (
    QuotationComparisonGroup,
    QuotationComparisonItem,
    QuotationComparisonOut,
)


def _extract_guest_count(text: str) -> int | None:
    """Detect guest or plate count mentions in scope summary for factual comparison."""
    match = re.search(r"(\d{2,5})\s*(?:guests?|pax|plates?|people|persons?)", text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def generate_quotation_comparison(
    event_id: uuid.UUID,
    event_currency: str,
    raw_quotes: Sequence[DictRow],
) -> QuotationComparisonOut:
    """Builds a deterministic, category-grouped quotation comparison."""
    today = date.today()

    # Group by category
    category_map: dict[str, list[DictRow]] = defaultdict(list)
    for q in raw_quotes:
        category_map[q["category"]].append(q)

    groups: list[QuotationComparisonGroup] = []
    total_quotes = len(raw_quotes)

    for category, rows in sorted(category_map.items()):
        items: list[QuotationComparisonItem] = []
        guest_counts: dict[uuid.UUID, int] = {}
        amounts: list[Decimal] = []

        for r in rows:
            amt = Decimal(str(r["amount"]))
            amounts.append(amt)
            missing: list[str] = []
            warnings: list[str] = []

            # Missing information detection
            if r["valid_until"] is None:
                missing.append("Quotation validity date missing")
            else:
                if r["valid_until"] < today:
                    warnings.append(f"Quotation expired on {r['valid_until'].isoformat()}")

            if not r["phone"] and not r["email"]:
                missing.append("Vendor contact information (phone/email) not recorded")

            scope = (r["scope_summary"] or "").strip()
            if len(scope) < 15:
                warnings.append("Scope summary is very brief; specific deliverables not detailed")

            # Extract guest count if present
            guests = _extract_guest_count(scope)
            if guests:
                guest_counts[r["quote_id"]] = guests

            # Currency check
            if r["currency"] != event_currency:
                warnings.append(f"Currency mismatch ({r['currency']} vs event {event_currency})")

            item = QuotationComparisonItem(
                vendor_id=r["vendor_id"],
                vendor_name=r["vendor_name"],
                vendor_status=VendorStatus(r["vendor_status"]),
                quote_id=r["quote_id"],
                amount=amt,
                currency=r["currency"],
                scope_summary=scope,
                valid_until=r["valid_until"],
                status=QuoteStatus(r["quote_status"]),
                missing_fields=missing,
                comparison_warnings=warnings,
                updated_at=r["quote_updated_at"],
            )
            items.append(item)

        # Cross-quote category warnings
        cat_warnings: list[str] = []
        distinct_guests = set(guest_counts.values())
        if len(distinct_guests) > 1:
            diff_str = ", ".join(f"{g} guests" for g in sorted(distinct_guests))
            cat_warnings.append(
                f"Quoted scopes cover varying guest counts ({diff_str}). "
                "Ensure per-head parity before comparing totals."
            )

        if len(amounts) >= 2:
            min_amt = min(amounts)
            max_amt = max(amounts)
            if min_amt > 0 and (max_amt / min_amt) >= Decimal("2.0"):
                cat_warnings.append(
                    "Significant price variance (>2x) detected across proposals. "
                    "Verify if scope deliverables and materials differ."
                )

        # Sort items by amount ascending for readability (without declaring best/winner)
        items.sort(key=lambda x: x.amount)

        groups.append(
            QuotationComparisonGroup(
                category=category,
                quotes=items,
                category_warnings=cat_warnings,
                price_range_min=min(amounts) if amounts else None,
                price_range_max=max(amounts) if amounts else None,
            )
        )

    return QuotationComparisonOut(
        event_id=event_id,
        currency=event_currency,
        groups=groups,
        total_quotes_compared=total_quotes,
    )

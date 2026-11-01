"""Unit tests for VendorConnect deterministic quotation comparison engine."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app.modules.vendors.comparison import _extract_guest_count, generate_quotation_comparison


def test_extract_guest_count():
    assert _extract_guest_count("Buffet dinner for 300 guests with live counters") == 300
    assert _extract_guest_count("Full royal spread for 450 pax") == 450
    assert _extract_guest_count("Catering for 200 plates") == 200
    assert _extract_guest_count("Standard photography package") is None


def test_quotation_comparison_grouping_and_warnings():
    event_id = uuid.uuid4()
    currency = "INR"
    today = date.today()

    v1_id = uuid.uuid4()
    v2_id = uuid.uuid4()
    v3_id = uuid.uuid4()

    now = datetime.now(UTC)

    raw_quotes = [
        {
            "quote_id": uuid.uuid4(),
            "vendor_id": v1_id,
            "vendor_name": "Royal Feast Caterers",
            "category": "catering",
            "vendor_status": "quoted",
            "contact_name": "Chef Sharma",
            "email": "sharma@example.test",
            "phone": "+91 98765 43210",
            "website_url": "https://royalfeast.example",
            "amount": Decimal("400000.00"),
            "currency": "INR",
            "scope_summary": "Dinner buffet for 250 guests including desserts and chaat counter",
            "valid_until": today + timedelta(days=15),
            "quote_notes": "Live counters included",
            "quote_status": "received",
            "quote_created_at": now,
            "quote_updated_at": now,
            "archived_at": None,
        },
        {
            "quote_id": uuid.uuid4(),
            "vendor_id": v2_id,
            "vendor_name": "Maharaja Banquets",
            "category": "catering",
            "vendor_status": "quoted",
            "contact_name": "Manager Verma",
            "email": None,
            "phone": None,  # Contact info missing
            "website_url": None,
            "amount": Decimal("900000.00"),  # >2x variance
            "currency": "INR",
            "scope_summary": "Luxury 7-course dinner for 350 guests with international cuisine",
            "valid_until": None,  # Validity date missing
            "quote_notes": None,
            "quote_status": "received",
            "quote_created_at": now,
            "quote_updated_at": now,
            "archived_at": None,
        },
        {
            "quote_id": uuid.uuid4(),
            "vendor_id": v3_id,
            "vendor_name": "Vivid Studio",
            "category": "photography",
            "vendor_status": "identified",
            "contact_name": "Photographer",
            "email": "vivid@example.test",
            "phone": "+91 99999 88888",
            "website_url": None,
            "amount": Decimal("150000.00"),
            "currency": "INR",
            "scope_summary": "Two-day wedding photo & video coverage",
            "valid_until": today - timedelta(days=2),  # Expired
            "quote_notes": None,
            "quote_status": "received",
            "quote_created_at": now,
            "quote_updated_at": now,
            "archived_at": None,
        },
    ]

    res = generate_quotation_comparison(
        event_id=event_id,
        event_currency=currency,
        raw_quotes=raw_quotes,
    )

    assert res.event_id == event_id
    assert res.currency == currency
    assert res.total_quotes_compared == 3
    assert len(res.groups) == 2

    groups_by_cat = {g.category: g for g in res.groups}
    assert "catering" in groups_by_cat
    assert "photography" in groups_by_cat

    # Check Catering group
    cat_group = groups_by_cat["catering"]
    assert len(cat_group.quotes) == 2
    assert cat_group.price_range_min == Decimal("400000.00")
    assert cat_group.price_range_max == Decimal("900000.00")

    # Assert category warnings: guest count variance & price variance > 2x
    assert any("varying guest counts" in w for w in cat_group.category_warnings)
    assert any("price variance (>2x)" in w for w in cat_group.category_warnings)

    # Check individual missing info / warnings on Maharaja Banquets
    maharaja_quote = next(q for q in cat_group.quotes if q.vendor_name == "Maharaja Banquets")
    assert any("validity date missing" in m.lower() for m in maharaja_quote.missing_fields)
    assert any("contact information" in m.lower() for m in maharaja_quote.missing_fields)

    # Check expired warning on Vivid Studio
    photo_group = groups_by_cat["photography"]
    photo_quote = photo_group.quotes[0]
    assert any("expired" in w.lower() for w in photo_quote.comparison_warnings)

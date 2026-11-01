"""Integration tests for Phase 4: VendorConnect module."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from tests.integration.conftest import event_payload

BASE = "/api/v1"


def add_member(admin, event_id, user_id, role, status="active"):
    admin.execute("insert into public.profiles (user_id) values (%s) on conflict do nothing", (user_id,))
    admin.execute(
        "insert into public.event_members (event_id, user_id, role, status) values (%s, %s, %s, %s)",
        (event_id, user_id, role, status),
    )


# ------------------------------------------------------------------ Vendor Lifecycle & Quotes
def test_vendor_lifecycle_and_quotes(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    assert res.status_code == 201
    event_id = res.json()["id"]

    # 1. Create vendors
    v1 = client.post(
        f"{BASE}/events/{event_id}/vendors",
        json={
            "category": "catering",
            "name": "Royal Feast Catering",
            "contact_name": "Chef Sharma",
            "email": "sharma@example.test",
            "phone": "+91 98765 43210",
            "website_url": "https://royalfeast.example",
            "notes": "Met at food expo",
        },
        headers=u.headers,
    )
    assert v1.status_code == 201
    v1_data = v1.json()
    assert v1_data["status"] == "identified"
    assert v1_data["category"] == "catering"
    vendor_id = v1_data["id"]

    # 2. Add quotation
    q1 = client.post(
        f"{BASE}/events/{event_id}/vendors/{vendor_id}/quotes",
        json={
            "amount": "450000.00",
            "currency": "INR",
            "scope_summary": "Dinner catering for 300 guests with dessert counters",
            "valid_until": (date.today() + timedelta(days=30)).isoformat(),
            "notes": "Excludes alcohol",
        },
        headers=u.headers,
    )
    assert q1.status_code == 201
    q1_data = q1.json()
    assert Decimal(str(q1_data["amount"])) == Decimal("450000.00")
    assert q1_data["status"] == "received"
    quote_id = q1_data["id"]

    # Vendor status should auto-advance to 'quoted'
    v_details = client.get(f"{BASE}/events/{event_id}/vendors/{vendor_id}", headers=u.headers).json()
    assert v_details["status"] == "quoted"
    assert len(v_details["quotes"]) == 1

    # 3. Shortlist quotation
    q_patch = client.patch(
        f"{BASE}/events/{event_id}/vendors/{vendor_id}/quotes/{quote_id}",
        json={"status": "shortlisted"},
        headers=u.headers,
    )
    assert q_patch.status_code == 200
    assert q_patch.json()["status"] == "shortlisted"

    # Quotation status update is semantically distinct from vendor booking status
    v_details2 = client.get(f"{BASE}/events/{event_id}/vendors/{vendor_id}", headers=u.headers).json()
    assert v_details2["status"] == "quoted"

    # 4. Accept quotation and verify quotation is accepted
    q_accept = client.patch(
        f"{BASE}/events/{event_id}/vendors/{vendor_id}/quotes/{quote_id}",
        json={"status": "accepted"},
        headers=u.headers,
    )
    assert q_accept.status_code == 200
    assert q_accept.json()["status"] == "accepted"

    # Vendor requires an explicit booking decision from the host
    v_patch = client.patch(
        f"{BASE}/events/{event_id}/vendors/{vendor_id}",
        json={"status": "booked"},
        headers=u.headers,
    )
    assert v_patch.status_code == 200
    assert v_patch.json()["status"] == "booked"

    v_details3 = client.get(f"{BASE}/events/{event_id}/vendors/{vendor_id}", headers=u.headers).json()
    assert v_details3["status"] == "booked"

    # 5. Soft archive vendor
    del_res = client.delete(f"{BASE}/events/{event_id}/vendors/{vendor_id}", headers=u.headers)
    assert del_res.status_code == 204

    # Default list excludes archived
    active_vendors = client.get(f"{BASE}/events/{event_id}/vendors", headers=u.headers).json()
    assert not any(v["id"] == vendor_id for v in active_vendors)

    # Including archived lists it
    all_vendors = client.get(
        f"{BASE}/events/{event_id}/vendors?include_archived=true", headers=u.headers
    ).json()
    assert any(v["id"] == vendor_id for v in all_vendors)

    # Adding quote to archived vendor must fail
    q_fail = client.post(
        f"{BASE}/events/{event_id}/vendors/{vendor_id}/quotes",
        json={
            "amount": "100000.00",
            "currency": "INR",
            "scope_summary": "Supplementary",
        },
        headers=u.headers,
    )
    assert q_fail.status_code == 403


# ------------------------------------------------------------------ BudgetAI & Expense Integration
def test_expense_vendor_association(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    # 1. Initialize budget and category
    client.post(f"{BASE}/events/{event_id}/budget", json={"total_limit": "1000000.00"}, headers=u.headers)
    cat = client.post(
        f"{BASE}/events/{event_id}/budget/categories",
        json={"category_key": "catering", "name": "Catering", "planned_amount": "500000.00"},
        headers=u.headers,
    ).json()

    # 2. Create vendor
    v = client.post(
        f"{BASE}/events/{event_id}/vendors",
        json={"category": "catering", "name": "Gourmet Kitchen"},
        headers=u.headers,
    ).json()
    vendor_id = v["id"]

    # 3. Create expense linked to vendor
    exp = client.post(
        f"{BASE}/events/{event_id}/expenses",
        json={
            "budget_category_id": cat["id"],
            "vendor_id": vendor_id,
            "description": "Catering advance deposit",
            "amount": "150000.00",
            "status": "paid",
        },
        headers=u.headers,
    )
    assert exp.status_code == 201
    exp_data = exp.json()
    assert exp_data["vendor_id"] == vendor_id

    # 4. Check vendor details include associated expense
    v_details = client.get(f"{BASE}/events/{event_id}/vendors/{vendor_id}", headers=u.headers).json()
    assert v_details["associated_expenses_count"] == 1
    assert Decimal(str(v_details["total_spent_amount"])) == Decimal("150000.00")
    assert len(v_details["associated_expenses"]) == 1
    assert v_details["associated_expenses"][0]["id"] == exp_data["id"]

    # 5. Associating expense with non-existent or foreign vendor must fail
    fake_exp = client.post(
        f"{BASE}/events/{event_id}/expenses",
        json={
            "budget_category_id": cat["id"],
            "vendor_id": "00000000-0000-0000-0000-000000000000",
            "description": "Bad vendor",
            "amount": "50000.00",
            "status": "planned",
        },
        headers=u.headers,
    )
    assert fake_exp.status_code == 400


# ------------------------------------------------------------------ Quotation Comparison & Context
def test_quotation_comparison_and_event_context(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    # Create two catering vendors with quotes
    v1 = client.post(
        f"{BASE}/events/{event_id}/vendors",
        json={"category": "catering", "name": "Royal Feast", "phone": "+91 99999 11111"},
        headers=u.headers,
    ).json()
    client.post(
        f"{BASE}/events/{event_id}/vendors/{v1['id']}/quotes",
        json={
            "amount": "400000.00",
            "currency": "INR",
            "scope_summary": "Buffet for 300 guests with sweets",
            "valid_until": (date.today() + timedelta(days=20)).isoformat(),
        },
        headers=u.headers,
    )

    v2 = client.post(
        f"{BASE}/events/{event_id}/vendors",
        json={"category": "catering", "name": "Grand Caterers"},
        headers=u.headers,
    ).json()
    client.post(
        f"{BASE}/events/{event_id}/vendors/{v2['id']}/quotes",
        json={
            "amount": "500000.00",
            "currency": "INR",
            "scope_summary": "Full service dinner for 350 guests",
            # valid_until missing intentionally
        },
        headers=u.headers,
    )

    # 1. Fetch quotation comparison
    comp_res = client.get(f"{BASE}/events/{event_id}/vendor-quote-comparison", headers=u.headers)
    assert comp_res.status_code == 200
    comp = comp_res.json()

    assert comp["event_id"] == event_id
    assert comp["total_quotes_compared"] == 2
    assert len(comp["groups"]) == 1
    group = comp["groups"][0]
    assert group["category"] == "catering"
    assert len(group["quotes"]) == 2
    # Verify guest variance warning
    assert any("varying guest counts" in w for w in group["category_warnings"])

    # 2. Fetch shared event context and assert vendor_summary
    ctx_res = client.get(f"{BASE}/events/{event_id}/context", headers=u.headers)
    assert ctx_res.status_code == 200
    ctx = ctx_res.json()
    assert "vendor_summary" in ctx and ctx["vendor_summary"] is not None
    v_summary = ctx["vendor_summary"]
    assert v_summary["total_vendors"] == 2
    assert v_summary["quote_count"] == 2
    assert len(v_summary["categories"]) == 1
    assert v_summary["categories"][0]["category"] == "catering"
    assert v_summary["categories"][0]["vendor_count"] == 2


# ------------------------------------------------------------------ Cross-Event Authorization
def test_cross_user_vendor_isolation(client, make_user, admin):
    host_a = make_user("host_a")
    host_b = make_user("host_b")

    res_a = client.post(f"{BASE}/events", json=event_payload(), headers=host_a.headers)
    event_a = res_a.json()["id"]

    v_a = client.post(
        f"{BASE}/events/{event_a}/vendors",
        json={"category": "decor", "name": "Secret Palace Decor"},
        headers=host_a.headers,
    ).json()
    vendor_id = v_a["id"]

    # Host B attempts to read Host A's vendors
    res_b_list = client.get(f"{BASE}/events/{event_a}/vendors", headers=host_b.headers)
    assert res_b_list.status_code in (403, 404)

    # Host B attempts to view single vendor details
    res_b_get = client.get(f"{BASE}/events/{event_a}/vendors/{vendor_id}", headers=host_b.headers)
    assert res_b_get.status_code in (403, 404)

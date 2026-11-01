"""Integration tests for Phase 3: BudgetAI and TimelineAI modules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.modules.ai.provider import FakeGenerationProvider
from tests.integration.conftest import event_payload

BASE = "/api/v1"


def add_member(admin, event_id, user_id, role, status="active"):
    admin.execute("insert into public.profiles (user_id) values (%s) on conflict do nothing", (user_id,))
    admin.execute(
        "insert into public.event_members (event_id, user_id, role, status) values (%s, %s, %s, %s)",
        (event_id, user_id, role, status),
    )


# ------------------------------------------------------------------ Budget Lifecycle & Summary
def test_budget_lifecycle_and_summary(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    assert res.status_code == 201
    event_id = res.json()["id"]

    # 1. Initialize budget
    b_res = client.post(
        f"{BASE}/events/{event_id}/budget",
        json={"total_limit": "2000000.00"},
        headers=u.headers,
    )
    assert b_res.status_code == 201
    b_data = b_res.json()
    assert Decimal(str(b_data["total_limit"])) == Decimal("2000000.00")
    assert b_data["currency"] == "INR"

    # 2. Add categories
    c1 = client.post(
        f"{BASE}/events/{event_id}/budget/categories",
        json={"category_key": "venue", "name": "Venue Booking", "planned_amount": "800000.00"},
        headers=u.headers,
    ).json()
    c2 = client.post(
        f"{BASE}/events/{event_id}/budget/categories",
        json={"category_key": "catering", "name": "Catering Services", "planned_amount": "600000.00"},
        headers=u.headers,
    ).json()

    # 3. Add expenses
    e1 = client.post(
        f"{BASE}/events/{event_id}/expenses",
        json={
            "budget_category_id": c1["id"],
            "description": "Venue deposit",
            "amount": "200000.00",
            "status": "paid",
        },
        headers=u.headers,
    ).json()
    assert Decimal(str(e1["amount"])) == Decimal("200000.00")

    e2 = client.post(
        f"{BASE}/events/{event_id}/expenses",
        json={
            "budget_category_id": c2["id"],
            "description": "Catering advance contract",
            "amount": "300000.00",
            "status": "committed",
        },
        headers=u.headers,
    ).json()
    assert e2["status"] == "committed"

    # 4. Check budget summary
    summary_res = client.get(f"{BASE}/events/{event_id}/budget/summary", headers=u.headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()

    assert Decimal(str(summary["total_limit"])) == Decimal("2000000.00")
    assert Decimal(str(summary["total_allocated"])) == Decimal("1400000.00")
    assert Decimal(str(summary["unallocated_amount"])) == Decimal("600000.00")
    assert Decimal(str(summary["paid_expenses"])) == Decimal("200000.00")
    assert Decimal(str(summary["committed_expenses"])) == Decimal("300000.00")
    assert Decimal(str(summary["projected_total"])) == Decimal("500000.00")
    assert Decimal(str(summary["remaining_after_committed"])) == Decimal("1500000.00")
    assert Decimal(str(summary["projected_headroom"])) == Decimal("1500000.00")


def test_category_deletion_protection_with_active_expenses(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    client.post(
        f"{BASE}/events/{event_id}/budget",
        json={"total_limit": "500000.00"},
        headers=u.headers,
    )
    cat = client.post(
        f"{BASE}/events/{event_id}/budget/categories",
        json={"category_key": "decor", "name": "Decorations", "planned_amount": "100000.00"},
        headers=u.headers,
    ).json()

    client.post(
        f"{BASE}/events/{event_id}/expenses",
        json={
            "budget_category_id": cat["id"],
            "description": "Flowers advance",
            "amount": "25000.00",
            "status": "committed",
        },
        headers=u.headers,
    )

    # Deleting category with active expense must fail with 409 Conflict
    del_res = client.delete(f"{BASE}/events/{event_id}/budget/categories/{cat['id']}", headers=u.headers)
    assert del_res.status_code == 409


# ------------------------------------------------------------------ Timeline & Tasks
def test_task_lifecycle_and_dependencies(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    now = datetime.now(UTC)
    t1 = client.post(
        f"{BASE}/events/{event_id}/tasks",
        json={
            "title": "Book Wedding Venue",
            "priority": "urgent",
            "due_at": (now + timedelta(days=10)).isoformat(),
        },
        headers=u.headers,
    ).json()

    t2 = client.post(
        f"{BASE}/events/{event_id}/tasks",
        json={
            "title": "Finalize Decor Theme",
            "priority": "high",
            "due_at": (now + timedelta(days=20)).isoformat(),
        },
        headers=u.headers,
    ).json()

    # Add valid dependency: t2 depends on t1 (t1 is prerequisite, due at day 10 <= t2 due at day 20)
    dep_res = client.post(
        f"{BASE}/events/{event_id}/tasks/{t2['id']}/dependencies",
        json={"depends_on_task_id": t1["id"]},
        headers=u.headers,
    )
    assert dep_res.status_code == 201

    # Attempt circular dependency: t1 depends on t2 (creates t1 -> t2 -> t1 cycle)
    cycle_res = client.post(
        f"{BASE}/events/{event_id}/tasks/{t1['id']}/dependencies",
        json={"depends_on_task_id": t2["id"]},
        headers=u.headers,
    )
    assert cycle_res.status_code == 409

    # Attempt self-dependency: t1 depends on t1
    self_res = client.post(
        f"{BASE}/events/{event_id}/tasks/{t1['id']}/dependencies",
        json={"depends_on_task_id": t1["id"]},
        headers=u.headers,
    )
    assert self_res.status_code == 400

    # Complete t1
    patch_res = client.patch(
        f"{BASE}/events/{event_id}/tasks/{t1['id']}",
        json={"status": "done"},
        headers=u.headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "done"
    assert patch_res.json()["completed_at"] is not None

    # Remove dependency
    del_dep = client.delete(
        f"{BASE}/events/{event_id}/tasks/{t2['id']}/dependencies/{t1['id']}",
        headers=u.headers,
    )
    assert del_dep.status_code == 204

    # Check timeline summary
    summary_res = client.get(f"{BASE}/events/{event_id}/timeline/summary", headers=u.headers)
    assert summary_res.status_code == 200
    timeline = summary_res.json()
    assert timeline["total_tasks"] == 2
    assert timeline["completed_tasks"] == 1
    assert timeline["completion_percentage"] == 50.0


# ------------------------------------------------------------------ Shared Event Context Integration
def test_shared_event_context_includes_budget_and_timeline(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    client.post(
        f"{BASE}/events/{event_id}/budget",
        json={"total_limit": "1500000.00"},
        headers=u.headers,
    )
    client.post(
        f"{BASE}/events/{event_id}/tasks",
        json={"title": "Photographer shortlist", "priority": "medium"},
        headers=u.headers,
    )

    ctx_res = client.get(f"{BASE}/events/{event_id}/context", headers=u.headers)
    assert ctx_res.status_code == 200
    ctx = ctx_res.json()

    assert "budget" in ctx and ctx["budget"] is not None
    assert Decimal(str(ctx["budget"]["total_limit"])) == Decimal("1500000.00")
    assert "timeline" in ctx and ctx["timeline"] is not None
    assert ctx["timeline"]["total_tasks"] == 1


# ------------------------------------------------------------------ AI Budget and Timeline Proposals
def test_ai_budget_proposal_generation_and_acceptance(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    client.post(
        f"{BASE}/events/{event_id}/budget",
        json={"total_limit": "1000000.00"},
        headers=u.headers,
    )

    # Inject fake AI response
    fake_payload = {
        "schema_version": 1,
        "summary": "Tailored budget allocation for Rajasthan royal wedding",
        "assumptions": ["300 guests expected"],
        "warnings": [],
        "savings_recommendations": ["Combine sound and lighting vendors"],
        "follow_up_questions": [],
        "proposed_allocations": [
            {
                "category_key": "venue_catering",
                "name": "Palace Venue & Banquet",
                "percentage": 50.0,
                "suggested_amount": 500000.00,
                "notes": "Food and palace rental",
            },
            {
                "category_key": "decor_styling",
                "name": "Royal Floral Decor",
                "percentage": 50.0,
                "suggested_amount": 500000.00,
                "notes": "Mandap and lighting",
            },
        ],
    }
    client.app.state.ai_provider = FakeGenerationProvider(canned_response=fake_payload)

    gen_res = client.post(
        f"{BASE}/events/{event_id}/budget/ai/generate",
        json={"prompt": "Suggest allocations for our royal wedding"},
        headers=u.headers,
    )
    assert gen_res.status_code == 201
    prop = gen_res.json()
    proposal_id = prop["id"]
    base_rev = prop["base_revision"]

    # Accept proposal
    accept_res = client.post(
        f"{BASE}/events/{event_id}/budget/ai/proposals/{proposal_id}/accept",
        json={
            "base_revision": base_rev,
            "selected_category_keys": ["venue_catering", "decor_styling"],
        },
        headers=u.headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "accepted"

    # Verify categories in database
    cats = client.get(f"{BASE}/events/{event_id}/budget/categories", headers=u.headers).json()
    cat_keys = {c["category_key"] for c in cats}
    assert "venue_catering" in cat_keys
    assert "decor_styling" in cat_keys


def test_ai_timeline_proposal_generation_and_acceptance(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    now = datetime.now(UTC)
    fake_payload = {
        "schema_version": 1,
        "summary": "Preparation schedule leading to the ceremonies",
        "assumptions": [],
        "warnings": [],
        "follow_up_questions": [],
        "proposed_tasks": [
            {
                "client_ref": "t_venue",
                "title": "Confirm Venue Contract",
                "due_at": (now + timedelta(days=5)).isoformat(),
                "priority": "urgent",
                "function_ref": None,
                "depends_on": [],
            },
            {
                "client_ref": "t_caterer",
                "title": "Taste and finalize catering menu",
                "due_at": (now + timedelta(days=12)).isoformat(),
                "priority": "high",
                "function_ref": None,
                "depends_on": ["t_venue"],
            },
        ],
    }
    client.app.state.ai_provider = FakeGenerationProvider(canned_response=fake_payload)

    gen_res = client.post(
        f"{BASE}/events/{event_id}/timeline/ai/generate",
        json={"prompt": "Create preparation roadmap"},
        headers=u.headers,
    )
    assert gen_res.status_code == 201
    prop = gen_res.json()
    proposal_id = prop["id"]
    base_rev = prop["base_revision"]

    # Accept proposal
    accept_res = client.post(
        f"{BASE}/events/{event_id}/timeline/ai/proposals/{proposal_id}/accept",
        json={
            "base_revision": base_rev,
            "selected_task_refs": ["t_venue", "t_caterer"],
        },
        headers=u.headers,
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "accepted"

    # Verify tasks and dependencies in database
    tasks = client.get(f"{BASE}/events/{event_id}/tasks", headers=u.headers).json()
    assert len(tasks) == 2
    tasks_by_title = {t["title"]: t for t in tasks}
    assert "Confirm Venue Contract" in tasks_by_title
    assert "Taste and finalize catering menu" in tasks_by_title
    caterer_task = tasks_by_title["Taste and finalize catering menu"]
    venue_task = tasks_by_title["Confirm Venue Contract"]
    assert str(venue_task["id"]) in [str(d) for d in caterer_task["depends_on_task_ids"]]

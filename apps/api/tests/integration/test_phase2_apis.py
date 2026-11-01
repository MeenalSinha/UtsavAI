"""Integration tests for Phase 2: Context, Preferences, Functions, PlanAI, and Acceptance."""

from __future__ import annotations

from app.modules.ai.provider import FakeGenerationProvider
from tests.integration.conftest import event_payload

BASE = "/api/v1"


def add_member(admin, event_id, user_id, role, status="active"):
    admin.execute("insert into public.profiles (user_id) values (%s) on conflict do nothing", (user_id,))
    admin.execute(
        "insert into public.event_members (event_id, user_id, role, status) values (%s, %s, %s, %s)",
        (event_id, user_id, role, status),
    )


# ------------------------------------------------------------------ Preferences
def test_preferences_lifecycle_and_revision_touch(client, make_user, admin):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    assert res.status_code == 201
    event_id = res.json()["id"]
    initial_revision = res.json()["revision"]

    # 1. Get default preferences
    r_get = client.get(f"{BASE}/events/{event_id}/preferences", headers=u.headers)
    assert r_get.status_code == 200
    pref = r_get.json()
    assert pref["style_tags"] == []
    assert pref["schema_version"] == 1

    # 2. Update preferences
    payload = {
        "style_tags": ["Traditional", "Royal"],
        "cultural_context": {"region": "Rajasthan", "traditions": ["Marwari"]},
        "priorities": {"guest_experience": "high", "budget_conscious": True},
        "accessibility_notes": {"wheelchair_access": True},
        "schema_version": 1,
    }
    r_put = client.put(f"{BASE}/events/{event_id}/preferences", json=payload, headers=u.headers)
    assert r_put.status_code == 200
    updated = r_put.json()
    assert updated["style_tags"] == ["Traditional", "Royal"]
    assert updated["cultural_context"]["region"] == "Rajasthan"

    # 3. Verify parent event revision was automatically incremented
    r_ev = client.get(f"{BASE}/events/{event_id}", headers=u.headers)
    assert r_ev.json()["revision"] > initial_revision


def test_preferences_permissions_and_isolation(client, make_user, admin):
    owner = make_user("owner")
    viewer = make_user("viewer")
    stranger = make_user("stranger")

    res = client.post(f"{BASE}/events", json=event_payload(), headers=owner.headers)
    event_id = res.json()["id"]
    add_member(admin, event_id, viewer.id, "viewer")

    # Viewer can read
    assert client.get(f"{BASE}/events/{event_id}/preferences", headers=viewer.headers).status_code == 200

    # Viewer cannot update (403)
    r_viewer_put = client.put(
        f"{BASE}/events/{event_id}/preferences",
        json={"style_tags": ["Modern"], "schema_version": 1},
        headers=viewer.headers,
    )
    assert r_viewer_put.status_code == 403

    # Stranger cannot read (404)
    assert client.get(f"{BASE}/events/{event_id}/preferences", headers=stranger.headers).status_code == 404


# ------------------------------------------------------------------ Functions
def test_functions_crud_and_ordering(client, make_user):
    u = make_user("host")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    # 1. Create function
    f1 = client.post(
        f"{BASE}/events/{event_id}/functions",
        json={
            "name": "Mehendi Ceremony",
            "starts_at": "2027-02-12T14:00:00+05:30",
            "ends_at": "2027-02-12T18:00:00+05:30",
            "location_name": "Courtyard",
            "notes": "Green and yellow dress code",
            "sort_order": 1,
        },
        headers=u.headers,
    )
    assert f1.status_code == 201
    f1_id = f1.json()["id"]
    assert f1.json()["name"] == "Mehendi Ceremony"

    # 2. Create second function with negative sort order (should sort before)
    f2 = client.post(
        f"{BASE}/events/{event_id}/functions",
        json={"name": "Haldi", "sort_order": 0},
        headers=u.headers,
    )
    assert f2.status_code == 201

    # 3. List functions
    r_list = client.get(f"{BASE}/events/{event_id}/functions", headers=u.headers)
    assert r_list.status_code == 200
    fns = r_list.json()
    assert len(fns) == 2
    assert fns[0]["name"] == "Haldi"
    assert fns[1]["name"] == "Mehendi Ceremony"

    # 4. Patch function
    r_patch = client.patch(
        f"{BASE}/events/{event_id}/functions/{f1_id}",
        json={"notes": "Updated note"},
        headers=u.headers,
    )
    assert r_patch.status_code == 200
    assert r_patch.json()["notes"] == "Updated note"

    # 5. Invalid date range (ends_at < starts_at)
    bad_dates = client.post(
        f"{BASE}/events/{event_id}/functions",
        json={
            "name": "Invalid Times",
            "starts_at": "2027-02-12T18:00:00+05:30",
            "ends_at": "2027-02-12T14:00:00+05:30",
        },
        headers=u.headers,
    )
    assert bad_dates.status_code == 422

    # 6. Delete function
    r_del = client.delete(f"{BASE}/events/{event_id}/functions/{f1_id}", headers=u.headers)
    assert r_del.status_code == 204

    r_after = client.get(f"{BASE}/events/{event_id}/functions", headers=u.headers)
    assert len(r_after.json()) == 1


# ------------------------------------------------------------------ Context
def test_shared_event_context(client, make_user):
    u = make_user("planner")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    client.post(
        f"{BASE}/events/{event_id}/functions",
        json={"name": "Sangeet Night", "sort_order": 1},
        headers=u.headers,
    )
    client.put(
        f"{BASE}/events/{event_id}/preferences",
        json={"style_tags": ["Modern"], "schema_version": 1},
        headers=u.headers,
    )

    r_ctx = client.get(f"{BASE}/events/{event_id}/context", headers=u.headers)
    assert r_ctx.status_code == 200
    ctx = r_ctx.json()
    assert ctx["event"]["id"] == event_id
    assert ctx["preferences"]["style_tags"] == ["Modern"]
    assert len(ctx["functions"]) == 1
    assert ctx["functions"][0]["name"] == "Sangeet Night"
    assert ctx["permissions"]["can_edit"] is True
    assert ctx["permissions"]["can_generate_plan"] is True


# ------------------------------------------------------------------ PlanAI & Acceptance
def test_plan_generation_and_selective_acceptance(client, make_user):
    u = make_user("ai_planner")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]
    base_rev = res.json()["revision"]

    # Configure Fake provider on client.app.state
    fake_payload = {
        "schema_version": 1,
        "summary": "Personalized 3-day royal wedding in Jaipur.",
        "assumptions": ["Guest count 300."],
        "warnings": ["Check hotel block capacity early."],
        "follow_up_questions": ["Do you want a dedicated DJ for Sangeet?"],
        "theme_suggestions": ["Royal Rajputana", "Desert Sunset"],
        "proposed_functions": [
            {
                "client_ref": "fn_1",
                "name": "Mehendi",
                "starts_at": "2027-02-12T14:00:00+05:30",
                "ends_at": "2027-02-12T18:00:00+05:30",
                "location_name": "Courtyard",
                "notes": "Green decor",
                "sort_order": 1,
            },
            {
                "client_ref": "fn_2",
                "name": "Sangeet",
                "starts_at": "2027-02-12T19:00:00+05:30",
                "ends_at": "2027-02-12T23:30:00+05:30",
                "location_name": "Grand Ballroom",
                "notes": "Stage and audio setup",
                "sort_order": 2,
            },
        ],
        "proposed_tasks": [
            {
                "client_ref": "t_1",
                "title": "Book Mehendi Artist",
                "description": "Shortlist top artists",
                "due_at": "2026-12-01T12:00:00Z",
                "priority": "high",
                "function_ref": "fn_1",
                "depends_on": [],
            },
            {
                "client_ref": "t_2",
                "title": "Confirm Sound & DJ",
                "description": "Audio system for Sangeet",
                "due_at": "2026-12-15T12:00:00Z",
                "priority": "high",
                "function_ref": "fn_2",
                "depends_on": [],
            },
            {
                "client_ref": "t_3",
                "title": "Review DJ Playlist",
                "description": "Finalize tracklist",
                "due_at": "2027-01-10T12:00:00Z",
                "priority": "medium",
                "function_ref": "fn_2",
                "depends_on": ["t_2"],
            },
        ],
        "planning_notes": ["Begin vendor shortlisting at least 3 months ahead."],
    }
    client.app.state.ai_provider = FakeGenerationProvider(canned_response=fake_payload)

    # 1. Generate plan
    gen_req = {
        "request": "Plan a 3-day royal wedding in Jaipur for 300 guests.",
        "include": ["functions", "tasks", "themes"],
        "base_revision": base_rev,
    }
    r_gen = client.post(f"{BASE}/events/{event_id}/plans/generate", json=gen_req, headers=u.headers)
    assert r_gen.status_code == 201
    prop = r_gen.json()
    prop_id = prop["proposal_id"]
    assert prop["status"] == "proposed"
    assert len(prop["payload"]["proposed_functions"]) == 2
    assert len(prop["payload"]["proposed_tasks"]) == 3

    # 2. Test missing dependency rejection
    bad_accept = client.post(
        f"{BASE}/events/{event_id}/ai/proposals/{prop_id}/accept",
        json={
            "base_revision": base_rev,
            "selected_function_refs": ["fn_2"],
            "selected_task_refs": ["t_3"],  # Depends on t_2 which is not selected!
        },
        headers=u.headers,
    )
    assert bad_accept.status_code == 400
    assert "depends on" in bad_accept.json()["error"]["message"]

    # 3. Selective acceptance of fn_1 and t_1 (partial acceptance)
    accept_partial = client.post(
        f"{BASE}/events/{event_id}/ai/proposals/{prop_id}/accept",
        json={
            "base_revision": base_rev,
            "selected_function_refs": ["fn_1"],
            "selected_task_refs": ["t_1"],
        },
        headers=u.headers,
    )
    assert accept_partial.status_code == 200
    res_partial = accept_partial.json()
    assert res_partial["status"] == "partially_accepted"
    assert res_partial["accepted_functions_count"] == 1
    assert res_partial["accepted_tasks_count"] == 1
    new_rev = res_partial["new_revision"]
    assert new_rev > base_rev

    # 4. Verify function and task are persisted in database
    fns = client.get(f"{BASE}/events/{event_id}/functions", headers=u.headers).json()
    assert len(fns) == 1
    assert fns[0]["name"] == "Mehendi"

    # 5. Acceptance with outdated revision fails with 409
    stale_accept = client.post(
        f"{BASE}/events/{event_id}/ai/proposals/{prop_id}/accept",
        json={
            "base_revision": base_rev,  # Old revision!
            "selected_function_refs": ["fn_2"],
            "selected_task_refs": ["t_2", "t_3"],
        },
        headers=u.headers,
    )
    assert stale_accept.status_code == 409

    # 6. Re-fetching proposal reflects STALE status
    p_fetch = client.get(f"{BASE}/events/{event_id}/ai/proposals/{prop_id}", headers=u.headers)
    assert p_fetch.status_code == 200
    assert p_fetch.json()["status"] == "stale"


def test_conversations_and_messages(client, make_user):
    u = make_user("chatter")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    event_id = res.json()["id"]

    client.app.state.ai_provider = FakeGenerationProvider(
        canned_text="I recommend starting with venue shortlisting."
    )

    # 1. Create conversation
    c_res = client.post(
        f"{BASE}/events/{event_id}/ai/conversations",
        json={"title": "Venue Ideas"},
        headers=u.headers,
    )
    assert c_res.status_code == 201
    conv_id = c_res.json()["id"]

    # 2. Send message
    m_res = client.post(
        f"{BASE}/events/{event_id}/ai/conversations/{conv_id}/messages",
        json={"content": "What venues do you recommend in Jaipur?"},
        headers=u.headers,
    )
    assert m_res.status_code == 201
    assert m_res.json()["role"] == "assistant"
    assert "venue shortlisting" in m_res.json()["content"]

    # 3. Read conversation history
    detail = client.get(f"{BASE}/events/{event_id}/ai/conversations/{conv_id}", headers=u.headers)
    assert detail.status_code == 200
    msgs = detail.json()["messages"]
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"

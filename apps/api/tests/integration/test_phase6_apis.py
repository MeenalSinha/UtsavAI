"""Integration tests for Phase 6: Adaptive Planning Engine."""

from __future__ import annotations

from tests.integration.conftest import event_payload

BASE = "/api/v1"


def test_adaptive_planning_full_lifecycle(client, make_user):
    host = make_user("owner")
    editor = make_user("editor")
    viewer = make_user("viewer")
    stranger = make_user("stranger")

    # 1. Create event (owner)
    res = client.post(f"{BASE}/events", json=event_payload(), headers=host.headers)
    assert res.status_code == 201
    event = res.json()
    event_id = event["id"]
    base_rev = event["revision"]

    # Add editor and viewer
    client.post(
        f"{BASE}/events/{event_id}/members",
        json={"email": editor.email, "role": "editor"},
        headers=host.headers,
    )
    client.post(
        f"{BASE}/events/{event_id}/members",
        json={"email": viewer.email, "role": "viewer"},
        headers=host.headers,
    )

    # 2. Viewer cannot propose changes (403 Forbidden)
    viewer_prop = client.post(
        f"{BASE}/events/{event_id}/change-proposals",
        json={
            "base_revision": base_rev,
            "request_text": "Viewer attempted change",
            "event_changes": {"expected_guest_count": 500},
        },
        headers=viewer.headers,
    )
    assert viewer_prop.status_code == 403

    # 3. Stranger gets 404 (RLS isolation)
    stranger_res = client.get(
        f"{BASE}/events/{event_id}/change-proposals",
        headers=stranger.headers,
    )
    assert stranger_res.status_code == 404

    # 4. Editor creates a change proposal
    prop_res = client.post(
        f"{BASE}/events/{event_id}/change-proposals",
        json={
            "base_revision": base_rev,
            "request_text": "Increase guest count to 350 and add Sangeet Celebration",
            "event_changes": {
                "expected_guest_count": 350,
                "location_name": "Rambagh Palace Grand Hall",
            },
            "function_changes": [
                {
                    "action": "add",
                    "name": "Sangeet Celebration",
                    "function_type": "ceremony",
                }
            ],
        },
        headers=editor.headers,
    )
    assert prop_res.status_code == 201
    prop_data = prop_res.json()
    proposal_id = prop_data["id"]
    assert prop_data["status"] == "proposed"
    assert prop_data["base_revision"] == base_rev
    assert "event" in prop_data["impact_result"]["affected_modules"]
    assert len(prop_data["impact_result"]["calculations"]) > 0

    # 5. List proposals
    list_res = client.get(f"{BASE}/events/{event_id}/change-proposals", headers=host.headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 6. Get proposal by ID
    get_res = client.get(
        f"{BASE}/events/{event_id}/change-proposals/{proposal_id}",
        headers=viewer.headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == proposal_id

    # 7. Non-owner (editor) CANNOT accept proposal (strictly owner only)
    editor_accept = client.post(
        f"{BASE}/events/{event_id}/change-proposals/{proposal_id}/accept",
        json={"selected_option_ids": []},
        headers=editor.headers,
    )
    assert editor_accept.status_code == 403

    # 8. Owner accepts proposal atomically
    accept_res = client.post(
        f"{BASE}/events/{event_id}/change-proposals/{proposal_id}/accept",
        json={"selected_option_ids": []},
        headers=host.headers,
    )
    assert accept_res.status_code == 200
    accepted = accept_res.json()
    assert accepted["status"] == "accepted"
    assert accepted["accepted_revision"] == base_rev + 1

    # 9. Verify event was updated and revision advanced
    ev_updated = client.get(f"{BASE}/events/{event_id}", headers=host.headers).json()
    assert ev_updated["revision"] == base_rev + 1
    assert ev_updated["expected_guest_count"] == 350
    assert ev_updated["location_name"] == "Rambagh Palace Grand Hall"

    # 10. Verify function was created
    funcs = client.get(f"{BASE}/events/{event_id}/functions", headers=host.headers).json()
    assert any(f["name"] == "Sangeet Celebration" for f in funcs)

    # 11. Concurrency check: Stale base_revision proposal is rejected
    stale_prop = client.post(
        f"{BASE}/events/{event_id}/change-proposals",
        json={
            "base_revision": base_rev,  # Old revision!
            "request_text": "Stale revision proposal",
            "event_changes": {"expected_guest_count": 400},
        },
        headers=host.headers,
    )
    assert stale_prop.status_code == 409


def test_adaptive_proposal_rejection(client, make_user):
    host = make_user("owner")
    res = client.post(f"{BASE}/events", json=event_payload(), headers=host.headers)
    event_id = res.json()["id"]
    base_rev = res.json()["revision"]

    prop_res = client.post(
        f"{BASE}/events/{event_id}/change-proposals",
        json={
            "base_revision": base_rev,
            "request_text": "Proposal to be rejected",
            "event_changes": {"expected_guest_count": 450},
        },
        headers=host.headers,
    )
    proposal_id = prop_res.json()["id"]

    rej_res = client.post(
        f"{BASE}/events/{event_id}/change-proposals/{proposal_id}/reject",
        json={"reason": "Venue not available for this capacity"},
        headers=host.headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

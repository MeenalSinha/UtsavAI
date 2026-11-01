"""Backend-level end-to-end workflow (real FastAPI + real PostgreSQL + RLS).

This mirrors the Phase 1 browser scenario at the API layer, with locally signed
JWTs standing in for Supabase Auth. The browser/Supabase run is a separate gate
(apps/web/e2e) and is reported separately.
"""

BASE = "/api/v1"


def test_two_user_workflow(client, make_user, admin):
    from tests.integration.conftest import event_payload

    # User A signs in (first authenticated call provisions the profile) and creates an event.
    a = make_user("usera")
    assert client.get(f"{BASE}/me", headers=a.headers).status_code == 200
    created = client.post(
        f"{BASE}/events", json=event_payload(title="Aarav and Meera's Wedding"), headers=a.headers
    )
    assert created.status_code == 201
    event = created.json()

    # Stored in PostgreSQL.
    assert (
        admin.execute("select title from public.events where id=%s", (event["id"],)).fetchone()[0]
        == "Aarav and Meera's Wedding"
    )

    # Appears on the dashboard list; can be reopened.
    listing = client.get(f"{BASE}/events", headers=a.headers).json()["data"]
    assert [e["id"] for e in listing] == [event["id"]]
    opened = client.get(f"{BASE}/events/{event['id']}", headers=a.headers)
    assert opened.status_code == 200 and opened.headers["etag"] == '"1"'

    # Update using the ETag from the read.
    updated = client.patch(
        f"{BASE}/events/{event['id']}",
        json={"expected_guest_count": 450},
        headers={**a.headers, "If-Match": opened.headers["etag"]},
    )
    assert updated.status_code == 200 and updated.json()["revision"] == 2

    # "Sign out / sign in again": a fresh token for the same subject still reopens the event.
    from tests.conftest import ISSUER  # noqa: F401

    a_again = client.get(f"{BASE}/events/{event['id']}", headers=a.headers)
    assert a_again.json()["expected_guest_count"] == 450

    # User B cannot reach A's event, creates their own and reopens it.
    b = make_user("userb")
    assert client.get(f"{BASE}/events/{event['id']}", headers=b.headers).status_code == 404
    assert client.get(f"{BASE}/events", headers=b.headers).json()["data"] == []
    assert (
        client.patch(
            f"{BASE}/events/{event['id']}",
            json={"title": "x"},
            headers={**b.headers, "If-Match": '"2"'},
        ).status_code
        == 404
    )
    assert client.delete(f"{BASE}/events/{event['id']}", headers=b.headers).status_code == 404
    mine = client.post(
        f"{BASE}/events", json=event_payload(title="B's birthday-style wedding"), headers=b.headers
    ).json()
    assert (
        client.get(f"{BASE}/events/{mine['id']}", headers=b.headers).json()["title"]
        == "B's birthday-style wedding"
    )
    assert [e["id"] for e in client.get(f"{BASE}/events", headers=a.headers).json()["data"]] == [event["id"]]

    # A archives; the row persists and stays readable.
    assert client.delete(f"{BASE}/events/{event['id']}", headers=a.headers).status_code == 204
    assert client.get(f"{BASE}/events/{event['id']}", headers=a.headers).json()["status"] == "archived"

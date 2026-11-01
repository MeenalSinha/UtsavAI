"""Event and profile APIs against a real database with real RLS."""

import uuid

from tests.integration.conftest import event_payload

BASE = "/api/v1"


def add_member(admin, event_id, user_id, role, status="active"):
    admin.execute("insert into public.profiles (user_id) values (%s) on conflict do nothing", (user_id,))
    admin.execute(
        "insert into public.event_members (event_id, user_id, role, status) values (%s,%s,%s,%s)",
        (event_id, user_id, role, status),
    )


# ------------------------------------------------------------------ profile
def test_me_provisions_profile_from_verified_jwt_only(client, make_user, admin):
    u = make_user("asha")
    r = client.get(f"{BASE}/me", headers=u.headers)
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == str(u.id) and body["preferred_locale"] == "en-IN"
    assert body["email"] == "asha@example.test"
    assert admin.execute("select count(*) from public.profiles").fetchone()[0] == 1
    assert client.get(f"{BASE}/me", headers=u.headers).status_code == 200  # idempotent
    assert admin.execute("select count(*) from public.profiles").fetchone()[0] == 1


def test_patch_me_updates_only_own_profile(client, make_user, admin):
    a, b = make_user("a"), make_user("b")
    client.get(f"{BASE}/me", headers=b.headers)
    r = client.patch(
        f"{BASE}/me",
        json={"display_name": "Meera", "timezone": "Asia/Kolkata", "preferred_locale": "hi-IN"},
        headers=a.headers,
    )
    assert r.status_code == 200 and r.json()["display_name"] == "Meera"
    b_name = admin.execute("select display_name from public.profiles where user_id=%s", (b.id,)).fetchone()[0]
    assert b_name is None
    bad = client.patch(f"{BASE}/me", json={"user_id": str(b.id), "display_name": "X"}, headers=a.headers)
    assert bad.status_code == 422
    assert client.patch(f"{BASE}/me", json={"timezone": "Nope/Nope"}, headers=a.headers).status_code == 422


# ------------------------------------------------------------------- create
def test_create_event_returns_documented_contract(client, make_user, admin):
    u = make_user("owner")
    r = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers)
    assert r.status_code == 201
    ev = r.json()
    assert set(ev) == {
        "id",
        "event_type",
        "title",
        "start_at",
        "end_at",
        "timezone",
        "location",
        "expected_guest_count",
        "currency",
        "status",
        "revision",
        "created_at",
        "updated_at",
        "archived_at",
        "my_role",
    }
    assert ev["start_at"] == "2027-02-12T04:30:00Z" and ev["end_at"].endswith("Z")
    assert ev["status"] == "draft" and ev["revision"] == 1 and ev["my_role"] == "owner"
    assert ev["location"] == {
        "name": "Test Venue",
        "city": "Jaipur",
        "region": "Rajasthan",
        "country_code": "IN",
    }
    assert r.headers["etag"] == '"1"' and r.headers["location"] == f"/api/v1/events/{ev['id']}"
    members = admin.execute(
        "select user_id, role, status from public.event_members where event_id=%s", (ev["id"],)
    ).fetchall()
    assert members == [(u.id, "owner", "active")]
    owner_col = admin.execute("select owner_user_id from public.events where id=%s", (ev["id"],)).fetchone()[
        0
    ]
    assert owner_col == u.id


def test_create_writes_audit_row_without_pii(client, make_user, admin):
    u = make_user("owner")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    row = admin.execute(
        "select action, actor_user_id, metadata, request_id from public.audit_logs where event_id=%s",
        (ev["id"],),
    ).fetchone()
    assert row[0] == "event.created" and row[1] == u.id
    assert row[2] == {"event_type": "wedding"} and row[3].startswith("req_")


def test_owner_cannot_be_chosen_by_the_client(client, make_user):
    a, b = make_user("a"), make_user("b")
    r = client.post(f"{BASE}/events", json=event_payload(owner_user_id=str(b.id)), headers=a.headers)
    assert r.status_code == 422
    r2 = client.post(f"{BASE}/events", json=event_payload(), headers={**a.headers, "X-User-Id": str(b.id)})
    assert r2.json()["my_role"] == "owner"
    assert client.get(f"{BASE}/events", headers=b.headers).json()["data"] == []


def test_failed_create_leaves_no_partial_rows(client, make_user, admin):
    u = make_user("a")
    bad = client.post(f"{BASE}/events", json=event_payload(timezone="Mars/Phobos"), headers=u.headers)
    assert bad.status_code == 422
    assert admin.execute("select count(*) from public.events").fetchone()[0] == 0
    assert admin.execute("select count(*) from public.event_members").fetchone()[0] == 0


# --------------------------------------------------------------------- read
def test_list_and_get_only_own_events(client, make_user):
    a, b = make_user("a"), make_user("b")
    ea = client.post(f"{BASE}/events", json=event_payload(title="A1"), headers=a.headers).json()
    eb = client.post(f"{BASE}/events", json=event_payload(title="B1"), headers=b.headers).json()
    assert [e["title"] for e in client.get(f"{BASE}/events", headers=a.headers).json()["data"]] == ["A1"]
    assert [e["title"] for e in client.get(f"{BASE}/events", headers=b.headers).json()["data"]] == ["B1"]
    assert client.get(f"{BASE}/events/{ea['id']}", headers=a.headers).status_code == 200
    r = client.get(f"{BASE}/events/{ea['id']}", headers=b.headers)
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
    unknown = client.get(f"{BASE}/events/{uuid.uuid4()}", headers=b.headers)
    assert unknown.json()["error"]["message"] == r.json()["error"]["message"]  # existence not revealed
    assert eb["id"] != ea["id"]


def test_pagination_is_stable_and_complete(client, make_user):
    u = make_user("a")
    created = []
    for i in range(7):
        day = 10 + i
        created.append(
            client.post(
                f"{BASE}/events",
                json=event_payload(
                    title=f"E{i}",
                    start_at=f"2027-03-{day}T10:00:00+05:30",
                    end_at=f"2027-03-{day}T20:00:00+05:30",
                ),
                headers=u.headers,
            ).json()["id"]
        )
    seen, cursor, pages = [], None, 0
    while True:
        params = {"limit": 3, **({"cursor": cursor} if cursor else {})}
        page = client.get(f"{BASE}/events", params=params, headers=u.headers).json()
        seen += [e["id"] for e in page["data"]]
        pages += 1
        cursor = page["next_cursor"]
        if not cursor:
            break
    assert pages == 3 and seen == created  # ordered by start_at ascending, no duplicates or gaps


def test_created_desc_sort_and_bad_cursor(client, make_user):
    u = make_user("a")
    ids = [
        client.post(f"{BASE}/events", json=event_payload(title=f"E{i}"), headers=u.headers).json()["id"]
        for i in range(3)
    ]
    data = client.get(f"{BASE}/events", params={"sort": "created_at"}, headers=u.headers).json()["data"]
    assert [e["id"] for e in data] == ids[::-1]
    assert client.get(f"{BASE}/events", params={"cursor": "garbage!"}, headers=u.headers).status_code == 400
    assert client.get(f"{BASE}/events", params={"limit": 1000}, headers=u.headers).status_code == 422
    assert (
        client.get(
            f"{BASE}/events", params={"sort": "owner_user_id; drop table events"}, headers=u.headers
        ).status_code
        == 422
    )


# ------------------------------------------------------------------- update
def test_update_with_if_match_increments_revision_and_audits(client, make_user, admin):
    u = make_user("a")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    r = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={
            "title": "Renamed",
            "expected_guest_count": 450,
            "status": "planning",
            "location": {"city": "Udaipur"},
        },
        headers={**u.headers, "If-Match": '"1"'},
    )
    assert r.status_code == 200
    out = r.json()
    assert out["revision"] == 2 and r.headers["etag"] == '"2"'
    assert out["title"] == "Renamed" and out["expected_guest_count"] == 450 and out["status"] == "planning"
    assert out["location"]["city"] == "Udaipur" and out["location"]["region"] == "Rajasthan"  # partial merge
    meta = admin.execute("select metadata from public.audit_logs where action='event.updated'").fetchone()[0]
    assert meta == {
        "changed_fields": ["city", "expected_guest_count", "status", "title"],
        "from_revision": 1,
    }


def test_stale_revision_is_409_and_no_change_applied(client, make_user):
    u = make_user("a")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    ok = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={"title": "First"},
        headers={**u.headers, "If-Match": '"1"'},
    )
    assert ok.status_code == 200
    stale = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={"title": "Second"},
        headers={**u.headers, "If-Match": '"1"'},
    )
    assert stale.status_code == 409
    err = stale.json()["error"]
    assert err["code"] == "REVISION_CONFLICT" and err["details"] == {"current_revision": 2}
    assert client.get(f"{BASE}/events/{ev['id']}", headers=u.headers).json()["title"] == "First"


def test_missing_or_malformed_if_match(client, make_user):
    u = make_user("a")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    assert (
        client.patch(f"{BASE}/events/{ev['id']}", json={"title": "x"}, headers=u.headers).status_code == 428
    )
    bad = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={"title": "x"},
        headers={**u.headers, "If-Match": "latest"},
    )
    assert bad.status_code == 400


def test_update_validates_merged_date_range_and_transitions(client, make_user):
    u = make_user("a")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    h = {**u.headers, "If-Match": '"1"'}
    bad_range = client.patch(f"{BASE}/events/{ev['id']}", json={"end_at": "2027-02-01T00:00:00Z"}, headers=h)
    assert (
        bad_range.status_code == 422
        and bad_range.json()["error"]["message"] == "The event date range is invalid."
    )
    illegal = client.patch(f"{BASE}/events/{ev['id']}", json={"status": "completed"}, headers=h)
    assert illegal.status_code == 422 and illegal.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
    assert (
        client.patch(f"{BASE}/events/{ev['id']}", json={"status": "archived"}, headers=h).status_code == 422
    )
    assert (
        client.patch(f"{BASE}/events/{ev['id']}", json={"revision": 50, "title": "x"}, headers=h).status_code
        == 422
    )
    assert client.get(f"{BASE}/events/{ev['id']}", headers=u.headers).json()["revision"] == 1


def test_noop_update_does_not_bump_revision(client, make_user):
    u = make_user("a")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    r = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={"title": ev["title"]},
        headers={**u.headers, "If-Match": '"1"'},
    )
    assert r.status_code == 200 and r.json()["revision"] == 1


def test_unrelated_user_cannot_modify_or_archive(client, make_user):
    a, b = make_user("a"), make_user("b")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=a.headers).json()
    assert (
        client.patch(
            f"{BASE}/events/{ev['id']}",
            json={"title": "hax"},
            headers={**b.headers, "If-Match": '"1"'},
        ).status_code
        == 404
    )
    assert client.delete(f"{BASE}/events/{ev['id']}", headers=b.headers).status_code == 404
    assert (
        client.get(f"{BASE}/events/{ev['id']}", headers=a.headers).json()["title"] == "Synthetic Test Wedding"
    )


# ------------------------------------------------------------------- roles
def test_role_matrix_over_http(client, make_user, admin):
    owner, editor, viewer, stranger = (make_user(n) for n in ("o", "e", "v", "s"))
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=owner.headers).json()
    add_member(admin, ev["id"], editor.id, "editor")
    add_member(admin, ev["id"], viewer.id, "viewer")

    for u in (owner, editor, viewer):
        got = client.get(f"{BASE}/events/{ev['id']}", headers=u.headers)
        assert got.status_code == 200
    assert client.get(f"{BASE}/events/{ev['id']}", headers=editor.headers).json()["my_role"] == "editor"
    assert client.get(f"{BASE}/events/{ev['id']}", headers=stranger.headers).status_code == 404
    assert [e["id"] for e in client.get(f"{BASE}/events", headers=editor.headers).json()["data"]] == [
        ev["id"]
    ]

    viewer_patch = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={"title": "v"},
        headers={**viewer.headers, "If-Match": '"1"'},
    )
    assert viewer_patch.status_code == 403 and viewer_patch.json()["error"]["code"] == "FORBIDDEN"

    editor_patch = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={"title": "edited by editor"},
        headers={**editor.headers, "If-Match": '"1"'},
    )
    assert editor_patch.status_code == 200 and editor_patch.json()["my_role"] == "editor"

    assert client.delete(f"{BASE}/events/{ev['id']}", headers=editor.headers).status_code == 403
    assert client.delete(f"{BASE}/events/{ev['id']}", headers=viewer.headers).status_code == 403
    assert client.delete(f"{BASE}/events/{ev['id']}", headers=owner.headers).status_code == 204


def test_revoked_member_loses_access(client, make_user, admin):
    owner, ex = make_user("o"), make_user("x")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=owner.headers).json()
    add_member(admin, ev["id"], ex.id, "editor", status="revoked")
    assert client.get(f"{BASE}/events/{ev['id']}", headers=ex.headers).status_code == 404


# ------------------------------------------------------------------ archive
def test_archive_is_soft_idempotent_and_hides_from_default_list(client, make_user, admin):
    u = make_user("a")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    assert client.delete(f"{BASE}/events/{ev['id']}", headers=u.headers).status_code == 204
    assert client.delete(f"{BASE}/events/{ev['id']}", headers=u.headers).status_code == 204  # idempotent
    row = admin.execute(
        "select status, archived_at is not null from public.events where id=%s", (ev["id"],)
    ).fetchone()
    assert row == ("archived", True)  # row still exists
    assert client.get(f"{BASE}/events", headers=u.headers).json()["data"] == []
    listed = client.get(f"{BASE}/events", params={"include_archived": "true"}, headers=u.headers).json()[
        "data"
    ]
    assert [e["status"] for e in listed] == ["archived"]
    only = client.get(f"{BASE}/events", params={"status": "archived"}, headers=u.headers).json()["data"]
    assert len(only) == 1
    got = client.get(f"{BASE}/events/{ev['id']}", headers=u.headers)
    assert got.status_code == 200 and got.json()["archived_at"].endswith("Z")
    audits = admin.execute("select count(*) from public.audit_logs where action='event.archived'").fetchone()[
        0
    ]
    assert audits == 1


def test_archived_event_is_read_only_via_api(client, make_user):
    u = make_user("a")
    ev = client.post(f"{BASE}/events", json=event_payload(), headers=u.headers).json()
    client.delete(f"{BASE}/events/{ev['id']}", headers=u.headers)
    current = client.get(f"{BASE}/events/{ev['id']}", headers=u.headers).json()
    r = client.patch(
        f"{BASE}/events/{ev['id']}",
        json={"title": "x"},
        headers={**u.headers, "If-Match": f'"{current["revision"]}"'},
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_database_errors_do_not_leak_details(client, make_user, monkeypatch):
    from app.modules.events import repository

    u = make_user("a")

    def boom(*a, **k):
        raise RuntimeError("SELECT secret FROM somewhere postgres://user:pw@host")

    monkeypatch.setattr(repository, "list_events", boom)
    r = client.get(f"{BASE}/events", headers=u.headers)
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "postgres://" not in r.text and "secret" not in r.text.lower()

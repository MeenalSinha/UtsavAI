"""P1-14: the transaction-local identity context must never leak between pooled users.

The pool is capped at ONE connection (see db_settings), so every request below
is guaranteed to reuse the same backend PostgreSQL session.
"""

import pytest

from app.modules.events import repository
from tests.integration.conftest import event_payload

BASE = "/api/v1"


def backend_pid_and_identity(db, user_id):
    with db.transaction(user_id, "test") as conn:
        row = conn.execute(
            "select pg_backend_pid() as pid, nullif(current_setting('app.user_id', true), '') as uid"
        ).fetchone()
    return row["pid"], row["uid"]


def test_identity_is_cleared_after_commit(database, make_user):
    a = make_user("a")
    pid_a, uid_a = backend_pid_and_identity(database, a.id)
    pid_none, uid_none = backend_pid_and_identity(database, None)
    assert uid_a == str(a.id)
    assert pid_a == pid_none, "pool must reuse the same session for this test to be meaningful"
    assert uid_none is None


def test_identity_is_cleared_after_rollback_on_exception(database, make_user):
    a = make_user("a")
    with pytest.raises(RuntimeError), database.transaction(a.id, "t") as conn:
        conn.execute("select 1")
        raise RuntimeError("boom")
    with database.pool.connection() as conn:  # raw checkout, no identity applied
        leaked = conn.execute("select nullif(current_setting('app.user_id', true), '') as v").fetchone()["v"]
    assert leaked is None


def test_identity_is_cleared_after_database_error(database, make_user):
    a = make_user("a")
    with pytest.raises(Exception), database.transaction(a.id, "t") as conn:  # noqa: B017, PT011
        conn.execute("select * from public.does_not_exist")
    pid, uid = backend_pid_and_identity(database, None)
    assert uid is None and pid


def test_user_b_cannot_see_user_a_event_on_reused_connection(database, make_user, client):
    a, b = make_user("a"), make_user("b")
    created = client.post(f"{BASE}/events", json=event_payload(), headers=a.headers)
    assert created.status_code == 201
    event_id = created.json()["id"]

    pids = set()
    with database.transaction(a.id, "ra") as conn:
        pids.add(conn.execute("select pg_backend_pid() p").fetchone()["p"])
        assert repository.get_event(conn, event_id) is not None
    with database.transaction(b.id, "rb") as conn:
        pids.add(conn.execute("select pg_backend_pid() p").fetchone()["p"])
        assert repository.get_event(conn, event_id) is None
        assert conn.execute("select count(*) c from public.events").fetchone()["c"] == 0
    with database.transaction(None, "anon") as conn:
        assert conn.execute("select count(*) c from public.events").fetchone()["c"] == 0
    assert len(pids) == 1, "all three transactions must have shared one backend session"


def test_http_requests_alternating_users_never_cross(client, make_user):
    a, b = make_user("a"), make_user("b")
    ev_a = client.post(f"{BASE}/events", json=event_payload(title="A's event"), headers=a.headers).json()
    for _ in range(5):
        assert client.get(f"{BASE}/events/{ev_a['id']}", headers=a.headers).status_code == 200
        assert client.get(f"{BASE}/events/{ev_a['id']}", headers=b.headers).status_code == 404
        assert client.get(f"{BASE}/events", headers=b.headers).json()["data"] == []
    # failed (rejected) request by B must not poison the next request by A
    client.patch(f"{BASE}/events/{ev_a['id']}", json={"title": "x"}, headers={**b.headers, "If-Match": '"1"'})
    assert client.get(f"{BASE}/events/{ev_a['id']}", headers=a.headers).json()["title"] == "A's event"


def test_reset_callback_clears_session_level_settings(database):
    with database.pool.connection() as conn:
        pid = conn.execute("select pg_backend_pid() p").fetchone()["p"]
        conn.execute("select set_config('app.user_id', 'session-level-leak', false)")
        conn.commit()
    with database.pool.connection() as conn:
        row = conn.execute(
            "select pg_backend_pid() p, nullif(current_setting('app.user_id', true), '') v"
        ).fetchone()
    assert row["p"] == pid and row["v"] is None


def test_readiness_verifies_database_and_role(client):
    r = client.get(f"{BASE}/health/ready")
    assert r.status_code == 200 and r.json() == {"status": "ready", "database": "ok"}

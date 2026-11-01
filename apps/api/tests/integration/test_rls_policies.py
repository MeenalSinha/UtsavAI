"""Row-level security evaluated as the real runtime role (NOBYPASSRLS)."""

import os

import psycopg
import pytest

from tests.conftest import RUNTIME_URL_DEFAULT
from tests.integration.test_schema_and_constraints import make_event, new_user

RUNTIME_URL = os.environ.get("TEST_DATABASE_URL", RUNTIME_URL_DEFAULT)


@pytest.fixture
def rt():
    """Fresh runtime connection (no pool) per test."""
    with psycopg.connect(RUNTIME_URL) as conn:
        yield conn


def as_user(conn, user_id):
    conn.execute("select set_config('app.user_id', %s, true)", (str(user_id) if user_id else "",))


def test_connected_as_non_privileged_role(rt):
    row = rt.execute(
        "select current_user, rolsuper, rolbypassrls from pg_roles where rolname = current_user"
    ).fetchone()
    assert row == ("utsavai_app", False, False)


def test_no_identity_means_no_rows(admin, rt):
    owner = new_user(admin)
    make_event(admin, owner)
    assert rt.execute("select count(*) from public.events").fetchone()[0] == 0
    assert rt.execute("select count(*) from public.profiles").fetchone()[0] == 0
    assert rt.execute("select count(*) from public.event_members").fetchone()[0] == 0


def test_unrelated_user_cannot_see_event_or_membership(admin, rt):
    a, b = new_user(admin), new_user(admin)
    eid = make_event(admin, a)
    as_user(rt, b)
    assert rt.execute("select count(*) from public.events where id=%s", (eid,)).fetchone()[0] == 0
    assert rt.execute("select count(*) from public.event_members").fetchone()[0] == 0
    assert rt.execute("select count(*) from public.profiles").fetchone()[0] == 1  # only own (b)
    rt.rollback()
    as_user(rt, a)
    assert rt.execute("select count(*) from public.events where id=%s", (eid,)).fetchone()[0] == 1


def test_unrelated_user_cannot_update_event(admin, rt):
    a, b = new_user(admin), new_user(admin)
    eid = make_event(admin, a)
    as_user(rt, b)
    cur = rt.execute("update public.events set title = 'hacked' where id = %s", (eid,))
    assert cur.rowcount == 0
    rt.rollback()
    assert admin.execute("select title from public.events where id=%s", (eid,)).fetchone()[0] == "T"


def test_cannot_insert_event_owned_by_someone_else(admin, rt):
    a, b = new_user(admin), new_user(admin)
    as_user(rt, b)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute(
            "insert into public.events (owner_user_id, event_type, title, start_at, end_at, timezone) "
            "values (%s, 'wedding', 'T', now(), now(), 'Asia/Kolkata')",
            (a,),
        )


def test_cannot_grant_self_membership_to_foreign_event(admin, rt):
    a, b = new_user(admin), new_user(admin)
    eid = make_event(admin, a)
    as_user(rt, b)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute(
            "insert into public.event_members (event_id, user_id, role) values (%s, %s, 'viewer')",
            (eid, b),
        )
    rt.rollback()
    as_user(rt, b)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute(
            "insert into public.event_members (event_id, user_id, role) values (%s, %s, 'owner')",
            (eid, b),
        )


def test_cannot_write_profile_of_another_user(admin, rt):
    a, b = new_user(admin), new_user(admin)
    as_user(rt, b)
    assert rt.execute("update public.profiles set display_name='x' where user_id=%s", (a,)).rowcount == 0
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("insert into public.profiles (user_id) values (gen_random_uuid())")


def grant_role(admin, event_id, user_id, role):
    admin.execute(
        "insert into public.event_members (event_id, user_id, role, status) values (%s, %s, %s, 'active')",
        (event_id, user_id, role),
    )


def test_viewer_reads_but_cannot_modify(admin, rt):
    a, v = new_user(admin), new_user(admin)
    eid = make_event(admin, a)
    grant_role(admin, eid, v, "viewer")
    as_user(rt, v)
    assert rt.execute("select count(*) from public.events where id=%s", (eid,)).fetchone()[0] == 1
    assert rt.execute("update public.events set title='x' where id=%s", (eid,)).rowcount == 0


def test_editor_can_update_but_not_archive(admin, rt):
    a, e = new_user(admin), new_user(admin)
    eid = make_event(admin, a)
    grant_role(admin, eid, e, "editor")
    as_user(rt, e)
    assert rt.execute("update public.events set title='edited' where id=%s", (eid,)).rowcount == 1
    rt.commit()
    as_user(rt, e)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("update public.events set status='archived' where id=%s", (eid,))


def test_revoked_and_invited_members_have_no_access(admin, rt):
    a, r, i = new_user(admin), new_user(admin), new_user(admin)
    eid = make_event(admin, a)
    admin.execute(
        "insert into public.event_members (event_id, user_id, role, status) values (%s,%s,'editor','revoked')",
        (eid, r),
    )
    admin.execute(
        "insert into public.event_members (event_id, user_id, role, status) values (%s,%s,'viewer','invited')",
        (eid, i),
    )
    for uid in (r, i):
        as_user(rt, uid)
        assert rt.execute("select count(*) from public.events where id=%s", (eid,)).fetchone()[0] == 0
        rt.rollback()


def test_owner_archives_and_archived_event_is_readable_but_frozen(admin, rt):
    a = new_user(admin)
    eid = make_event(admin, a)
    as_user(rt, a)
    rt.execute("update public.events set status='archived' where id=%s", (eid,))
    rt.commit()
    row = admin.execute(
        "select status, archived_at is not null, revision from public.events where id=%s", (eid,)
    ).fetchone()
    assert row == ("archived", True, 2)
    as_user(rt, a)
    assert rt.execute("select count(*) from public.events where id=%s", (eid,)).fetchone()[0] == 1
    with pytest.raises(psycopg.errors.CheckViolation, match="read-only"):
        rt.execute("update public.events set title='nope' where id=%s", (eid,))


def test_runtime_role_cannot_delete_or_truncate(admin, rt):
    a = new_user(admin)
    make_event(admin, a)
    as_user(rt, a)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("delete from public.events")
    rt.rollback()
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("truncate public.events")


def test_cannot_set_revision_or_owner_directly(admin, rt):
    a = new_user(admin)
    eid = make_event(admin, a)
    as_user(rt, a)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("update public.events set revision = 500 where id=%s", (eid,))
    rt.rollback()
    as_user(rt, a)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("update public.events set owner_user_id = gen_random_uuid() where id=%s", (eid,))


def test_audit_log_is_append_only_and_owner_readable(admin, rt):
    a, v = new_user(admin), new_user(admin)
    eid = make_event(admin, a)
    grant_role(admin, eid, v, "viewer")
    as_user(rt, a)
    rt.execute(
        "insert into public.audit_logs (event_id, actor_user_id, actor_type, action, entity_type) "
        "values (%s, %s, 'user', 'event.updated', 'event')",
        (eid, a),
    )
    assert rt.execute("select count(*) from public.audit_logs").fetchone()[0] == 1
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("update public.audit_logs set action='x'")
    rt.rollback()
    as_user(rt, a)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute("delete from public.audit_logs")
    rt.rollback()
    as_user(rt, a)  # forging someone else's authorship is rejected
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        rt.execute(
            "insert into public.audit_logs (event_id, actor_user_id, actor_type, action, entity_type) "
            "values (%s, %s, 'user', 'x', 'event')",
            (eid, v),
        )


def test_invalid_identity_value_fails_closed(admin, rt):
    rt.execute("select set_config('app.user_id', 'not-a-uuid', true)")
    with pytest.raises(psycopg.errors.InvalidTextRepresentation):
        rt.execute("select count(*) from public.events")

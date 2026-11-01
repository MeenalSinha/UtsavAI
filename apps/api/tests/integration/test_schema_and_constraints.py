"""Migrations, constraints, triggers and grants, verified against a real database."""

import uuid

import psycopg
import pytest


def seed_profile(admin, user_id):
    admin.execute("insert into public.profiles (user_id) values (%s) on conflict do nothing", (user_id,))


def new_user(admin):
    uid = uuid.uuid4()
    admin.execute("insert into auth.users (id, email) values (%s, %s)", (uid, f"{uid.hex[:8]}@example.test"))
    seed_profile(admin, uid)
    return uid


EVENT_SQL = (
    "insert into public.events (owner_user_id, event_type, title, start_at, end_at, timezone) "
    "values (%s, 'wedding', 'T', '2027-01-01T10:00Z', '2027-01-02T10:00Z', 'Asia/Kolkata') returning id"
)


def make_event(admin, owner):
    """Create event + owner membership in one transaction, as the application does."""
    with admin.transaction():
        eid = admin.execute(EVENT_SQL, (owner,)).fetchone()[0]
        admin.execute(
            "insert into public.event_members (event_id, user_id, role) values (%s, %s, 'owner')",
            (eid, owner),
        )
    return eid


def test_expected_tables_exist_with_rls_enabled(admin):
    rows = admin.execute(
        "select relname, relrowsecurity from pg_class c join pg_namespace n on n.oid = c.relnamespace "
        "where n.nspname = 'public' and relkind = 'r' order by relname"
    ).fetchall()
    assert dict(rows) == {
        "ai_conversations": True,
        "ai_messages": True,
        "ai_proposals": True,
        "audit_logs": True,
        "event_functions": True,
        "event_members": True,
        "event_preferences": True,
        "events": True,
        "profiles": True,
        "task_dependencies": True,
        "tasks": True,
    }


def test_runtime_role_is_least_privileged(admin):
    row = admin.execute(
        "select rolsuper, rolbypassrls, rolcreatedb, rolcreaterole from pg_roles where rolname = 'utsavai_app'"
    ).fetchone()
    assert row == (False, False, False, False)


def test_runtime_role_cannot_delete_or_ddl(admin):
    privs = admin.execute(
        "select table_name, privilege_type from information_schema.role_table_grants "
        "where grantee = 'utsavai_app' and table_schema = 'public'"
    ).fetchall()
    granted = {(t, p) for t, p in privs}
    assert not any(p in {"DELETE", "TRUNCATE", "REFERENCES", "TRIGGER"} for _, p in granted)
    assert ("audit_logs", "UPDATE") not in granted  # append-only
    create = admin.execute("select has_schema_privilege('utsavai_app', 'public', 'CREATE')").fetchone()[0]
    assert create is False


def test_data_api_roles_have_no_access(admin):
    for role in ("anon", "authenticated"):
        for table in ("profiles", "events", "event_members", "audit_logs"):
            ok = admin.execute(
                "select has_table_privilege(%s, %s, 'SELECT')", (role, f"public.{table}")
            ).fetchone()[0]
            assert ok is False, (role, table)


def test_runtime_role_cannot_update_protected_columns(admin):
    for col in ("revision", "owner_user_id", "archived_at", "id", "created_at", "event_type"):
        ok = admin.execute(
            "select has_column_privilege('utsavai_app', 'public.events', %s, 'UPDATE')", (col,)
        ).fetchone()[0]
        assert ok is False, col


def test_event_defaults_revision_one_status_draft_uuid_pk(admin):
    owner = new_user(admin)
    eid = make_event(admin, owner)
    row = admin.execute(
        "select revision, status, currency, expected_guest_count, archived_at from public.events where id=%s",
        (eid,),
    ).fetchone()
    assert row == (1, "draft", "INR", 0, None)
    assert isinstance(eid, uuid.UUID)


def test_event_without_owner_membership_cannot_commit(admin):
    owner = new_user(admin)
    with (
        pytest.raises(psycopg.errors.CheckViolation, match="no active owner membership"),
        admin.transaction(),
    ):
        admin.execute(EVENT_SQL, (owner,))


def test_only_one_active_owner_per_event(admin):
    owner, other = new_user(admin), new_user(admin)
    eid = make_event(admin, owner)
    with pytest.raises(psycopg.errors.UniqueViolation):
        admin.execute(
            "insert into public.event_members (event_id, user_id, role) values (%s, %s, 'owner')",
            (eid, other),
        )


@pytest.mark.parametrize(
    "fragment",
    [
        "expected_guest_count = -1",
        "end_at = '2026-12-31T10:00Z'",
        "currency = 'inr'",
        "country_code = 'IND'",
        "status = 'bogus'",
        "title = '   '",
        "event_type = 'Bad Type'",
    ],
)
def test_check_constraints_reject_invalid_rows(admin, fragment):
    owner = new_user(admin)
    eid = make_event(admin, owner)
    with pytest.raises((psycopg.errors.CheckViolation, psycopg.errors.DataError)):
        admin.execute(f"update public.events set {fragment} where id = %s", (eid,))  # noqa: S608


def test_invalid_timezone_rejected_by_database(admin):
    owner = new_user(admin)
    with pytest.raises(psycopg.errors.InvalidParameterValue), admin.transaction():
        admin.execute(
            "insert into public.events (owner_user_id, event_type, title, start_at, end_at, timezone) "
            "values (%s, 'wedding', 'T', now(), now(), 'Mars/Phobos')",
            (owner,),
        )


def test_event_type_is_not_a_postgres_enum(admin):
    n = admin.execute(
        "select count(*) from pg_type where typtype = 'e' and typnamespace = 'public'::regnamespace"
    ).fetchone()[0]
    assert n == 0


def test_foreign_keys(admin):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        admin.execute("insert into public.profiles (user_id) values (gen_random_uuid())")
    owner = new_user(admin)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        admin.execute(
            "insert into public.event_members (event_id, user_id, role) values (gen_random_uuid(), %s, 'viewer')",
            (owner,),
        )
    eid = make_event(admin, owner)
    with pytest.raises(psycopg.errors.ForeignKeyViolation):  # owner profile cannot vanish under an event
        admin.execute("delete from public.profiles where user_id = %s", (owner,))
    assert eid


def test_membership_cascades_when_event_removed(admin):
    owner = new_user(admin)
    eid = make_event(admin, owner)
    admin.execute("delete from public.events where id = %s", (eid,))
    assert (
        admin.execute("select count(*) from public.event_members where event_id=%s", (eid,)).fetchone()[0]
        == 0
    )


def test_revision_increments_automatically_and_updated_at_moves(admin):
    owner = new_user(admin)
    eid = make_event(admin, owner)
    before = admin.execute("select updated_at from public.events where id=%s", (eid,)).fetchone()[0]
    admin.execute("update public.events set title = 'Renamed' where id = %s", (eid,))
    admin.execute("update public.events set title = 'Renamed again' where id = %s", (eid,))
    rev, after = admin.execute(
        "select revision, updated_at from public.events where id=%s", (eid,)
    ).fetchone()
    assert rev == 3 and after >= before


def test_revision_cannot_be_forced_even_by_privileged_sql(admin):
    owner = new_user(admin)
    eid = make_event(admin, owner)
    admin.execute("update public.events set title = 'x', revision = 999 where id = %s", (eid,))
    assert admin.execute("select revision from public.events where id=%s", (eid,)).fetchone()[0] == 2

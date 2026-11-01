-- Migration 6: row-level security, explicit least-privilege grants.
--
-- Authorization model (docs/SECURITY.md section 4.2):
--   * FastAPI verifies the Supabase JWT and sets the transaction-local setting
--     app.user_id. All policies key off app.current_user_id().
--   * The runtime role (utsavai_app) is NOBYPASSRLS and owns nothing.
--   * Policy recursion is avoided by design: event_members is readable only for
--     the caller's own rows, and events policies read event_members. Listing
--     other members of an event (owner view) is added with the collaboration
--     feature and will use a dedicated non-recursive mechanism.
--   * No privilege-elevating (definer-rights) functions are introduced in Phase 1.

alter table public.profiles       enable row level security;
alter table public.events         enable row level security;
alter table public.event_members  enable row level security;
alter table public.audit_logs     enable row level security;

-- ---------------------------------------------------------------- grants
-- Supabase auto-grants new tables to the Data API roles. The browser must never
-- reach these tables directly, so revoke explicitly (guarded for plain Postgres).
do $$
declare
  r text;
begin
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on public.profiles, public.events, public.event_members, public.audit_logs from %I', r);
      execute format('revoke all on schema app from %I', r);
    end if;
  end loop;
end
$$;

revoke all on public.profiles, public.events, public.event_members, public.audit_logs from public;

grant select on public.profiles to utsavai_app;
grant insert (user_id, display_name, preferred_locale, timezone) on public.profiles to utsavai_app;
grant update (display_name, preferred_locale, timezone) on public.profiles to utsavai_app;

grant select on public.events to utsavai_app;
grant insert (
  owner_user_id, event_type, title, start_at, end_at, timezone,
  location_name, city, region, country_code, expected_guest_count, currency
) on public.events to utsavai_app;
-- revision, updated_at, archived_at, owner_user_id and event_type are intentionally NOT updatable.
grant update (
  title, start_at, end_at, timezone, location_name, city, region,
  country_code, expected_guest_count, currency, status
) on public.events to utsavai_app;

grant select, insert on public.event_members to utsavai_app;

-- Append-only: no UPDATE or DELETE grant for the application role.
grant select, insert on public.audit_logs to utsavai_app;

-- ---------------------------------------------------------------- profiles
create policy profiles_select_own on public.profiles
  for select to utsavai_app
  using (user_id = app.current_user_id());

create policy profiles_insert_own on public.profiles
  for insert to utsavai_app
  with check (user_id = app.current_user_id());

create policy profiles_update_own on public.profiles
  for update to utsavai_app
  using (user_id = app.current_user_id())
  with check (user_id = app.current_user_id());

-- ---------------------------------------------------------------- event_members
create policy event_members_select_own on public.event_members
  for select to utsavai_app
  using (user_id = app.current_user_id());

-- Phase 1 only allows the creator to add their own owner membership for an
-- event they own. Inviting collaborators is a later phase.
create policy event_members_insert_owner on public.event_members
  for insert to utsavai_app
  with check (
    user_id = app.current_user_id()
    and role = 'owner'
    and status = 'active'
    and exists (
      select 1 from public.events e
       where e.id = event_members.event_id
         and e.owner_user_id = app.current_user_id()
    )
  );

-- ---------------------------------------------------------------- events
create policy events_select_member on public.events
  for select to utsavai_app
  using (
    owner_user_id = app.current_user_id()
    or exists (
      select 1 from public.event_members m
       where m.event_id = events.id
         and m.user_id = app.current_user_id()
         and m.status = 'active'
    )
  );

create policy events_insert_self_owned on public.events
  for insert to utsavai_app
  with check (owner_user_id = app.current_user_id());

create policy events_update_owner_editor on public.events
  for update to utsavai_app
  using (
    owner_user_id = app.current_user_id()
    or exists (
      select 1 from public.event_members m
       where m.event_id = events.id
         and m.user_id = app.current_user_id()
         and m.status = 'active'
         and m.role in ('owner', 'editor')
    )
  )
  with check (
    owner_user_id = app.current_user_id()
    or exists (
      select 1 from public.event_members m
       where m.event_id = events.id
         and m.user_id = app.current_user_id()
         and m.status = 'active'
         and m.role in ('owner', 'editor')
    )
  );
-- No DELETE policy and no DELETE grant: events are archived, never hard-deleted by the app.

-- ---------------------------------------------------------------- audit_logs
create policy audit_logs_insert_actor on public.audit_logs
  for insert to utsavai_app
  with check (
    actor_type = 'user'
    and actor_user_id = app.current_user_id()
    and exists (select 1 from public.events e where e.id = audit_logs.event_id)
  );

create policy audit_logs_select_owner on public.audit_logs
  for select to utsavai_app
  using (
    exists (
      select 1 from public.event_members m
       where m.event_id = audit_logs.event_id
         and m.user_id = app.current_user_id()
         and m.status = 'active'
         and m.role = 'owner'
    )
  );

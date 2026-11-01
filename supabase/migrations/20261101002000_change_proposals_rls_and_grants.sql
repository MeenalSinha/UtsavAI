-- Migration 20: Phase 6 RLS policies and grants for change_proposals table.

alter table public.change_proposals enable row level security;

-- Revoke all permissions from anon, authenticated, and public
do $$
declare
  r text;
  tbls text[] := array['change_proposals'];
  t text;
begin
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      foreach t in array tbls loop
        execute format('revoke all on public.%I from %I', t, r);
      end loop;
    end if;
  end loop;
  foreach t in array tbls loop
    execute format('revoke all on public.%I from public', t);
  end loop;
end
$$;

-- Explicit grants for runtime role utsavai_app (strictly zero DELETE grants)
grant select, insert, update on public.change_proposals to utsavai_app;

-- ---------------------------------------------------------------- change_proposals RLS
-- Members can view change proposals for events they belong to
create policy change_proposals_select on public.change_proposals
  for select to utsavai_app
  using (app.is_event_member(event_id));

-- Owners and editors can create change proposals
create policy change_proposals_insert on public.change_proposals
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- Owners and editors can update proposals (e.g. status transition, owner acceptance)
create policy change_proposals_update on public.change_proposals
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

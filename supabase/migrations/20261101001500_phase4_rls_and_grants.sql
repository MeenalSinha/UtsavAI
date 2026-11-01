-- Migration 15: Phase 4 RLS policies and grants for event_vendors and vendor_quotes.

alter table public.event_vendors enable row level security;
alter table public.vendor_quotes  enable row level security;

-- Revoke all permissions from anon, authenticated, and public
do $$
declare
  r text;
  tbls text[] := array['event_vendors', 'vendor_quotes'];
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

-- Explicit grants for the application runtime role utsavai_app (strictly no DELETE)
grant select, insert, update on public.event_vendors to utsavai_app;
grant select, insert, update on public.vendor_quotes to utsavai_app;

-- ---------------------------------------------------------------- event_vendors
create policy event_vendors_select on public.event_vendors
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy event_vendors_insert on public.event_vendors
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

create policy event_vendors_update on public.event_vendors
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- vendor_quotes
create policy vendor_quotes_select on public.vendor_quotes
  for select to utsavai_app
  using (exists (
    select 1 from public.event_vendors v
     where v.id = vendor_quotes.vendor_id
       and app.is_event_member(v.event_id)
  ));

create policy vendor_quotes_insert on public.vendor_quotes
  for insert to utsavai_app
  with check (exists (
    select 1 from public.event_vendors v
     where v.id = vendor_quotes.vendor_id
       and app.is_event_member(v.event_id, array['owner', 'editor'])
       and v.archived_at is null
  ));

create policy vendor_quotes_update on public.vendor_quotes
  for update to utsavai_app
  using (exists (
    select 1 from public.event_vendors v
     where v.id = vendor_quotes.vendor_id
       and app.is_event_member(v.event_id, array['owner', 'editor'])
  ))
  with check (exists (
    select 1 from public.event_vendors v
     where v.id = vendor_quotes.vendor_id
       and app.is_event_member(v.event_id, array['owner', 'editor'])
  ));

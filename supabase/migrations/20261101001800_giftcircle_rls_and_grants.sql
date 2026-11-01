-- Migration 18: Phase 5 RLS policies and grants for GiftCircle tables.

alter table public.gift_registries    enable row level security;
alter table public.gift_items         enable row level security;
alter table public.gift_reservations  enable row level security;
alter table public.gift_contributions enable row level security;
alter table public.idempotency_records enable row level security;

-- Revoke all permissions from anon, authenticated, and public
do $$
declare
  r text;
  tbls text[] := array['gift_registries', 'gift_items', 'gift_reservations', 'gift_contributions', 'idempotency_records'];
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
grant select, insert, update on public.gift_registries to utsavai_app;
grant select, insert, update on public.gift_items to utsavai_app;
grant select, insert, update on public.gift_reservations to utsavai_app;
grant select, insert, update on public.gift_contributions to utsavai_app;
grant select, insert, update on public.idempotency_records to utsavai_app;

-- ---------------------------------------------------------------- gift_registries
create policy gift_registries_select on public.gift_registries
  for select to utsavai_app
  using (
    app.is_event_member(event_id)
    or (
      is_public = true
      and revoked_at is null
      and (expires_at is null or expires_at > pg_catalog.now())
      and share_token_hash is not null
      and share_token_hash = app.current_share_token_hash()
    )
  );

create policy gift_registries_insert on public.gift_registries
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

create policy gift_registries_update on public.gift_registries
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- gift_items
create policy gift_items_select on public.gift_items
  for select to utsavai_app
  using (exists (
    select 1 from public.gift_registries r
     where r.id = gift_items.registry_id
       and (
         app.is_event_member(r.event_id)
         or (
           r.is_public = true
           and r.revoked_at is null
           and (r.expires_at is null or r.expires_at > pg_catalog.now())
           and r.share_token_hash is not null
           and r.share_token_hash = app.current_share_token_hash()
           and gift_items.is_active = true
         )
       )
  ));

create policy gift_items_insert on public.gift_items
  for insert to utsavai_app
  with check (exists (
    select 1 from public.gift_registries r
     where r.id = gift_items.registry_id
       and app.is_event_member(r.event_id, array['owner', 'editor'])
  ));

create policy gift_items_update on public.gift_items
  for update to utsavai_app
  using (exists (
    select 1 from public.gift_registries r
     where r.id = gift_items.registry_id
       and app.is_event_member(r.event_id, array['owner', 'editor'])
  ))
  with check (exists (
    select 1 from public.gift_registries r
     where r.id = gift_items.registry_id
       and app.is_event_member(r.event_id, array['owner', 'editor'])
  ));

-- ---------------------------------------------------------------- gift_reservations
create policy gift_reservations_select on public.gift_reservations
  for select to utsavai_app
  using (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_reservations.gift_item_id
       and (
         app.is_event_member(r.event_id)
         or (
           r.is_public = true
           and r.revoked_at is null
           and (r.expires_at is null or r.expires_at > pg_catalog.now())
           and r.share_token_hash is not null
           and r.share_token_hash = app.current_share_token_hash()
         )
       )
  ));

create policy gift_reservations_insert on public.gift_reservations
  for insert to utsavai_app
  with check (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_reservations.gift_item_id
       and (
         app.is_event_member(r.event_id, array['owner', 'editor'])
         or (
           r.is_public = true
           and r.revoked_at is null
           and (r.expires_at is null or r.expires_at > pg_catalog.now())
           and r.share_token_hash is not null
           and r.share_token_hash = app.current_share_token_hash()
           and i.is_active = true
           and i.gift_mode = 'individual'
         )
       )
  ));

create policy gift_reservations_update on public.gift_reservations
  for update to utsavai_app
  using (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_reservations.gift_item_id
       and (
         app.is_event_member(r.event_id, array['owner', 'editor'])
         or (
           r.is_public = true
           and r.revoked_at is null
           and (r.expires_at is null or r.expires_at > pg_catalog.now())
           and r.share_token_hash is not null
           and r.share_token_hash = app.current_share_token_hash()
         )
       )
  ))
  with check (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_reservations.gift_item_id
       and (
         app.is_event_member(r.event_id, array['owner', 'editor'])
         or (
           r.is_public = true
           and r.revoked_at is null
           and (r.expires_at is null or r.expires_at > pg_catalog.now())
           and r.share_token_hash is not null
           and r.share_token_hash = app.current_share_token_hash()
         )
       )
  ));

-- ---------------------------------------------------------------- gift_contributions
create policy gift_contributions_select on public.gift_contributions
  for select to utsavai_app
  using (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_contributions.gift_item_id
       and (
         app.is_event_member(r.event_id)
         or (
           r.is_public = true
           and r.revoked_at is null
           and (r.expires_at is null or r.expires_at > pg_catalog.now())
           and r.share_token_hash is not null
           and r.share_token_hash = app.current_share_token_hash()
         )
       )
  ));

create policy gift_contributions_insert on public.gift_contributions
  for insert to utsavai_app
  with check (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_contributions.gift_item_id
       and (
         app.is_event_member(r.event_id, array['owner', 'editor'])
         or (
           r.is_public = true
           and r.revoked_at is null
           and (r.expires_at is null or r.expires_at > pg_catalog.now())
           and r.share_token_hash is not null
           and r.share_token_hash = app.current_share_token_hash()
           and i.is_active = true
           and i.gift_mode = 'group'
           and r.allow_group_gifting = true
         )
       )
  ));

create policy gift_contributions_update on public.gift_contributions
  for update to utsavai_app
  using (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_contributions.gift_item_id
       and app.is_event_member(r.event_id, array['owner', 'editor'])
  ))
  with check (exists (
    select 1 from public.gift_items i
      join public.gift_registries r on r.id = i.registry_id
     where i.id = gift_contributions.gift_item_id
       and app.is_event_member(r.event_id, array['owner', 'editor'])
  ));

-- ---------------------------------------------------------------- idempotency_records
create policy idempotency_records_select on public.idempotency_records
  for select to utsavai_app using (true);

create policy idempotency_records_insert on public.idempotency_records
  for insert to utsavai_app with check (true);

create policy idempotency_records_update on public.idempotency_records
  for update to utsavai_app using (true) with check (true);

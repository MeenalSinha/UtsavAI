-- Migration 3: events. Exact shape per docs/DATABASE_SCHEMA.md section 3.2.
-- event_type is varchar + format check (NOT a PostgreSQL enum) so categories stay extensible.

create table public.events (
  id                   uuid primary key default gen_random_uuid(),
  owner_user_id        uuid not null references public.profiles (user_id) on delete restrict,
  event_type           varchar(40) not null check (event_type ~ '^[a-z][a-z0-9_]{1,39}$'),
  title                varchar(160) not null check (char_length(btrim(title)) >= 1),
  start_at             timestamptz not null,
  end_at               timestamptz not null,
  timezone             varchar(64) not null,
  location_name        varchar(160),
  city                 text check (city is null or char_length(city) <= 120),
  region               text check (region is null or char_length(region) <= 120),
  country_code         char(2) check (country_code is null or country_code ~ '^[A-Z]{2}$'),
  expected_guest_count integer not null default 0 check (expected_guest_count >= 0),
  currency             char(3) not null default 'INR' check (currency ~ '^[A-Z]{3}$'),
  status               text not null default 'draft' check (status in ('draft', 'planning', 'completed', 'archived')),
  revision             bigint not null default 1 check (revision >= 1),
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now(),
  archived_at          timestamptz,
  constraint events_date_range check (end_at >= start_at),
  constraint events_archive_consistency check ((status = 'archived') = (archived_at is not null))
);

comment on table public.events is 'Canonical event context. owner_user_id is canonical; event_members mirrors it.';

create index events_owner_status_idx on public.events (owner_user_id, status);
create index events_status_start_idx on public.events (status, start_at);
create index events_created_idx on public.events (created_at desc, id desc);

create trigger events_validate_timezone
  before insert or update of timezone on public.events
  for each row execute function app.validate_timezone();

-- Revision, updated_at and archive rules are enforced in the database so that
-- no application path can bypass them. The runtime role has no UPDATE grant on
-- revision, archived_at or owner_user_id; this trigger maintains them.
create or replace function app.events_before_update()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if old.status = 'archived' then
    raise exception 'archived events are read-only' using errcode = '23514';
  end if;

  if new.status = 'archived' then
    if old.owner_user_id is distinct from app.current_user_id() then
      raise exception 'only the owner may archive an event' using errcode = '42501';
    end if;
    new.archived_at := pg_catalog.now();
  end if;

  new.revision := old.revision + 1;
  new.updated_at := pg_catalog.now();
  return new;
end
$$;

create trigger events_before_update
  before update on public.events
  for each row execute function app.events_before_update();

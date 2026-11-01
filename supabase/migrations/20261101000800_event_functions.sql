-- Migration 8: event_functions. Exact shape per docs/DATABASE_SCHEMA.md section 3.5.

create table public.event_functions (
  id            uuid primary key default gen_random_uuid(),
  event_id      uuid not null references public.events (id) on delete cascade,
  name          varchar(120) not null check (char_length(btrim(name)) >= 1),
  starts_at     timestamptz,
  ends_at       timestamptz,
  location_name text check (location_name is null or char_length(location_name) <= 240),
  notes         text check (notes is null or char_length(notes) <= 4000),
  sort_order    integer not null default 0,
  is_deleted    boolean not null default false,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  constraint event_functions_time_range check (
    ends_at is null or starts_at is null or ends_at >= starts_at
  )
);

comment on table public.event_functions is 'Functions/ceremonies associated with an event.';

create index event_functions_event_sort_idx on public.event_functions (event_id, sort_order, created_at);
create index event_functions_event_starts_idx on public.event_functions (event_id, starts_at);

create or replace function app.functions_touch_event()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  target_id uuid;
begin
  if (tg_op = 'DELETE') then
    target_id := old.event_id;
  else
    new.updated_at := pg_catalog.now();
    target_id := new.event_id;
  end if;

  update public.events
     set title = title
   where id = target_id
     and status <> 'archived';

  if (tg_op = 'DELETE') then
    return old;
  else
    return new;
  end if;
end;
$$;

create trigger event_functions_touch
  before insert or update or delete on public.event_functions
  for each row execute function app.functions_touch_event();


-- Migration 14: event_vendors and vendor_quotes for Phase 4 VendorConnect.

create table public.event_vendors (
  id           uuid primary key default gen_random_uuid(),
  event_id     uuid not null references public.events (id) on delete cascade,
  category     varchar(60) not null check (length(trim(category)) > 0),
  name         varchar(160) not null check (length(trim(name)) > 0),
  contact_name varchar(120),
  email        text,
  phone        text,
  website_url  text,
  notes        text,
  status       text not null default 'identified' check (status in ('identified', 'contacted', 'quoted', 'shortlisted', 'booked', 'declined')),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  archived_at  timestamptz,
  constraint event_vendors_event_id_id_key unique (id, event_id)
);

comment on table public.event_vendors is 'Event-scoped vendor records managed privately by event hosts.';

create index event_vendors_event_category_status_idx on public.event_vendors (event_id, category, status);
create index event_vendors_active_idx on public.event_vendors (event_id) where archived_at is null;

create table public.vendor_quotes (
  id            uuid primary key default gen_random_uuid(),
  vendor_id     uuid not null references public.event_vendors (id) on delete cascade,
  amount        numeric(12,2) not null check (amount >= 0),
  currency      char(3) not null check (currency ~ '^[A-Z]{3}$'),
  scope_summary text not null check (length(trim(scope_summary)) > 0),
  valid_until   date,
  notes         text,
  status        text not null default 'received' check (status in ('received', 'shortlisted', 'accepted', 'rejected', 'expired')),
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

comment on table public.vendor_quotes is 'User-entered commercial quotation offers from vendors.';

create index vendor_quotes_vendor_status_valid_idx on public.vendor_quotes (vendor_id, status, valid_until);

-- Trigger function for event_vendors touching parent event
create or replace function app.vendor_touch_event()
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

create trigger event_vendors_touch_event_trigger
  before update on public.event_vendors
  for each row execute function app.vendor_touch_event();

create trigger event_vendors_after_insert_trigger
  after insert or delete on public.event_vendors
  for each row execute function app.vendor_touch_event();

-- Trigger function for vendor_quotes touching parent event
create or replace function app.quote_touch_event()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  target_event_id uuid;
  target_vendor_id uuid;
begin
  if (tg_op = 'DELETE') then
    target_vendor_id := old.vendor_id;
  else
    new.updated_at := pg_catalog.now();
    target_vendor_id := new.vendor_id;
  end if;

  select event_id into target_event_id
    from public.event_vendors
   where id = target_vendor_id;

  if (target_event_id is not null) then
    update public.events
       set title = title
     where id = target_event_id
       and status <> 'archived';
  end if;

  if (tg_op = 'DELETE') then
    return old;
  else
    return new;
  end if;
end;
$$;

create trigger vendor_quotes_touch_event_trigger
  before update on public.vendor_quotes
  for each row execute function app.quote_touch_event();

create trigger vendor_quotes_after_insert_trigger
  after insert or delete on public.vendor_quotes
  for each row execute function app.quote_touch_event();


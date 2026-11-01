-- Migration 17: GiftCircle schema — gift_registries, gift_items, gift_reservations, gift_contributions, idempotency_records

-- Helper function to retrieve candidate public share token hash from transaction context
create or replace function app.current_share_token_hash()
returns text
language sql
stable
set search_path = ''
as $$
  select nullif(pg_catalog.current_setting('app.share_token_hash', true), '')
$$;

grant execute on function app.current_share_token_hash() to utsavai_app;

-- ---------------------------------------------------------------- gift_registries
create table if not exists public.gift_registries (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.events(id) on delete cascade,
  title text not null check (length(trim(title)) between 1 and 160),
  is_public boolean not null default false,
  share_token_hash text unique,
  allow_group_gifting boolean not null default true,
  expires_at timestamptz,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint gift_registries_event_id_key unique (event_id)
);

create index if not exists idx_gift_registries_event on public.gift_registries (event_id);
create index if not exists idx_gift_registries_token_hash on public.gift_registries (share_token_hash) where share_token_hash is not null;

-- ---------------------------------------------------------------- gift_items
create table if not exists public.gift_items (
  id uuid primary key default gen_random_uuid(),
  registry_id uuid not null references public.gift_registries(id) on delete cascade,
  title text not null check (length(trim(title)) between 1 and 160),
  description text check (description is null or length(description) <= 2000),
  item_type text not null default 'product' check (item_type in ('product', 'cash_fund', 'experience', 'other')),
  gift_mode text not null default 'individual' check (gift_mode in ('individual', 'group')),
  product_url text check (product_url is null or length(product_url) <= 1000),
  target_amount numeric(12,2) check (target_amount is null or target_amount > 0),
  currency text not null check (length(currency) = 3),
  priority text not null default 'important' check (priority in ('nice_to_have', 'important', 'high_priority')),
  display_order integer not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint gift_items_group_target_required check (
    gift_mode <> 'group' or (target_amount is not null and target_amount > 0)
  )
);

create index if not exists idx_gift_items_registry_active on public.gift_items (registry_id, is_active, display_order);

-- ---------------------------------------------------------------- gift_reservations
create table if not exists public.gift_reservations (
  id uuid primary key default gen_random_uuid(),
  gift_item_id uuid not null references public.gift_items(id) on delete cascade,
  guest_alias text check (guest_alias is null or length(trim(guest_alias)) between 1 and 80),
  status text not null default 'reserved' check (status in ('reserved', 'cancelled', 'fulfilled', 'expired')),
  cancellation_token_hash text unique,
  expires_at timestamptz,
  idempotency_key text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_gift_reservations_item_status on public.gift_reservations (gift_item_id, status);
create index if not exists idx_gift_reservations_cancel_hash on public.gift_reservations (cancellation_token_hash) where cancellation_token_hash is not null;
create unique index if not exists idx_unique_active_gift_reservation on public.gift_reservations (gift_item_id) where status in ('reserved', 'fulfilled');
create unique index if not exists idx_gift_reservations_idempotency on public.gift_reservations (gift_item_id, idempotency_key) where idempotency_key is not null;

-- ---------------------------------------------------------------- gift_contributions
create table if not exists public.gift_contributions (
  id uuid primary key default gen_random_uuid(),
  gift_item_id uuid not null references public.gift_items(id) on delete cascade,
  guest_alias text check (guest_alias is null or length(trim(guest_alias)) between 1 and 80),
  amount numeric(12,2) not null check (amount > 0),
  currency text not null check (length(currency) = 3),
  status text not null default 'pledged' check (status in ('pledged', 'verified', 'withdrawn', 'refunded')),
  verification_method text check (verification_method is null or verification_method in ('host_manual_confirmation', 'payment_provider_webhook')),
  verified_at timestamptz,
  verified_by uuid references public.profiles(user_id) on delete set null,
  provider_reference text check (provider_reference is null or length(provider_reference) <= 255),
  confirmation_note text check (confirmation_note is null or length(confirmation_note) <= 2000),
  idempotency_key text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint gift_contributions_status_verification_check check (
    (status = 'pledged' and verified_at is null and verified_by is null and verification_method is null)
    or
    (status = 'verified' and verified_at is not null and verification_method is not null)
    or
    (status in ('withdrawn', 'refunded'))
  )
);

create index if not exists idx_gift_contributions_item_status on public.gift_contributions (gift_item_id, status);
create unique index if not exists idx_gift_contributions_idempotency on public.gift_contributions (gift_item_id, idempotency_key) where idempotency_key is not null;

-- ---------------------------------------------------------------- idempotency_records
create table if not exists public.idempotency_records (
  id uuid primary key default gen_random_uuid(),
  scope text not null check (length(scope) between 1 and 100),
  idempotency_key text not null check (length(idempotency_key) between 1 and 128),
  request_hash text not null check (length(request_hash) = 64),
  response_code integer not null,
  response_body jsonb not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '24 hours'),
  constraint idempotency_records_scope_key unique (scope, idempotency_key)
);

create index if not exists idx_idempotency_records_scope_key on public.idempotency_records (scope, idempotency_key);

-- ---------------------------------------------------------------- triggers
create trigger touch_gift_reservations_updated_at
  before update on public.gift_reservations
  for each row execute function app.set_updated_at();

create trigger touch_gift_contributions_updated_at
  before update on public.gift_contributions
  for each row execute function app.set_updated_at();

-- Trigger function for gift_registries touching parent event
create or replace function app.registry_touch_event()
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
     set revision = revision + 1,
         updated_at = pg_catalog.now()
   where id = target_id
     and status <> 'archived';

  if (tg_op = 'DELETE') then
    return old;
  else
    return new;
  end if;
end;
$$;

create trigger gift_registries_touch_event_trigger
  before update on public.gift_registries
  for each row execute function app.registry_touch_event();

create trigger gift_registries_after_insert_trigger
  after insert or delete on public.gift_registries
  for each row execute function app.registry_touch_event();

-- Trigger function for gift_items touching parent event
create or replace function app.gift_item_touch_event()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  target_event_id uuid;
  target_registry_id uuid;
begin
  if (tg_op = 'DELETE') then
    target_registry_id := old.registry_id;
  else
    new.updated_at := pg_catalog.now();
    target_registry_id := new.registry_id;
  end if;

  select event_id into target_event_id
    from public.gift_registries
   where id = target_registry_id;

  if (target_event_id is not null) then
    update public.events
       set revision = revision + 1,
           updated_at = pg_catalog.now()
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

create trigger gift_items_touch_event_trigger
  before update on public.gift_items
  for each row execute function app.gift_item_touch_event();

create trigger gift_items_after_insert_trigger
  after insert or delete on public.gift_items
  for each row execute function app.gift_item_touch_event();

-- Migration 12: Budgets, budget_categories, and expenses. Exact shape per docs/DATABASE_SCHEMA.md section 4.

create table public.budgets (
  id          uuid primary key default gen_random_uuid(),
  event_id    uuid not null references public.events (id) on delete cascade,
  total_limit numeric(12,2) not null check (total_limit >= 0),
  currency    char(3) not null check (currency ~ '^[A-Z]{3}$'),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint budgets_event_id_unique unique (event_id)
);

comment on table public.budgets is 'Event spending limits and overall budget configuration. One per event.';

create index budgets_event_idx on public.budgets (event_id);

create table public.budget_categories (
  id             uuid primary key default gen_random_uuid(),
  budget_id      uuid not null references public.budgets (id) on delete cascade,
  category_key   varchar(64) not null check (char_length(btrim(category_key)) >= 1),
  name           varchar(160) not null check (char_length(btrim(name)) >= 1),
  planned_amount numeric(12,2) not null default 0.00 check (planned_amount >= 0),
  sort_order     integer not null default 0,
  is_deleted     boolean not null default false,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  constraint budget_categories_budget_key_unique unique (budget_id, category_key)
);

comment on table public.budget_categories is 'Budget allocation buckets by category.';

create index budget_categories_budget_sort_idx on public.budget_categories (budget_id, sort_order, created_at);

create table public.expenses (
  id                 uuid primary key default gen_random_uuid(),
  event_id           uuid not null references public.events (id) on delete cascade,
  budget_category_id uuid not null references public.budget_categories (id) on delete restrict,
  vendor_id          uuid,
  description        varchar(240) not null check (char_length(btrim(description)) >= 1),
  amount             numeric(12,2) not null check (amount > 0),
  currency           char(3) not null check (currency ~ '^[A-Z]{3}$'),
  expense_date       date not null default current_date,
  status             text not null default 'planned' check (status in ('planned', 'committed', 'paid', 'cancelled')),
  is_deleted         boolean not null default false,
  created_by         uuid not null references public.profiles (user_id),
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

comment on table public.expenses is 'Recorded expenses for an event, tracked by status: planned, committed, paid, cancelled.';

create index expenses_event_status_idx on public.expenses (event_id, status);
create index expenses_category_status_idx on public.expenses (budget_category_id, status);
create index expenses_event_date_idx on public.expenses (event_id, expense_date);

-- Trigger function to touch parent event revision on budget mutations
create or replace function app.budget_touch_event()
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

create trigger budgets_touch_event_trigger
  before update on public.budgets
  for each row execute function app.budget_touch_event();

create trigger budgets_after_insert_trigger
  after insert or delete on public.budgets
  for each row execute function app.budget_touch_event();

-- Trigger function for budget_categories touching parent event
create or replace function app.category_touch_event()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  target_event_id uuid;
  b_id uuid;
begin
  if (tg_op = 'DELETE') then
    b_id := old.budget_id;
  else
    new.updated_at := pg_catalog.now();
    b_id := new.budget_id;
  end if;

  select b.event_id into target_event_id
    from public.budgets b
   where b.id = b_id;

  if target_event_id is not null then
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

create trigger categories_touch_event_trigger
  before update on public.budget_categories
  for each row execute function app.category_touch_event();

create trigger categories_after_insert_trigger
  after insert or delete on public.budget_categories
  for each row execute function app.category_touch_event();

-- Trigger function for expenses touching parent event
create or replace function app.expense_touch_event()
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

create trigger expenses_touch_event_trigger
  before update on public.expenses
  for each row execute function app.expense_touch_event();

create trigger expenses_after_insert_trigger
  after insert or delete on public.expenses
  for each row execute function app.expense_touch_event();

-- Trigger function for tasks touching parent event
create or replace function app.task_touch_event()
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

create trigger tasks_touch_event_trigger
  before update on public.tasks
  for each row execute function app.task_touch_event();

create trigger tasks_after_insert_trigger
  after insert or delete on public.tasks
  for each row execute function app.task_touch_event();


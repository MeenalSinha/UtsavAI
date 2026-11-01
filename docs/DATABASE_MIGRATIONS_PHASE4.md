# Database Migrations — Phase 4

## 1. Overview

Phase 4 introduces 3 database migrations to PostgreSQL via Supabase:

1. `20261101001400_event_vendors_and_quotes.sql`
2. `20261101001500_phase4_rls_and_grants.sql`
3. `20261101001600_expense_vendor_relationship.sql`

---

## 2. Migration Details

### Migration 14: `20261101001400_event_vendors_and_quotes.sql`
- Creates table `public.event_vendors`:
  - `id uuid primary key default gen_random_uuid()`
  - `event_id uuid not null references public.events(id) on delete cascade`
  - `name text not null check (length(trim(name)) between 1 and 200)`
  - `category text not null check (length(trim(category)) between 1 and 100)`
  - `contact_name text check (contact_name is null or length(trim(contact_name)) between 1 and 200)`
  - `phone text check (phone is null or length(trim(phone)) between 1 and 50)`
  - `email text check (email is null or length(trim(email)) between 3 and 255)`
  - `website_url text check (website_url is null or length(trim(website_url)) between 1 and 500)`
  - `notes text check (notes is null or length(notes) <= 4000)`
  - `status text not null default 'identified' check (status in ('identified', 'contacted', 'quoted', 'shortlisted', 'booked', 'declined'))`
  - `created_at timestamptz not null default now()`
  - `updated_at timestamptz not null default now()`
  - `archived_at timestamptz`
  - `constraint event_vendors_id_event_id_key unique (id, event_id)`
- Creates table `public.vendor_quotes`:
  - `id uuid primary key default gen_random_uuid()`
  - `event_id uuid not null references public.events(id) on delete cascade`
  - `vendor_id uuid not null`
  - `foreign key (vendor_id, event_id) references public.event_vendors(id, event_id) on delete cascade`
  - `amount numeric(12,2) not null check (amount >= 0)`
  - `currency text not null check (length(currency) = 3)`
  - `scope_summary text not null check (length(trim(scope_summary)) between 1 and 2000)`
  - `valid_until date`
  - `notes text check (notes is null or length(notes) <= 2000)`
  - `status text not null default 'received' check (status in ('received', 'shortlisted', 'accepted', 'rejected', 'expired'))`
  - `created_at timestamptz not null default now()`
  - `updated_at timestamptz not null default now()`
- Attaches trigger `touch_event_revision_on_vendor_change` updating parent event `revision` and `updated_at` on mutations.

### Migration 15: `20261101001500_phase4_rls_and_grants.sql`
- Enables Row Level Security on `event_vendors` and `vendor_quotes`.
- Enforces `force row level security`.
- Grants `select, insert, update` to `utsavai_app` (zero `DELETE` grants).
- Establishes RLS policies ensuring only users with active `event_memberships` can view or manage vendors.

### Migration 16: `20261101001600_expense_vendor_relationship.sql`
- Adds foreign key constraint:
  `alter table public.expenses add constraint expenses_vendor_fk foreign key (vendor_id, event_id) references public.event_vendors (id, event_id) on delete set null;`
- Creates composite index `idx_expenses_event_vendor on public.expenses (event_id, vendor_id)`.
- Guarantees complete cross-event tenant isolation between expenses and vendors.


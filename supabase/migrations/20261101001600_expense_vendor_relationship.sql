-- Migration 16: Composite foreign key relationship between expenses and event_vendors.

-- Enforces that an expense can only reference a vendor belonging to the exact same event.
alter table public.expenses
  add constraint expenses_vendor_event_fkey
  foreign key (vendor_id, event_id)
  references public.event_vendors (id, event_id)
  on delete set null;

create index if not exists expenses_vendor_idx on public.expenses (vendor_id) where vendor_id is not null;


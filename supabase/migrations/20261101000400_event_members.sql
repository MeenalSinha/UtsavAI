-- Migration 4: event_members and the owner-membership invariant.

create table public.event_members (
  event_id   uuid not null references public.events (id) on delete cascade,
  user_id    uuid not null references public.profiles (user_id) on delete cascade,
  role       text not null check (role in ('owner', 'editor', 'viewer')),
  status     text not null default 'active' check (status in ('invited', 'active', 'revoked')),
  invited_by uuid references public.profiles (user_id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (event_id, user_id)
);

create index event_members_user_status_idx on public.event_members (user_id, status);
create index event_members_event_role_idx on public.event_members (event_id, role);

-- Exactly one active owner membership per event.
create unique index event_members_one_active_owner_idx
  on public.event_members (event_id)
  where role = 'owner' and status = 'active';

create trigger event_members_set_updated_at
  before update on public.event_members
  for each row execute function app.set_updated_at();

-- An event can never be committed without its owner membership. The check is a
-- deferred constraint trigger, so creating the event and the membership in one
-- transaction is valid while creating the event alone fails at commit.
create or replace function app.assert_event_has_owner_member()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if not exists (
    select 1
      from public.event_members m
     where m.event_id = new.id
       and m.user_id = new.owner_user_id
       and m.role = 'owner'
       and m.status = 'active'
  ) then
    raise exception 'event % has no active owner membership', new.id using errcode = '23514';
  end if;
  return null;
end
$$;

create constraint trigger events_require_owner_member
  after insert on public.events
  deferrable initially deferred
  for each row execute function app.assert_event_has_owner_member();

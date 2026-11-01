-- Migration 5: append-only audit log (docs/DATABASE_SCHEMA.md section 9.1).

create table public.audit_logs (
  id            uuid primary key default gen_random_uuid(),
  event_id      uuid not null references public.events (id) on delete cascade,
  actor_user_id uuid references public.profiles (user_id) on delete set null,
  actor_type    text not null check (actor_type in ('user', 'public_guest', 'system')),
  action        text not null check (char_length(action) between 1 and 80),
  entity_type   text not null check (char_length(entity_type) between 1 and 60),
  entity_id     uuid,
  metadata      jsonb not null default '{}'::jsonb check (pg_column_size(metadata) <= 4096),
  request_id    text check (request_id is null or char_length(request_id) <= 80),
  created_at    timestamptz not null default now()
);

create index audit_logs_event_created_idx on public.audit_logs (event_id, created_at desc);
create index audit_logs_entity_idx on public.audit_logs (entity_type, entity_id);

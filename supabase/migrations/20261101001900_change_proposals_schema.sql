-- Migration 19: Phase 6 Adaptive Planning Engine — change_proposals table

create table if not exists public.change_proposals (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.events(id) on delete cascade,
  created_by uuid not null references public.profiles(user_id),
  base_revision bigint not null,
  request_text text not null check (length(trim(request_text)) between 1 and 4000),
  requested_changes jsonb not null default '{}'::jsonb,
  impact_result jsonb not null default '{}'::jsonb,
  ai_explanation text check (ai_explanation is null or length(ai_explanation) <= 10000),
  status text not null default 'proposed' check (status in ('proposed', 'accepted', 'rejected', 'stale', 'expired')),
  accepted_at timestamptz,
  accepted_revision bigint,
  rules_version text not null default '1.0.0',
  schema_version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_change_proposals_event_created on public.change_proposals (event_id, created_at desc);
create index if not exists idx_change_proposals_event_status on public.change_proposals (event_id, status);

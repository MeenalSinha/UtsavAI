-- Migration 9: ai_conversations, ai_proposals, ai_messages. Exact shape per docs/DATABASE_SCHEMA.md section 8.

create table public.ai_conversations (
  id         uuid primary key default gen_random_uuid(),
  event_id   uuid not null references public.events (id) on delete cascade,
  user_id    uuid not null references public.profiles (user_id) on delete cascade,
  title      varchar(160),
  is_deleted boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

comment on table public.ai_conversations is 'Persistent chat sessions scoped to an event and member.';

create index ai_conversations_event_user_idx on public.ai_conversations (event_id, user_id, updated_at desc);

create table public.ai_proposals (
  id              uuid primary key default gen_random_uuid(),
  event_id        uuid not null references public.events (id) on delete cascade,
  conversation_id uuid references public.ai_conversations (id) on delete cascade,
  created_by      uuid not null references public.profiles (user_id) on delete cascade,
  proposal_type   text not null check (proposal_type in ('plan', 'timeline', 'budget_suggestions', 'vendor_summary', 'gift_recommendations')),
  base_revision   bigint not null check (base_revision >= 1),
  schema_version  integer not null default 1,
  payload         jsonb not null,
  status          text not null default 'proposed' check (status in ('proposed', 'partially_accepted', 'accepted', 'rejected', 'stale')),
  model_id        text,
  prompt_version  text,
  created_at      timestamptz not null default now(),
  accepted_at     timestamptz
);

comment on table public.ai_proposals is 'Structured AI proposals with revision tracking and acceptance state.';

create index ai_proposals_event_created_idx on public.ai_proposals (event_id, created_at desc);
create index ai_proposals_event_status_idx on public.ai_proposals (event_id, status);

create table public.ai_messages (
  id                uuid primary key default gen_random_uuid(),
  conversation_id   uuid not null references public.ai_conversations (id) on delete cascade,
  proposal_id       uuid references public.ai_proposals (id) on delete set null,
  role              text not null check (role in ('user', 'assistant', 'system_metadata')),
  content           text not null check (char_length(btrim(content)) >= 1),
  model_id          text,
  prompt_version    text,
  validation_status text not null default 'not_applicable' check (validation_status in ('not_applicable', 'valid', 'invalid', 'repaired')),
  created_at        timestamptz not null default now()
);

comment on table public.ai_messages is 'Message history within an AI conversation.';

create index ai_messages_conversation_idx on public.ai_messages (conversation_id, created_at asc);


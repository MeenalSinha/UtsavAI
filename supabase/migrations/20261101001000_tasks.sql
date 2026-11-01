-- Migration 10: tasks and task_dependencies.
-- Minimal persistence for accepted PlanAI starter tasks per docs/DATABASE_SCHEMA.md section 5.

create table public.tasks (
  id               uuid primary key default gen_random_uuid(),
  event_id         uuid not null references public.events (id) on delete cascade,
  function_id      uuid references public.event_functions (id) on delete set null,
  title            varchar(180) not null check (char_length(btrim(title)) >= 1),
  description      text check (description is null or char_length(description) <= 4000),
  due_at           timestamptz,
  status           text not null default 'todo' check (status in ('todo', 'in_progress', 'blocked', 'done', 'cancelled')),
  priority         text not null default 'medium' check (priority in ('low', 'medium', 'high', 'urgent')),
  assigned_user_id uuid references public.profiles (user_id) on delete set null,
  origin           text not null default 'manual' check (origin in ('manual', 'ai_accepted', 'adaptive_accepted')),
  sort_order       integer not null default 0,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  completed_at     timestamptz
);

comment on table public.tasks is 'Planning tasks and milestones. Accepted PlanAI starter tasks carry origin = ai_accepted.';

create index tasks_event_status_due_idx on public.tasks (event_id, status, due_at);
create index tasks_assigned_status_idx on public.tasks (assigned_user_id, status, due_at);
create index tasks_function_idx on public.tasks (function_id);

create table public.task_dependencies (
  task_id            uuid not null references public.tasks (id) on delete cascade,
  depends_on_task_id uuid not null references public.tasks (id) on delete cascade,
  created_at         timestamptz not null default now(),
  primary key (task_id, depends_on_task_id),
  constraint task_dependencies_no_self_ref check (task_id <> depends_on_task_id)
);

comment on table public.task_dependencies is 'Directed dependencies between tasks within the same event.';

create index task_dependencies_reverse_idx on public.task_dependencies (depends_on_task_id);


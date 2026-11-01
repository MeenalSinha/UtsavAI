-- Migration 11: Phase 2 RLS policies and least-privilege grants.

alter table public.event_preferences enable row level security;
alter table public.event_functions   enable row level security;
alter table public.ai_conversations  enable row level security;
alter table public.ai_proposals      enable row level security;
alter table public.ai_messages       enable row level security;
alter table public.tasks             enable row level security;
alter table public.task_dependencies enable row level security;

-- Revoke all permissions from anon, authenticated, and public
do $$
declare
  r text;
  tbls text[] := array[
    'event_preferences', 'event_functions', 'ai_conversations',
    'ai_proposals', 'ai_messages', 'tasks', 'task_dependencies'
  ];
  t text;
begin
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      foreach t in array tbls loop
        execute format('revoke all on public.%I from %I', t, r);
      end loop;
    end if;
  end loop;
  foreach t in array tbls loop
    execute format('revoke all on public.%I from public', t);
  end loop;
end
$$;

-- Helper function to check if app.current_user_id() is an active event member with optional role requirement
create or replace function app.is_event_member(p_event_id uuid, p_required_roles text[] default null)
returns boolean
language sql
stable
set search_path = ''
as $$
  select exists (
    select 1 from public.events e
    where e.id = p_event_id
      and (
        (e.owner_user_id = app.current_user_id() and (p_required_roles is null or 'owner' = any(p_required_roles)))
        or exists (
          select 1 from public.event_members m
          where m.event_id = p_event_id
            and m.user_id = app.current_user_id()
            and m.status = 'active'
            and (p_required_roles is null or m.role = any(p_required_roles))
        )
      )
  );
$$;

grant execute on function app.is_event_member(uuid, text[]) to utsavai_app;

-- Dedicated helper for removing an event function
create or replace function app.delete_event_function(p_event_id uuid, p_function_id uuid)
returns boolean
language plpgsql
set search_path = ''
as $$
declare
  deleted_count integer;
begin
  if not app.is_event_member(p_event_id, array['owner', 'editor']) then
    raise exception 'unauthorized to delete function' using errcode = '42501';
  end if;

  update public.event_functions
     set is_deleted = true,
         updated_at = pg_catalog.now()
   where id = p_function_id
     and event_id = p_event_id
     and not is_deleted;

  get diagnostics deleted_count = row_count;
  return deleted_count > 0;
end;
$$;

grant execute on function app.delete_event_function(uuid, uuid) to utsavai_app;

-- Dedicated helper for removing an AI conversation
create or replace function app.delete_ai_conversation(p_event_id uuid, p_conversation_id uuid)
returns boolean
language plpgsql
set search_path = ''
as $$
declare
  deleted_count integer;
begin
  if not app.is_event_member(p_event_id, array['owner', 'editor']) then
    raise exception 'unauthorized to delete conversation' using errcode = '42501';
  end if;

  update public.ai_conversations
     set is_deleted = true,
         updated_at = pg_catalog.now()
   where id = p_conversation_id
     and event_id = p_event_id
     and user_id = app.current_user_id()
     and not is_deleted;

  get diagnostics deleted_count = row_count;
  return deleted_count > 0;
end;
$$;

grant execute on function app.delete_ai_conversation(uuid, uuid) to utsavai_app;

-- Explicit grants for the application runtime role (NO DELETE, NO TRUNCATE)
grant select, insert, update on public.event_preferences to utsavai_app;
grant select, insert, update on public.event_functions to utsavai_app;
grant select, insert, update on public.ai_conversations to utsavai_app;
grant select, insert, update on public.ai_proposals to utsavai_app;
grant select, insert on public.ai_messages to utsavai_app;
grant select, insert, update on public.tasks to utsavai_app;
grant select, insert on public.task_dependencies to utsavai_app;

-- ---------------------------------------------------------------- event_preferences
create policy preferences_select on public.event_preferences
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy preferences_insert on public.event_preferences
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

create policy preferences_update on public.event_preferences
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- event_functions
create policy functions_select on public.event_functions
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy functions_insert on public.event_functions
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

create policy functions_update on public.event_functions
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- ai_conversations
create policy ai_conversations_select on public.ai_conversations
  for select to utsavai_app
  using (user_id = app.current_user_id() and app.is_event_member(event_id));

create policy ai_conversations_insert on public.ai_conversations
  for insert to utsavai_app
  with check (user_id = app.current_user_id() and app.is_event_member(event_id, array['owner', 'editor']));

create policy ai_conversations_update on public.ai_conversations
  for update to utsavai_app
  using (user_id = app.current_user_id() and app.is_event_member(event_id, array['owner', 'editor']))
  with check (user_id = app.current_user_id() and app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- ai_proposals
create policy ai_proposals_select on public.ai_proposals
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy ai_proposals_insert on public.ai_proposals
  for insert to utsavai_app
  with check (created_by = app.current_user_id() and app.is_event_member(event_id, array['owner', 'editor']));

create policy ai_proposals_update on public.ai_proposals
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- ai_messages
create policy ai_messages_select on public.ai_messages
  for select to utsavai_app
  using (exists (
    select 1 from public.ai_conversations c
     where c.id = ai_messages.conversation_id
       and c.user_id = app.current_user_id()
       and app.is_event_member(c.event_id)
  ));

create policy ai_messages_insert on public.ai_messages
  for insert to utsavai_app
  with check (exists (
    select 1 from public.ai_conversations c
     where c.id = ai_messages.conversation_id
       and c.user_id = app.current_user_id()
       and app.is_event_member(c.event_id, array['owner', 'editor'])
  ));

-- ---------------------------------------------------------------- tasks
create policy tasks_select on public.tasks
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy tasks_insert on public.tasks
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

create policy tasks_update on public.tasks
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- task_dependencies
create policy task_dependencies_select on public.task_dependencies
  for select to utsavai_app
  using (exists (
    select 1 from public.tasks t
     where t.id = task_dependencies.task_id
       and app.is_event_member(t.event_id)
  ));

create policy task_dependencies_insert on public.task_dependencies
  for insert to utsavai_app
  with check (exists (
    select 1 from public.tasks t1, public.tasks t2
     where t1.id = task_dependencies.task_id
       and t2.id = task_dependencies.depends_on_task_id
       and t1.event_id = t2.event_id
       and app.is_event_member(t1.event_id, array['owner', 'editor'])
  ));

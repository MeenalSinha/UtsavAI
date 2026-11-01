-- Migration 13: Phase 3 RLS policies and grants for budgets, categories, and expenses.

alter table public.budgets           enable row level security;
alter table public.budget_categories  enable row level security;
alter table public.expenses           enable row level security;

-- Revoke all permissions from anon, authenticated, and public
do $$
declare
  r text;
  tbls text[] := array['budgets', 'budget_categories', 'expenses'];
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

-- Explicit grants for the application runtime role utsavai_app
grant select, insert, update on public.budgets to utsavai_app;
grant select, insert, update, delete on public.budget_categories to utsavai_app;
grant select, insert, update on public.expenses to utsavai_app;
grant delete on public.task_dependencies to utsavai_app;

-- ---------------------------------------------------------------- budgets
create policy budgets_select on public.budgets
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy budgets_insert on public.budgets
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

create policy budgets_update on public.budgets
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- budget_categories
create policy budget_categories_select on public.budget_categories
  for select to utsavai_app
  using (exists (
    select 1 from public.budgets b
     where b.id = budget_categories.budget_id
       and app.is_event_member(b.event_id)
  ));

create policy budget_categories_insert on public.budget_categories
  for insert to utsavai_app
  with check (exists (
    select 1 from public.budgets b
     where b.id = budget_categories.budget_id
       and app.is_event_member(b.event_id, array['owner', 'editor'])
  ));

create policy budget_categories_update on public.budget_categories
  for update to utsavai_app
  using (exists (
    select 1 from public.budgets b
     where b.id = budget_categories.budget_id
       and app.is_event_member(b.event_id, array['owner', 'editor'])
  ))
  with check (exists (
    select 1 from public.budgets b
     where b.id = budget_categories.budget_id
       and app.is_event_member(b.event_id, array['owner', 'editor'])
  ));

create policy budget_categories_delete on public.budget_categories
  for delete to utsavai_app
  using (exists (
    select 1 from public.budgets b
     where b.id = budget_categories.budget_id
       and app.is_event_member(b.event_id, array['owner', 'editor'])
  ));

-- ---------------------------------------------------------------- expenses
create policy expenses_select on public.expenses
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy expenses_insert on public.expenses
  for insert to utsavai_app
  with check (
    created_by = app.current_user_id()
    and app.is_event_member(event_id, array['owner', 'editor'])
  );

create policy expenses_update on public.expenses
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));

-- ---------------------------------------------------------------- task_dependencies (allow delete)
create policy task_dependencies_delete on public.task_dependencies
  for delete to utsavai_app
  using (exists (
    select 1 from public.tasks t
     where t.id = task_dependencies.task_id
       and app.is_event_member(t.event_id, array['owner', 'editor'])
  ));


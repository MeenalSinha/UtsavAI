# Database Migrations Documentation: Phase 6

**Version:** 1.0.0  
**Date:** 1 November 2026  

---

## Migration 19: `20261101001900_change_proposals_schema.sql`

Creates the core schema for the Adaptive Planning Engine.

```sql
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
```

---

## Migration 20: `20261101002000_change_proposals_rls_and_grants.sql`

Secures `public.change_proposals` with Row-Level Security, restricts public access, and grants minimal privileges to the runtime application role:

```sql
alter table public.change_proposals enable row level security;

-- Revoke all permissions from anon, authenticated, and public
do $$
declare
  r text;
  tbls text[] := array['change_proposals'];
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

-- Explicit grants for runtime role utsavai_app (strictly zero DELETE grants)
grant select, insert, update on public.change_proposals to utsavai_app;

-- RLS policies
create policy change_proposals_select on public.change_proposals
  for select to utsavai_app
  using (app.is_event_member(event_id));

create policy change_proposals_insert on public.change_proposals
  for insert to utsavai_app
  with check (app.is_event_member(event_id, array['owner', 'editor']));

create policy change_proposals_update on public.change_proposals
  for update to utsavai_app
  using (app.is_event_member(event_id, array['owner', 'editor']))
  with check (app.is_event_member(event_id, array['owner', 'editor']));
```

---

## Verification Assertions
- Table count in public schema with RLS enabled: **22 tables**.
- Migration reproducibility verified (scratch database dump diff identical).
- Guardrails verified: zero `BYPASSRLS` grants, zero `SECURITY DEFINER` functions.

-- UtsavAI Phase 1 / migration 1: foundation helpers and runtime role.
-- Conventions follow docs/DATABASE_SCHEMA.md section 1.

create schema if not exists app;
comment on schema app is 'UtsavAI helper functions (identity context, triggers). Not exposed through the Supabase Data API.';

-- Dedicated runtime role used by FastAPI. NOBYPASSRLS, no superuser, no DDL.
-- The migration creates it NOLOGIN; the operator enables LOGIN and sets a
-- password out of band (see docs/DATABASE_SETUP.md). No secret lives in git.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'utsavai_app') then
    create role utsavai_app nologin nosuperuser nocreatedb nocreaterole noinherit nobypassrls;
  else
    alter role utsavai_app nosuperuser nocreatedb nocreaterole nobypassrls;
  end if;
end
$$;

grant usage on schema app to utsavai_app;
grant usage on schema public to utsavai_app;

-- Identity context set by FastAPI with set_config('app.user_id', <uuid>, true)
-- after the Supabase JWT has been verified. Returns NULL when unset or empty,
-- which makes every policy deny by default. An invalid uuid raises (fails closed).
create or replace function app.current_user_id()
returns uuid
language sql
stable
set search_path = ''
as $$
  select nullif(pg_catalog.current_setting('app.user_id', true), '')::uuid
$$;

grant execute on function app.current_user_id() to utsavai_app;

create or replace function app.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := pg_catalog.now();
  return new;
end
$$;

-- Validates IANA timezone names (CHECK constraints cannot use subqueries).
create or replace function app.validate_timezone()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.timezone is not null then
    perform pg_catalog.now() at time zone new.timezone;
  end if;
  return new;
exception
  when invalid_parameter_value then
    raise exception 'invalid IANA timezone: %', new.timezone using errcode = '22023';
end
$$;

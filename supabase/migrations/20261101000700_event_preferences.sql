-- Migration 7: event_preferences. Exact shape per docs/DATABASE_SCHEMA.md section 3.4.

create table public.event_preferences (
  event_id            uuid primary key references public.events (id) on delete cascade,
  style_tags          text[] not null default '{}',
  cultural_context    jsonb not null default '{}'::jsonb check (jsonb_typeof(cultural_context) = 'object'),
  priorities          jsonb not null default '{}'::jsonb check (jsonb_typeof(priorities) = 'object'),
  accessibility_notes jsonb not null default '{}'::jsonb check (jsonb_typeof(accessibility_notes) = 'object'),
  schema_version      integer not null default 1 check (schema_version >= 1),
  updated_at          timestamptz not null default now()
);

comment on table public.event_preferences is 'User-supplied cultural, style, and personal preferences.';

create or replace function app.preferences_touch_event()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at := pg_catalog.now();
  update public.events
     set title = title
   where id = new.event_id
     and status <> 'archived';
  return new;
end;
$$;

create trigger event_preferences_touch
  before insert or update on public.event_preferences
  for each row execute function app.preferences_touch_event();


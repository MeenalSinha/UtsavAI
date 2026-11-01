-- Migration 2: profiles (1:1 with auth.users). Credentials stay in Supabase Auth.

create table public.profiles (
  user_id          uuid primary key references auth.users (id) on delete cascade,
  display_name     text check (display_name is null or char_length(btrim(display_name)) between 1 and 80),
  preferred_locale text not null default 'en-IN' check (preferred_locale ~ '^[a-z]{2,3}(-[A-Z]{2})?$'),
  timezone         text,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

comment on table public.profiles is 'Minimal application profile. Primary key references auth.users.id.';

create trigger profiles_set_updated_at
  before update on public.profiles
  for each row execute function app.set_updated_at();

create trigger profiles_validate_timezone
  before insert or update of timezone on public.profiles
  for each row execute function app.validate_timezone();

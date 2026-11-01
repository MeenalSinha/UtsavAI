# UtsavAI Phase 2 — Database Migrations & Schema Architecture

## Overview

Phase 2 introduces the persistence foundation for Event Preferences, Event Functions, PlanAI Conversations & Proposals, and Event Tasks. All tables adhere to strict PostgreSQL constraints, Row-Level Security (RLS), and least-privilege permissions for the `utsavai_app` runtime role.

---

## Migration Catalog

| Migration File | Target Table(s) / Objects | Purpose |
| :--- | :--- | :--- |
| `20261101000700_event_preferences.sql` | `public.event_preferences`, trigger `trg_event_preferences_revision` | Stores aesthetic tags, cultural traditions, priorities, accessibility. Auto-bumps event revision. |
| `20261101000800_event_functions.sql` | `public.event_functions`, trigger `trg_event_functions_revision` | Stores itinerary functions/ceremonies with `sort_order`. Auto-bumps event revision on mutation. |
| `20261101000900_ai_and_planning.sql` | `public.ai_conversations`, `public.ai_proposals`, `public.ai_messages` | Stores persistent PlanAI chat threads, immutable structured proposals, and message history. |
| `20261101001000_tasks.sql` | `public.tasks`, `public.task_dependencies` | Stores preparation tasks with origin tracking (`manual`, `ai_accepted`, `system_template`) and task DAG dependencies. |
| `20261101001100_phase2_rls_and_grants.sql` | All Phase 2 tables, helper `app.is_event_member`, functions `app.delete_event_function`, `app.delete_ai_conversation` | Configures RLS policies, least-privilege grants, and security definer procedures. |

---

## Table Schemas & Constraints

### 1. `public.event_preferences`
* **Primary Key:** `event_id` (UUID references `public.events(id)` ON DELETE CASCADE).
* **Columns:**
  * `style_tags` (`TEXT[]` NOT NULL DEFAULT `{}`)
  * `cultural_context` (`JSONB` NOT NULL DEFAULT `{}`)
  * `priorities` (`JSONB` NOT NULL DEFAULT `{}`)
  * `accessibility_notes` (`JSONB` NOT NULL DEFAULT `{}`)
  * `schema_version` (`INTEGER` NOT NULL DEFAULT 1)
  * `created_at` (`TIMESTAMPTZ` NOT NULL DEFAULT `NOW()`)
  * `updated_at` (`TIMESTAMPTZ` NOT NULL DEFAULT `NOW()`)
* **Trigger:** Updates `updated_at` on `event_preferences` and triggers `revision = revision + 1`, `updated_at = NOW()` on the parent `public.events` record.

### 2. `public.event_functions`
* **Primary Key:** `id` (UUID DEFAULT `gen_random_uuid()`)
* **Foreign Key:** `event_id` references `public.events(id)` ON DELETE CASCADE.
* **Columns:**
  * `name` (`TEXT` NOT NULL)
  * `starts_at` (`TIMESTAMPTZ` NULL)
  * `ends_at` (`TIMESTAMPTZ` NULL)
  * `location_name` (`TEXT` NULL)
  * `notes` (`TEXT` NULL)
  * `sort_order` (`INTEGER` NOT NULL DEFAULT 0)
  * `created_at` (`TIMESTAMPTZ` NOT NULL DEFAULT `NOW()`)
  * `updated_at` (`TIMESTAMPTZ` NOT NULL DEFAULT `NOW()`)
* **Constraints:**
  * `check_event_functions_timing`: `ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at`
* **Trigger:** Bumps parent event `revision` upon INSERT, UPDATE, or DELETE.

### 3. `public.ai_conversations`
* **Primary Key:** `id` (UUID DEFAULT `gen_random_uuid()`)
* **Foreign Keys:**
  * `event_id` references `public.events(id)` ON DELETE CASCADE
  * `user_id` references `auth.users(id)` ON DELETE CASCADE
* **Columns:** `title` (TEXT), `created_at`, `updated_at`.

### 4. `public.ai_proposals`
* **Primary Key:** `id` (UUID DEFAULT `gen_random_uuid()`)
* **Foreign Keys:**
  * `event_id` references `public.events(id)` ON DELETE CASCADE
  * `conversation_id` references `public.ai_conversations(id)` ON DELETE SET NULL
* **Columns:**
  * `base_revision` (`INTEGER` NOT NULL)
  * `status` (`TEXT` NOT NULL DEFAULT `'proposed'`) — CHECK (`status IN ('proposed', 'partially_accepted', 'accepted', 'rejected', 'stale')`)
  * `schema_version` (`INTEGER` NOT NULL DEFAULT 1)
  * `payload` (`JSONB` NOT NULL)
  * `model_metadata` (`JSONB` NOT NULL DEFAULT `{}`)
  * `accepted_at` (`TIMESTAMPTZ` NULL)
  * `created_at` (`TIMESTAMPTZ` NOT NULL DEFAULT `NOW()`)

### 5. `public.ai_messages`
* **Primary Key:** `id` (UUID DEFAULT `gen_random_uuid()`)
* **Foreign Keys:**
  * `conversation_id` references `public.ai_conversations(id)` ON DELETE CASCADE
  * `proposal_id` references `public.ai_proposals(id)` ON DELETE SET NULL
* **Columns:**
  * `role` (`TEXT` NOT NULL) — CHECK (`role IN ('user', 'assistant', 'system_metadata')`)
  * `content` (`TEXT` NOT NULL)
  * `validation_status` (`TEXT` NOT NULL DEFAULT `'valid'`)
  * `created_at` (`TIMESTAMPTZ` NOT NULL DEFAULT `NOW()`)

### 6. `public.tasks` & `public.task_dependencies`
* **Primary Key:** `id` (UUID DEFAULT `gen_random_uuid()`)
* **Foreign Keys:**
  * `event_id` references `public.events(id)` ON DELETE CASCADE
  * `function_id` references `public.event_functions(id)` ON DELETE SET NULL
* **Columns:**
  * `title` (`TEXT` NOT NULL)
  * `description` (`TEXT` NULL)
  * `due_at` (`TIMESTAMPTZ` NULL)
  * `priority` (`TEXT` NOT NULL DEFAULT `'medium'`) — CHECK (`priority IN ('low', 'medium', 'high', 'urgent')`)
  * `status` (`TEXT` NOT NULL DEFAULT `'pending'`) — CHECK (`status IN ('pending', 'in_progress', 'completed', 'blocked', 'cancelled')`)
  * `origin` (`TEXT` NOT NULL DEFAULT `'manual'`) — CHECK (`origin IN ('manual', 'ai_accepted', 'system_template')`)
* **Dependencies Table:**
  * `(task_id, depends_on_task_id)` composite primary key with CHECK `task_id != depends_on_task_id`.

---

## Row-Level Security (RLS) & Least-Privilege Grants

* All 7 Phase 2 tables have `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;` applied.
* RLS policies enforce membership checks via `app.is_event_member(event_id, auth.uid())`.
* The `utsavai_app` runtime role is granted `SELECT, INSERT, UPDATE` on all application tables.
* **Security Invariant:** As in Phase 1, `utsavai_app` holds **NO DIRECT DELETE** privileges on private tables. Function and conversation deletions are executed via vetted `SECURITY DEFINER` procedures:
  * `app.delete_event_function(p_function_id UUID, p_event_id UUID)`
  * `app.delete_ai_conversation(p_conversation_id UUID, p_event_id UUID)`
  These verify membership before performing the deletion within an isolated database context.

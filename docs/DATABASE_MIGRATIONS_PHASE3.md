# Database Migrations Phase 3 — Budgets, Expenses & DAG Tasks

## 1. Summary of Migrations

Phase 3 introduces two database migrations:

1. `supabase/migrations/20261101001200_budgets_and_expenses.sql`
   - Defines `public.budgets` (1:1 with `public.events`).
   - Defines `public.budget_categories` (buckets for budget allocation).
   - Defines `public.expenses` (expense tracking with `status in ('planned', 'committed', 'paid', 'cancelled')`).
   - Creates triggers `budgets_touch_event_trigger`, `categories_touch_event_trigger`, `expenses_touch_event_trigger`, and `tasks_touch_event_trigger` to update the parent event's `revision` counter upon mutations.

2. `supabase/migrations/20261101001300_phase3_rls_and_grants.sql`
   - Enables Row Level Security (RLS) on `public.budgets`, `public.budget_categories`, and `public.expenses`.
   - Revokes permissions from `anon`, `authenticated`, and `public`.
   - Grants minimal privileges (`SELECT`, `INSERT`, `UPDATE`, and controlled `DELETE`) to the application role `utsavai_app`.
   - Enforces membership checks using `app.is_event_member()`.
   - 0 `SECURITY DEFINER` functions; 0 `BYPASSRLS` privileges.

## 2. Table Specifications

### 2.1 `public.budgets`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK, default `gen_random_uuid()` | Primary Key |
| `event_id` | UUID | FK `events(id)` ON DELETE CASCADE, UNIQUE | Associated event |
| `total_limit` | NUMERIC(12, 2) | NOT NULL, CHECK (`total_limit >= 0`) | Maximum spend ceiling |
| `currency` | CHAR(3) | NOT NULL, CHECK (`currency ~ '^[A-Z]{3}$'`) | ISO currency code (e.g. INR) |
| `created_at` | TIMESTAMPTZ | NOT NULL, default `now()` | Audit timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, default `now()` | Audit timestamp |

### 2.2 `public.budget_categories`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK, default `gen_random_uuid()` | Primary Key |
| `budget_id` | UUID | FK `budgets(id)` ON DELETE CASCADE | Associated budget |
| `category_key` | VARCHAR(64) | NOT NULL, btrim length >= 1 | Machine-readable slug |
| `name` | VARCHAR(160) | NOT NULL, btrim length >= 1 | Display title |
| `planned_amount` | NUMERIC(12, 2) | NOT NULL, CHECK (`planned_amount >= 0`) | Allocation limit |
| `sort_order` | INTEGER | NOT NULL, default 0 | Display priority |
| `is_deleted` | BOOLEAN | NOT NULL, default `false` | Soft-delete flag |

### 2.3 `public.expenses`
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK, default `gen_random_uuid()` | Primary Key |
| `event_id` | UUID | FK `events(id)` ON DELETE CASCADE | Associated event |
| `budget_category_id` | UUID | FK `budget_categories(id)` ON DELETE RESTRICT | Spending bucket |
| `vendor_id` | UUID | NULLABLE | Associated vendor (future) |
| `description` | VARCHAR(240) | NOT NULL | Expense notes |
| `amount` | NUMERIC(12, 2) | NOT NULL, CHECK (`amount > 0`) | Financial amount |
| `currency` | CHAR(3) | NOT NULL, CHECK (`currency ~ '^[A-Z]{3}$'`) | Currency code |
| `expense_date` | DATE | NOT NULL, default `current_date` | Date of transaction |
| `status` | TEXT | CHECK (`status in ('planned', 'committed', 'paid', 'cancelled')`) | Lifecycle status |
| `is_deleted` | BOOLEAN | NOT NULL, default `false` | Soft-delete flag |
| `created_by` | UUID | FK `profiles(user_id)` | Author |

## 3. Row Level Security Policies

| Table | Operation | Policy Name | Enforcement Condition |
| :--- | :--- | :--- | :--- |
| `budgets` | SELECT | `budgets_select` | `app.is_event_member(event_id)` |
| `budgets` | INSERT | `budgets_insert` | `app.is_event_member(event_id, array['owner', 'editor'])` |
| `budgets` | UPDATE | `budgets_update` | `app.is_event_member(event_id, array['owner', 'editor'])` |
| `budget_categories` | SELECT | `budget_categories_select` | `app.is_event_member(b.event_id)` |
| `budget_categories` | INSERT | `budget_categories_insert` | `app.is_event_member(b.event_id, array['owner', 'editor'])` |
| `budget_categories` | UPDATE | `budget_categories_update` | `app.is_event_member(b.event_id, array['owner', 'editor'])` |
| `budget_categories` | DELETE | `budget_categories_delete` | `app.is_event_member(b.event_id, array['owner', 'editor'])` |
| `expenses` | SELECT | `expenses_select` | `app.is_event_member(event_id)` |
| `expenses` | INSERT | `expenses_insert` | `created_by = app.current_user_id() AND app.is_event_member(event_id, array['owner', 'editor'])` |
| `expenses` | UPDATE | `expenses_update` | `app.is_event_member(event_id, array['owner', 'editor'])` |
| `task_dependencies` | DELETE | `task_dependencies_delete` | `app.is_event_member(t.event_id, array['owner', 'editor'])` |

## 4. Verification & Guardrail Compliance

1. **Reproducibility Test:** Migrations apply cleanly from scratch twice to identical schemas.
2. **No BYPASSRLS:** Confirmed via automated migration inspection script.
3. **No SECURITY DEFINER:** Confirmed via automated AST / regex scan.
4. **All Tables Covered:** Every table in the public schema has `relrowsecurity = true`.

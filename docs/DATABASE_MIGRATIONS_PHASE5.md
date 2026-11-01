# Database Migrations Documentation — Phase 5 (GiftCircle)

## 1. Migration Sequence

The Phase 5 migrations extend the canonical database schema with 5 new tables and 100% RLS coverage:

| Order | Migration File | Description |
|---|---|---|
| 17 | `supabase/migrations/20261101001700_giftcircle_schema.sql` | Gift registries, items, reservations, contributions, idempotency tables, and event revision triggers |
| 18 | `supabase/migrations/20261101001800_giftcircle_rls_and_grants.sql` | RLS enablement, least-privilege grants (zero DELETE), host policies, and capability-based public policies |

---

## 2. Table Schemas

### `public.gift_registries`
- `id` (uuid, primary key)
- `event_id` (uuid, unique, foreign key -> `events(id)` on delete cascade)
- `title` (text, not null)
- `welcome_message` (text)
- `delivery_address` (text)
- `allow_group_gifting` (boolean, not null, default true)
- `is_public` (boolean, not null, default true)
- `status` (text, not null, check in `('active', 'archived')`)
- `share_token_hash` (char(64), unique, SHA-256 hash)
- `revoked_at` (timestamptz)
- `expires_at` (timestamptz)
- `created_at` / `updated_at` (timestamptz, not null)

### `public.gift_items`
- `id` (uuid, primary key)
- `registry_id` (uuid, not null, foreign key -> `gift_registries(id)` on delete cascade)
- `name` (text, not null)
- `description` (text)
- `item_type` (text, not null, check in `('physical', 'experience', 'cash_fund')`)
- `gift_mode` (text, not null, check in `('individual', 'group')`)
- `target_amount` (numeric(12,2), check `target_amount is null or target_amount > 0`)
- `currency` (char(3), not null, default 'INR')
- `external_url` (text)
- `image_url` (text)
- `priority` (text, not null, default 'medium', check in `('high', 'medium', 'low')`)
- `sort_order` (integer, not null, default 0)
- `is_active` (boolean, not null, default true)
- `created_at` / `updated_at` (timestamptz, not null)

### `public.gift_reservations`
- `id` (uuid, primary key)
- `gift_item_id` (uuid, not null, foreign key -> `gift_items(id)` on delete cascade)
- `guest_alias` (text)
- `notes` (text)
- `status` (text, not null, default 'reserved', check in `('reserved', 'fulfilled', 'cancelled', 'expired')`)
- `cancellation_token_hash` (char(64), not null)
- `expires_at` (timestamptz)
- `created_at` / `updated_at` (timestamptz, not null)
- **Constraint**: `idx_unique_active_gift_reservation` partial index on `gift_item_id` where `status = 'reserved'`.

### `public.gift_contributions`
- `id` (uuid, primary key)
- `gift_item_id` (uuid, not null, foreign key -> `gift_items(id)` on delete cascade)
- `guest_alias` (text)
- `amount` (numeric(12,2), not null, check `amount > 0`)
- `currency` (char(3), not null, default 'INR')
- `status` (text, not null, default 'pledged', check in `('pledged', 'verified', 'cancelled')`)
- `idempotency_key` (text, not null)
- `verification_method` (text, check in `('offline_cash', 'upi_direct', 'bank_transfer', 'gift_card', 'other')`)
- `verification_notes` (text)
- `verified_at` (timestamptz)
- `created_at` / `updated_at` (timestamptz, not null)

### `public.idempotency_records`
- `id` (uuid, primary key)
- `scope` (text, not null)
- `idempotency_key` (text, not null)
- `request_hash` (text, not null)
- `response_code` (integer, not null)
- `response_body` (jsonb, not null)
- `created_at` (timestamptz, not null)
- **Constraint**: `unique (scope, idempotency_key)`

---

## 3. Grants & Security Invariants
- `GRANT SELECT, INSERT, UPDATE ON ALL TABLES TO utsavai_app;`
- Strictly **ZERO** `DELETE` table grants.
- Strictly **ZERO** `SECURITY DEFINER` procedures.
- Strictly **ZERO** `BYPASSRLS` roles.
- All 21 public tables in the database have `relrowsecurity = true`.

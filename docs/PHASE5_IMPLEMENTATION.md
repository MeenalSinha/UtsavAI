# Phase 5 Implementation Report — GiftCircle

## 1. Executive Summary

Phase 5 introduces **GiftCircle**, an intelligent wedding gift registry and group gifting system designed specifically for Indian and multicultural wedding celebrations. GiftCircle bridges couples and their wedding guests through a secure, account-free public registry interface, while providing hosts with comprehensive private wishlist management, group gifting coordination, and offline receipt reconciliation.

- **Status**: Completed & Verified
- **Scope**: Private host registry curation, public guest share link with cryptographic hash security, single-guest individual gift reservation with cancellation token, group gifting with row-locked atomic pledge capacity tracking, host offline reconciliation, and Shared Event Context extension.
- **Security & Integrity Invariants Preserved**:
  - Zero `DELETE` table grants for `utsavai_app` (soft updates and cancellation states only).
  - Zero `SECURITY DEFINER` functions in migrations.
  - Zero `BYPASSRLS` roles.
  - Raw share tokens are stored exclusively as SHA-256 cryptographic hashes (`share_token_hash`). Old links are immediately invalidated upon rotation or revocation.
  - Public guest transactions operate via dedicated session-scoped configuration (`app.share_token_hash`) with capability-based Row-Level Security policies.
  - No payment gateways, card collection, or UPI money holding: Pledges explicitly represent guest intent, and host confirmation represents offline receipt on celebration day.

---

## 2. Architecture & Database Design

### 2.1 Database Migrations
Two canonical migrations establish the GiftCircle schema and security foundation:

1. `20261101001700_giftcircle_schema.sql`:
   - `public.gift_registries`: Stores registry title, welcome note, delivery address, group gifting permissions, status, and `share_token_hash` (`char(64)`).
   - `public.gift_items`: Wishlist items with `item_type` (`physical`, `experience`, `cash_fund`), `gift_mode` (`individual`, `group`), `target_amount` (`NUMERIC(12,2)`), `currency`, `priority`, and soft-deactivation flag (`is_active`).
   - `public.gift_reservations`: Individual gift claims with `idx_unique_active_gift_reservation` partial unique index enforcing at most one active reservation per item (`status = 'reserved'`).
   - `public.gift_contributions`: Group gift pledges with guest alias, pledged amount, status (`pledged`, `verified`, `cancelled`), and host verification metadata.
   - `public.idempotency_records`: Transactional deduplication table storing request hash and response JSON to protect all guest reservation and contribution actions.
   - Trigger `touch_event_revision_on_gift_change` ensuring optimistic concurrency revision bump on the parent celebration event.

2. `20261101001800_giftcircle_rls_and_grants.sql`:
   - RLS strictly enabled on all 5 tables (`gift_registries`, `gift_items`, `gift_reservations`, `gift_contributions`, `idempotency_records`).
   - Restricted grants to `utsavai_app`: `SELECT, INSERT, UPDATE` only (strictly no `DELETE`).
   - Member-based RLS policies for host operations via `app.is_event_member()`.
   - Capability-based RLS policies for public guest operations via `app.current_share_token_hash()`.

---

## 3. Backend Implementation

- **Domain Model (`app/core/domain.py`)**: Added `Permission.GIFT_REGISTRY_READ`, `Permission.GIFT_REGISTRY_MANAGE`, and enums `GiftItemType`, `GiftMode`, `GiftItemPriority`, `GiftReservationStatus`, `GiftContributionStatus`, and `VerificationMethod`.
- **Database Connection Pool (`app/database/pool.py`)**: Added `public_transaction(share_token_hash, request_id)` context manager configuring `app.share_token_hash` transactionally.
- **Repository (`app/modules/gifts/repository.py`)**:
  - Atomic row locking via `lock_item_for_update(conn, item_id)` (`SELECT ... FOR UPDATE`).
  - Active reservation partial uniqueness and transactional expiry.
  - Deterministic accounting calculations (`pledged`, `verified`, and `remaining_amount`).
  - Idempotency storage and lookup.
- **Service (`app/modules/gifts/service.py`)**:
  - Secure random 32-byte URL-safe share token generation.
  - Deterministic SHA-256 token and cancellation secret hashing.
  - Concurrency control preventing over-pledging on group gifts.
  - Audit logging with `actor_type="public_guest"` and `actor_type="user"`.
- **REST APIs**:
  - Host endpoints mounted at `/api/v1/events/{event_id}/gift-registry`: items CRUD, reservations, contributions, share-link lifecycle, and overview summary.
  - Public guest endpoints mounted at `/api/v1/public/registries/{share_token}`: account-free registry viewing, individual reservation, reservation cancellation via secret code, and group gift pledging.
- **Shared Event Context (`app/modules/events/context.py`)**: Extended with `gift_summary` (`total_items`, `reserved_items`, `group_items`, `total_contributed`, `currency`).

---

## 4. Frontend Implementation

- **Types (`features/gifts/types/index.ts`)**: Full TypeScript definitions reflecting the generated OpenAPI 3.1 contract.
- **Service (`features/gifts/services/gift-service.ts`)**: Dual-mode client communicating through BFF for hosts and `/api/public` proxy for guests.
- **BFF Allow-list (`lib/bff/proxy.ts`)**: Host GiftCircle endpoints registered in strict method-validated route definitions.
- **Host Workspace (`(app)/events/[eventId]/giftcircle/page.tsx` & components)**:
  - Top metrics banner: total items, claimed/reserved, total pledged, and total verified.
  - Share Link modal with one-click copy, rotation, and revocation.
  - Tabbed interface: Wishlist items (with category and mode filters), Active Reservations (with host release action), and Group Pledges (with offline confirmation action).
  - Add/Edit Item modal supporting individual and group gifts with validation.
  - Offline receipt verification dialog.
- **Public Guest Page (`/g/[shareToken]/page.tsx` & components)**:
  - Warm, mobile-first, celebratory wedding aesthetic.
  - Financial transparency banner informing guests that gifts are settled offline directly with the hosts.
  - Individual gift reservation modal issuing a guest cancellation code.
  - Group gift pledge modal with remaining capacity enforcement.
  - Polite error states for expired or revoked links.
- **Navigation & Module Routing**: Unlocked `GiftCircle` in `config/modules.ts`, `config/routes.ts`, and `workspace-nav.tsx`. Phase 6 (Adaptive Planning) remains locked as "Coming soon".

---

## 5. Verification & Test Summary

- **Backend Unit Tests**: 102 passed, including `test_gift_calculations.py` (idempotency hashing, token security, Decimal capacity calculations).
- **Backend Lint & Types**: Ruff check clean, Ruff format clean, MyPy strict clean (75 source files).
- **Database Guardrails**: Zero `BYPASSRLS`, zero `SECURITY DEFINER`, all 21 tables secured with active RLS.
- **Frontend Test Suite**: 108 tests passed across 18 test files, including host workspace and public guest interactions.
- **Production Build**: Next.js production build compiled cleanly (`npm run build`).
- **OpenAPI Contract**: Schema exported and validated with zero discrepancies (`npm run contract`).

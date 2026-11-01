# Phase 4 Implementation Report — VendorConnect

## 1. Executive Summary

Phase 4 introduces **VendorConnect**, an integrated vendor management and quotation comparison module for UtsavAI. VendorConnect bridges celebration planning with commercial coordination by offering deterministic quotation evaluation, multi-vendor tracking, and seamless cross-module links to BudgetAI and Shared Event Context.

- **Status**: Completed & Verified
- **Scope**: Private event vendor tracking, deterministic quotation comparison, guest count parity checks, cross-event isolation with BudgetAI expenses.
- **Constraints Preserved**:
  - Zero `DELETE` table grants for `utsavai_app` (soft-archive only via `archived_at`).
  - Zero `SECURITY DEFINER` procedures in migrations.
  - Zero `BYPASSRLS` roles.
  - Strict composite foreign keys `(vendor_id, event_id)` preventing cross-event data leaks.
  - Objective comparison without fabricating artificial quality scores or assuming cheapest is best.

---

## 2. Architecture & Database Design

### 2.1 Database Migrations
Three migrations were introduced in canonical sequence:

1. `20261101001400_event_vendors_and_quotes.sql`:
   - `public.event_vendors`: Stores vendor name, category, contact person, phone, email, website URL, private host notes, engagement status, and soft-archive timestamp (`archived_at`). Includes composite unique constraint `unique (id, event_id)`.
   - `public.vendor_quotes`: Stores quoted monetary amount (`NUMERIC(12,2)`), currency, scope summary, validity deadline, private notes, and decision status (`received`, `shortlisted`, `accepted`, `rejected`, `expired`).
   - Trigger `touch_event_revision_on_vendor_change` ensuring optimistic concurrency tracking on parent events.

2. `20261101001500_phase4_rls_and_grants.sql`:
   - RLS enabled on `event_vendors` and `vendor_quotes`.
   - Granular least-privilege grants to `utsavai_app`: `SELECT, INSERT, UPDATE` only.
   - Member-based RLS policies verifying event participation through `event_memberships`.

3. `20261101001600_expense_vendor_relationship.sql`:
   - Adds composite foreign key `foreign key (vendor_id, event_id) references public.event_vendors (id, event_id) on delete set null` to `public.expenses`.
   - Guarantees an expense cannot reference a vendor belonging to another celebration.

---

## 3. Backend Implementation

- **Domain Model (`app/core/domain.py`)**: Added `Permission.VENDOR_READ`, `Permission.VENDOR_MANAGE`, `VendorStatus`, and `QuoteStatus`.
- **Repository (`app/modules/vendors/repository.py`)**: Handles CRUD, soft archiving, event quote listings, and metrics calculation.
- **Comparison Engine (`app/modules/vendors/comparison.py`)**:
  - Groups quotations by category.
  - Calculates min/max pricing range.
  - Detects missing critical information (validity deadline, contact details, short scope).
  - Extracts guest counts using regex (`(\d+)\s*guests?`) and flags capacity discrepancies across quotes in the same category.
  - Warns on extreme price variance (>2x difference).
- **Service (`app/modules/vendors/service.py`)**: Validates state transitions, maintains event revision increments, writes audit logs, and coordinates quotation acceptance with vendor booking.
- **REST Endpoints (`app/api/v1/vendors.py`)**:
  - `GET /api/v1/events/{event_id}/vendors`
  - `POST /api/v1/events/{event_id}/vendors`
  - `GET /api/v1/events/{event_id}/vendors/summary`
  - `GET /api/v1/events/{event_id}/vendors/{vendor_id}`
  - `PATCH /api/v1/events/{event_id}/vendors/{vendor_id}`
  - `DELETE /api/v1/events/{event_id}/vendors/{vendor_id}` (Soft archive)
  - `GET /api/v1/events/{event_id}/vendors/{vendor_id}/quotes`
  - `POST /api/v1/events/{event_id}/vendors/{vendor_id}/quotes`
  - `PATCH /api/v1/events/{event_id}/vendors/{vendor_id}/quotes/{quote_id}`
  - `GET /api/v1/events/{event_id}/vendor-quote-comparison`
- **Shared Event Context (`app/modules/events/context.py`)**: Added `vendor_summary` containing total vendors, category breakdowns, quotes count, and pending decisions.

---

## 4. Frontend Workspace (`apps/web`)

- **Route**: `/events/[eventId]/vendors`
- **Component Architecture**:
  - `VendorWorkspace`: Top metrics bar (Total, Contacted, Quoted, Shortlisted, Booked, Pending Decisions), category & status filter bars, tab navigation.
  - `VendorDetailDialog`: Overview, Quotations, and BudgetAI Associated Expenses tabs.
  - `VendorFormDialog`: Add/edit vendor with category autocomplete and validation.
  - `QuoteFormDialog`: Add/edit quote with scope guidelines and validity deadline.
  - `QuoteComparisonView`: Side-by-side category comparison cards with discrepancy warning banners.
- **Navigation**: Unlocked `vendorconnect` in `modules.ts`, `routes.ts`, and `workspace-nav.tsx`.

---

## 5. Verification & Test Metrics

- **Frontend Tests**: 17/17 test files passed (102/102 unit/component tests in Vitest).
- **TypeScript**: `tsc --noEmit` passed with 0 errors.
- **ESLint**: `eslint . --max-warnings 0` passed with 0 warnings.
- **Contract Verification**: `npm run contract` passed with 0 schema drift.
- **Next.js Production Build**: `next build` compiled all routes cleanly with dynamic server-rendering.
- **Backend Checks**:
  - Ruff lint & format: 0 errors across 95 files.
  - Mypy: 0 errors across 69 source files.
  - Unit tests: passed.
  - Migration & RLS guardrails: verified clean.
  - Secret scanner: 0 exposed keys, tokens, or credentials.

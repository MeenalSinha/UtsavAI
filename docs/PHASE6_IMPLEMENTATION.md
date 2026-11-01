# UtsavAI Phase 6 Implementation: Adaptive Planning Engine

**Version:** 1.0.0  
**Date:** 1 November 2026  
**Status:** Completed & Verified  

---

## 1. Executive Summary

Phase 6 introduces the **Adaptive Planning Engine**, an intelligent cross-module decision support and replanning system for UtsavAI. In real-world celebrations, changes never happen in isolation: shifting an event date ripples into task deadlines, vendor quotes, and registry expiration dates; increasing the guest count stresses catering budgets, table seating, and vendor capacities.

Rather than acting as an ungrounded chatbot or a passive dashboard, the Adaptive Planning Engine:
1. **Reads ground-truth PostgreSQL state** across all active celebration modules (Core Event, PlanAI, BudgetAI, TimelineAI, VendorConnect, and GiftCircle).
2. **Evaluates versioned, deterministic impact rules** with Decimal precision and zero hallucinations.
3. **Presents structured options and warnings** with severity classifications (`low`, `medium`, `high`, `critical`).
4. **Leverages Gemini for advisory explanations** and natural-language prompt interpretation, while remaining 100% operational when AI is offline.
5. **Enforces owner-only atomic proposal acceptance** inside an isolated PostgreSQL transaction, guaranteeing that all approved primary mutations and secondary mitigations apply simultaneously or roll back completely.

---

## 2. System Architecture

```text
                                  ┌────────────────────────┐
                                  │   Host / Planner UI    │
                                  │ (/events/[id]/adaptive)│
                                  └───────────┬────────────┘
                                              │ HTTP / JSON
                                              ▼
                                  ┌────────────────────────┐
                                  │  Next.js BFF / Proxy   │
                                  └───────────┬────────────┘
                                              │ Authorization & Forwarding
                                              ▼
                                  ┌────────────────────────┐
                                  │    FastAPI Backend     │
                                  │ (api/v1/adaptive.py)   │
                                  └───────────┬────────────┘
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    ▼                                                  ▼
     ┌────────────────────────────┐                    ┌────────────────────────────┐
     │  Adaptive Service Layer    │                    │   Advisory Gemini AI       │
     │  (modules/adaptive/service)│◄───────────────────┤   (Explains & Interprets)  │
     └──────────────┬─────────────┘                    └────────────────────────────┘
                    │
                    ▼
     ┌────────────────────────────┐
     │  Impact Analysis Engine    │
     │ (deterministic rule suite) │
     └──────────────┬─────────────┘
                    │
         ┌──────────┼──────────┬──────────┬──────────┬──────────┐
         ▼          ▼          ▼          ▼          ▼          ▼
    EventRules  BudgetRules  Timeline   VendorRules  GiftRules  FunctionRules
    (Capacity/  (Headroom/   (Deadline   (Quote      (Registry  (Ceremonies/
     Dates)      Committed)   Shifts)     Expiry)     Expiry)    Milestones)
                    │
                    ▼
     ┌────────────────────────────┐
     │   PostgreSQL Persistence   │
     │     (change_proposals)     │
     │   Row-level Locking (FOR   │
     │ UPDATE) & Atomic Rollback  │
     └────────────────────────────┘
```

---

## 3. Database Schema & Concurrency Design

### 3.1 Table Definition: `change_proposals`
Stored in `public.change_proposals` under strict Row-Level Security:
- `id` (UUID PK): Unique proposal identifier.
- `event_id` (UUID FK): References `events(id)` on delete cascade.
- `created_by` (UUID FK): References `profiles(user_id)`.
- `base_revision` (bigint): Event revision at proposal generation time.
- `request_text` (text): Host-facing description of change.
- `requested_changes` (JSONB): Strongly-typed, versioned change request.
- `impact_result` (JSONB): Deterministic calculation diffs, severity, warnings, and suggested option catalog.
- `ai_explanation` (text nullable): Advisory natural-language summary.
- `status` (text): Enum (`proposed`, `accepted`, `rejected`, `stale`, `expired`).
- `accepted_at` (timestamptz nullable): Timestamp of acceptance.
- `accepted_revision` (bigint nullable): Revision at which changes committed.
- `rules_version` (text): Version of deterministic rules engine (e.g. `1.0.0`).
- `schema_version` (int): Payload schema version (e.g. `1`).
- `created_at`, `updated_at` (timestamptz).

### 3.2 Concurrency & Stale Revision Guard
When an event requirement changes, the proposal records `base_revision`. When the owner submits acceptance:
1. `events` row is locked via `SELECT ... FOR UPDATE`.
2. Current revision is compared against `base_revision`.
3. If `event.revision != proposal.base_revision`, the proposal is transitioned to `stale` and rejected with `409 Conflict`.
4. If valid, changes commit and `events.revision` increments by exactly 1 for the whole transaction.
5. All other pending proposals for that event are transitioned to `stale`.

---

## 4. Cross-Module Impact Coverage

| Module | Evaluated Requirements | Potential Impacts Detected | Mitigations Generated |
|---|---|---|---|
| **Event / Planning** | Guest count, dates, location | Venue capacity exceeded, invalid date inversions, location travel friction | Scaling warnings, schedule diffs |
| **BudgetAI** | Total limit, guest scaling | Budget ceiling lower than committed expenses, negative projected headroom | `opt_flag_budget_for_review` |
| **TimelineAI** | Event dates, function archival | Deadlines outside event window, orphaned tasks from archived functions | `opt_reschedule_tasks` (shifts all task due dates) |
| **VendorConnect** | Date shifts, guest scaling | Quotes expired before revised dates, catering headcount mismatches | `opt_mark_vendor_quotes_review` |
| **GiftCircle** | Event end date shift | Public registry expiring before revised wedding end date | `opt_extend_gift_registry` |

---

## 5. Security & Least Privilege

1. **Role-Based Authorization:**
   - `owner`: Full permissions (`adaptive_plan.read`, `adaptive_plan.propose`, `adaptive_plan.manage`). Only owner can accept proposals.
   - `editor`: Can read and propose changes (`adaptive_plan.read`, `adaptive_plan.propose`). Cannot accept.
   - `viewer`: Read-only access (`adaptive_plan.read`). Cannot propose or accept.
2. **Database Grants:**
   - `GRANT SELECT, INSERT, UPDATE ON public.change_proposals TO utsavai_app;`
   - Strictly zero `DELETE` grants.
   - Zero `SECURITY DEFINER` procedures.
   - Zero `BYPASSRLS`.
3. **Audit Trail:**
   - Every proposal creation, rejection, and atomic acceptance appends an immutable record to `public.audit_logs`.

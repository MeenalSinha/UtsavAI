# UtsavAI — System Architecture

**Version:** 1.0  
**Date:** 31 October 2026  
**Architecture style:** Modular monolith with a single deployable FastAPI backend and a Next.js web application

## 1. Architecture goals

- Keep all domain data organized around a canonical event context.
- Make ordinary application operations deterministic and independent of Gemini availability.
- Isolate AI integration behind a provider adapter and schema-validated contracts.
- Enforce authorization at API and database layers.
- Keep GiftCircle's public, account-free guest experience separate from private event data.
- Support additional event categories through configuration/templates and flexible event functions.
- Avoid microservices, distributed transactions and message queues until scale or operational evidence requires them.

## 2. High-level system context

```text
┌────────────────────────────────────────────────────────────────┐
│                         Users / Browsers                        │
│      Host & collaborators                  GiftCircle guests    │
└──────────────────┬─────────────────────────────────┬───────────┘
                   │                                 │
                   ▼                                 ▼
┌────────────────────────────────────────────────────────────────┐
│              Next.js App Router + React + TypeScript             │
│  Host workspace UI | Public registry UI | Server-side BFF       │
│  Tailwind CSS + shadcn/ui | Supabase Auth session cookies        │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTPS / versioned REST API
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                      FastAPI Modular Monolith                    │
│                                                                  │
│  API / Auth middleware / Authorization / Pydantic contracts     │
│  ┌────────────┐ ┌───────────┐ ┌────────────┐ ┌───────────────┐  │
│  │ Event Core │ │ PlanAI    │ │ BudgetAI   │ │ TimelineAI    │  │
│  └────────────┘ └───────────┘ └────────────┘ └───────────────┘  │
│  ┌────────────┐ ┌───────────┐ ┌────────────┐ ┌───────────────┐  │
│  │ Vendor     │ │ GiftCircle│ │ Adaptive   │ │ Audit /       │  │
│  │ Connect    │ │           │ │ Planning   │ │ Observability │  │
│  └────────────┘ └───────────┘ └────────────┘ └───────────────┘  │
│                                                                  │
│  Domain services → repositories → transaction boundary           │
│  Gemini adapter (suggestion-only; no privileged tool execution)  │
└──────────────────┬───────────────────────────────┬───────────────┘
                   │                               │
                   ▼                               ▼
┌──────────────────────────────┐     ┌────────────────────────────┐
│ Supabase-managed PostgreSQL  │     │ Google Gemini API          │
│ Source of truth, RLS,        │     │ Structured candidate       │
│ constraints, indexes,        │     │ output; no direct DB or    │
│ transactions and audit log   │     │ payment/vendor operations  │
└──────────────────────────────┘     └────────────────────────────┘
```

## 3. Deployment units

### 3.1 Web application

- Next.js App Router, React and TypeScript.
- Tailwind CSS and shadcn/ui for consistent UI primitives.
- Server Components for initial authenticated page rendering where useful.
- Client Components for interactive forms, planning previews and registry actions.
- Supabase Auth SSR integration using secure, HTTP-only cookie-backed sessions and the PKCE flow.
- Next.js Route Handlers act as a same-origin Backend-for-Frontend (BFF) for browser requests. They validate the session, forward the user's access token to FastAPI and avoid exposing backend credentials.
- Public GiftCircle pages do not require a Supabase session.

The BFF is a thin transport/session layer only. Business rules remain in FastAPI so they are not duplicated between Next.js and Python.

### 3.2 Backend application

A single FastAPI deployment contains modules with explicit boundaries:

1. `identity`: token verification, profiles and event membership.
2. `events`: event lifecycle, preferences, event context and revision management.
3. `planning`: PlanAI prompt orchestration and proposal acceptance.
4. `budget`: categories, expenses, summaries and validation.
5. `timeline`: tasks, milestones and dependency graph validation.
6. `vendors`: event-scoped vendor records and quotations.
7. `gifts`: registries, public links, reservations, pledges and reconciliation.
8. `adaptive`: change proposals, impact rules and atomic acceptance.
9. `ai`: Gemini adapter, prompt templates, schemas, validation and usage telemetry.
10. `audit`: append-only domain audit records and request correlation.

Each module exposes application services and repository interfaces. Routers must not contain domain calculations or direct database business logic.

### 3.3 Data layer

- Supabase-managed PostgreSQL is the canonical data store.
- Supabase Auth is the identity provider; application profile rows reference `auth.users.id`.
- Use SQL migrations as the source of truth for tables, indexes, constraints, grants, policies and test fixtures.
- Use a server-only database connection with a dedicated non-superuser, `NOBYPASSRLS` runtime role. Do not use a superuser or unrestricted service-role credential for routine requests.
- After validating the Supabase JWT, FastAPI opens a transaction and sets request-scoped database context (for example `app.user_id`) with transaction-local settings. RLS policies use that context and event membership. Public GiftCircle requests first set a candidate token-hash context for an RLS-filtered exact-match registry lookup, then set the resolved registry-ID context.
- All context settings must be transaction-local and cleared on commit/rollback to prevent pooled-connection identity leakage.
- The backend is the only component with direct database credentials. The browser never receives a database password or privileged key.

This approach makes FastAPI the sole domain-write path and retains Postgres RLS as defense-in-depth. The exact connection/pool configuration must be proven in an integration test against the selected Supabase project before Phase 1 is considered complete.

## 4. Request and identity flow

### 4.1 Authenticated host request

1. User signs in through Supabase Auth.
2. Next.js stores/refreshes the session using secure server-side cookies.
3. Browser calls same-origin BFF Route Handler.
4. BFF validates the Supabase session and forwards the access token as a bearer token to FastAPI over HTTPS.
5. FastAPI verifies JWT signature, issuer, audience, expiry and subject; it does not trust a user ID from request JSON or headers.
6. Backend sets transaction-local database identity context and queries under the non-bypass runtime role.
7. API authorization checks that the user is an active event member with a role permitting the operation. RLS independently limits accessible rows.

### 4.2 Public GiftCircle request

1. Guest opens a registry URL containing a random bearer share token.
2. FastAPI hashes the token using the configured cryptographic hash and compares it with the stored token hash using constant-time comparison where application-level comparison is used.
3. Backend confirms the registry is active, not revoked and not expired.
4. Within a scoped transaction, it sets a transaction-local candidate token-hash context. The first registry lookup is RLS-filtered by exact equality with `gift_registries.share_token_hash` plus active/public/expiry checks; a non-match returns no row. After this lookup succeeds, the backend sets the resolved registry-ID context for item/reservation/contribution queries.
5. RLS and service-level allow-listing restrict the result to public registry fields and that registry's gift items.
6. Writes are limited to reservation or pledge operations with validation, rate limits, idempotency and audit metadata. Guest requests cannot query private event tables.

A public share token is a bearer capability. It must have high entropy, be revocable/rotatable, be stored hashed, and be redacted from application logs and analytics.

## 5. Shared event context

The event context is an application-level, permission-filtered data transfer object assembled on demand from the normalized source records. It is not a second mutable copy of the event.

Recommended context sections:

- `event`: event ID, type, title, start/end, timezone, location, currency, guest count and revision.
- `preferences`: style, traditions/cultural context supplied by the user, priorities and constraints.
- `functions`: function names, times, locations and notes.
- `budget_summary`: deterministic aggregate only; do not include unnecessary individual financial details in prompts.
- `timeline_summary`: milestones, incomplete tasks and deadlines.
- `vendor_summary`: vendor categories/statuses and approved quote summary when relevant.
- `gift_summary`: registry status and aggregate completion only when relevant.
- `permissions`: role and fields/modules the current actor may access.

Context builders should support module-specific projections. For example, a guest registry endpoint must not call the full event-context builder. Gemini receives only the minimum information required for the specific task.

## 6. Module boundaries and dependencies

| Module | Owns | May depend on | Must not own |
|---|---|---|---|
| Event Core | Events, functions, preferences, members, revision | Identity, repositories | Budget totals, gift payment status |
| PlanAI | Conversations, planning proposals, prompt contracts | Event context, AI adapter, task/function schemas | Direct mutation of domain records |
| BudgetAI | Budget, categories, expenses, calculations | Event Core, AI suggestions | AI-derived authoritative totals |
| TimelineAI | Tasks, dependencies, schedule validation | Event Core, PlanAI proposals | Unvalidated AI schedules |
| VendorConnect | Event vendors and quotes | Event Core, Budget summary (read-only) | External vendor verification/booking APIs in MVP |
| GiftCircle | Registry, items, reservations, pledges | Event Core, audit | Guest access to private event records; payment processing |
| Adaptive | Change proposals, impact rules and application orchestration | All modules through published service interfaces | Duplicated source-of-truth data |
| AI adapter | Gemini requests, schema validation, usage data | Configured model endpoint | Database credentials or privileged business operations |

Circular imports/dependencies are prohibited. Adaptive Planning orchestrates module services; lower-level modules must not import Adaptive Planning.

## 7. Adaptive Planning design

Use an explicit dependency map, not open-ended agent reasoning, to identify impact:

- Guest count → catering assumptions, guest-related budget categories, venue/capacity tasks and possibly gift recommendations.
- Event date/time → function schedules, task due dates, vendor quote validity and reminder dates.
- Total budget → category allocation checks and cost-saving suggestions; it does not silently modify paid expenses.
- Function added/removed → task proposals, schedule view and related planning notes.
- Location change → venue/vendor shortlist review and travel-related planning tasks (not external booking).

The preview service returns `base_revision`, `affected_modules`, `affected_records`, `warnings` and `proposed_operations`. Each operation is typed and allow-listed. Acceptance revalidates the operations and applies them in one transaction. Every material mutation represented in the shared planning context advances the event revision; a stale base revision returns 409.

## 8. AI integration boundary

- One `GeminiClient` adapter is the only module allowed to call Google Gemini.
- Model name, API key, temperature, timeout, retry policy and token ceiling are configuration, not hard-coded values.
- Use JSON structured output with a versioned response schema, then validate using Pydantic models and domain validators.
- A valid schema does not make content true. Dates, references, money, IDs and constraints are checked against database/application state.
- AI has no direct SQL, browser, shell, payment or vendor-booking tools.
- AI responses are stored as proposals/messages with prompt and schema versions; selected proposals are mapped to typed commands and applied only after user confirmation.
- Add bounded retries for transient provider errors and schema repair. Do not loop indefinitely.
- Track model, prompt version, token/usage metadata, latency and validation outcome without logging sensitive prompt content by default.

## 9. API and communication conventions

- REST API prefix: `/api/v1`.
- JSON request/response bodies; OpenAPI generated by FastAPI.
- Bearer JWT required for private endpoints; public GiftCircle endpoints use a share token.
- Use UUIDs for public/internal resource identifiers; public access still requires the registry capability token.
- Use idempotency keys on operations that create reservations, pledges, expenses or accept change proposals.
- Use `If-Match`/revision preconditions for updates to event-level state.
- Standard error envelope and request ID on all responses.
- Pagination for list endpoints; predictable sorting.

## 10. Reliability, performance and scaling

- Ordinary application operations must not call Gemini unless the user explicitly requests an AI feature.
- Add request timeouts and bounded retries around Gemini; retry only safe/idempotent generation requests.
- Use database transactions for reservations, pledges, budget mutations and adaptive acceptance.
- Use indexes for event scoping, membership policies, foreign keys, due-date queries and registry lookups.
- Cache only non-sensitive, non-authoritative information. Do not cache permission decisions across sessions or public token revocation state for long periods.
- Add rate limits to AI generation and public registry endpoints.
- Start with a single FastAPI service and managed Postgres. Scale vertically and tune database queries before considering separate services.
- Background workers/scheduled jobs are deferred until reminders, expiry cleanup or payment webhooks require them.

## 11. Observability

Capture:

- Structured request logs with correlation ID, route, status, latency and actor ID where authenticated.
- Domain counters for event creation, task generation, change proposals, reservations, pledges and reconciliation.
- Gemini request latency, model, input/output token usage where exposed, provider errors and schema-validation outcomes.
- Database slow-query metrics and transaction conflicts.
- Public endpoint rate-limit events and invalid/revoked token attempts.

Never log access tokens, raw registry share tokens, guest cancellation secrets, API keys, payment credentials or full personal event context. Configure log retention and redaction.

## 12. Architecture decision records

| ADR | Decision | Rationale |
|---|---|---|
| ADR-001 | Modular monolith | One deployable backend is simpler to test and operate at MVP scale. |
| ADR-002 | PostgreSQL is source of truth | Relational constraints and transactions fit budgets, tasks, membership and registry state. |
| ADR-003 | FastAPI owns domain writes | One authoritative implementation of business rules and calculations. |
| ADR-004 | AI proposes; backend validates and commits | Prevents hallucinated totals or unauthorized actions. |
| ADR-005 | Public GiftCircle uses high-entropy capability token | Allows guest access without accounts while preserving privacy controls. |
| ADR-006 | Generic event core, wedding-first templates | Supports future categories without category-specific database redesign. |
| ADR-007 | No payment processing in MVP | Avoids premature financial, compliance and dispute-handling complexity. |

## 13. External technical references

- [Next.js App Router Route Handlers](https://nextjs.org/docs/app/getting-started/route-handlers)
- [Supabase Auth server-side rendering](https://supabase.com/docs/guides/auth/server-side)
- [Supabase Auth with Next.js](https://supabase.com/docs/guides/auth/quickstarts/nextjs)
- [Supabase PostgreSQL Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)

---

## Phase 1 Implementation Notes

The implementation follows this document. Concrete choices:

* Monorepo: `apps/web` (Next.js 15, React 19), `apps/api` (FastAPI, modular monolith with
  `identity`, `events`, `audit`), `supabase/migrations`.
* Layering in the API: thin routers, services own the transaction and authorization, repositories hold
  parameterised SQL. A service opens exactly one identity-scoped transaction per request; routers never touch the database.
* Synchronous psycopg 3 connection pool with prepared statements disabled (transaction-pooler safe).
* The frontend performs all authentication on the server; the browser reaches FastAPI only through
  the BFF. Server Components call FastAPI directly with the validated access token.
* Domain rules (categories, statuses, roles, permissions, limits) live in `app/core/domain.py` and are
  published through `GET /api/v1/meta`.

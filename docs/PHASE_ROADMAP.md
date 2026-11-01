# UtsavAI — Phase Roadmap and Phase 0 Exit Review

**Version:** 1.0  
**Date:** 31 October 2026

## 1. Development roadmap

The project will be built in eight implementation phases after this Phase 0 blueprint. Each phase ends with tests, an implementation audit, documentation updates and a Git commit/PR. Do not start a later phase while the current phase has failing critical acceptance tests.

| Phase | Name | Scope | Exit gate | Status |
|---|---|---|---|---|
| **0** | Requirements & Architecture | PRD, MVP boundaries, personas, workflows, modular architecture, schema, APIs, AI, security and testing baseline | All ten documents reviewed for consistency; no application feature code created. | **COMPLETED** |
| **1** | Project Foundation | Repository setup, Next.js shell, FastAPI shell, environment config, Supabase Auth, PostgreSQL migrations, RLS/runtime identity context, CI | User can authenticate and create/reopen a private event; cross-user/event isolation tests pass. | **COMPLETED** |
| **2** | Core Event Planning / PlanAI | Event settings/preferences/functions, shared event context, conversation UI, Gemini adapter, structured plan proposal and review/acceptance | User can generate a validated wedding plan and accept selected proposals; AI failure leaves CRUD usable. | **COMPLETED** |
| **3** | Budget & Timeline Intelligence | Budget/category/expense operations, deterministic summaries, task CRUD, task dependencies, schedule proposals | Financial totals reconcile exactly; dependency cycles are rejected; generated plans remain proposals until accepted. | **COMPLETED** |
| **4** | VendorConnect | Event-scoped vendors, quotations, comparison and booking-status tracking | Quotes can be entered/compared without implying external verification or payment. | Planned |
| **5** | GiftCircle | Registry management, token generation/revocation, public registry UI, account-free reservation and group pledges, host reconciliation | Public no-login journey passes; concurrent duplicate reservations and over-pledges are prevented; no money is collected. | Planned |
| **6** | Adaptive Planning Engine | Typed change requests, deterministic impact map, AI explanations/options, preview, approval and atomic revision-checked application | A material requirement change previews impacts across modules and applies only after owner approval. | Planned |
| **7** | Finalization & Deployment | Full testing, accessibility, threat review, observability, demo fixtures, documentation, deployment and final audit | Release gates in PRD, security and testing docs all pass. | Planned |

## 2. Phase working rules

For every implementation phase:

1. Read the relevant Phase 0 documents before coding.
2. Convert phase scope into small tasks with acceptance criteria.
3. Implement the backend/domain behavior before polishing the UI for stateful workflows.
4. Keep fixtures and demo data synthetic and isolated from production.
5. Add unit, integration and relevant end-to-end tests alongside the feature.
6. Run lint, type checks, tests, build and security checks.
7. Audit for incomplete stubs, hard-coded data, fake AI output, unsafe secrets and broken routes.
8. Update docs/contracts if implementation decisions change; do not leave documentation silently stale.
9. Commit the completed phase and record known limitations before proceeding.

## 3. Demo path for the final MVP

A single coherent scenario should demonstrate the full value proposition:

1. Host signs in and creates an Indian wedding with date, location, guest count and budget.
2. PlanAI produces a structured draft with functions, tasks and transparent assumptions.
3. Host reviews and accepts selected functions/tasks.
4. Budget view shows categories, expenses, exact totals and warnings.
5. Timeline view shows task status and dependencies.
6. VendorConnect compares manually entered quotations.
7. GiftCircle publishes a shareable registry; a guest opens it on a mobile browser without signing in.
8. Guest reserves an individual item and pledges toward a group gift. UI explains that no payment is collected.
9. Host manually confirms an offline contribution and sees the confirmation method.
10. Host increases the guest count while holding the budget ceiling; Adaptive Planning previews affected areas and applies only after approval.

Use an isolated demo environment and clearly labelled synthetic data. Do not use real couple/guest contact data in public demo recordings.

## 4. Dependencies and sequencing

- Phase 1 must establish the authentication, authorization, database transaction and RLS model before any private module is implemented.
- Phase 2 establishes the shared event-context contract and AI validation pipeline used by later AI-assisted modules.
- Phase 3 provides authoritative budget/timeline services that Adaptive Planning consumes.
- Phase 4 provides vendor records and quote state that Adaptive Planning can flag for review.
- Phase 5 depends on event core, public capability security, idempotency and database transaction tests.
- Phase 6 must orchestrate stable service interfaces from Phases 2–5; do not duplicate their logic.
- Phase 7 is not a substitute for tests during earlier phases; it performs full-system verification and hardening.

## 5. Explicit implementation guardrails

- Do not introduce microservices for MVP.
- Do not let Gemini calculate authoritative budget values or mutate database state.
- Do not expose Supabase service secrets, database credentials or Gemini keys to the browser.
- Do not enable anonymous direct database access to all GiftCircle tables; public access must be token-scoped and field-limited.
- Do not call a pledged contribution a payment or payment-provider verification.
- Do not display vendor availability/verification claims unsupported by the data.
- Do not implement payment processing before the payment-state, webhook, refund/dispute and provider design is approved.
- Do not make birthdays/community events a blocking requirement for the wedding MVP; preserve generic event design and add categories later.

## 6. Phase 0 deliverables checklist

- [x] `/docs/PRD.md`
- [x] `/docs/MVP_SCOPE.md`
- [x] `/docs/USER_FLOWS.md`
- [x] `/docs/ARCHITECTURE.md`
- [x] `/docs/DATABASE_SCHEMA.md`
- [x] `/docs/API_SPECIFICATION.md`
- [x] `/docs/AI_DESIGN.md`
- [x] `/docs/SECURITY.md`
- [x] `/docs/TESTING_STRATEGY.md`
- [x] `/docs/PHASE_ROADMAP.md`

## 7. Final documentation consistency audit

The ten documents were cross-checked against the following architecture and product invariants:

| Audit item | Result | Consistency rule |
|---|---|---|
| MVP scope vs roadmap | Pass | Wedding-first MVP; phases follow the agreed sequence; future event categories remain extensible. |
| Shared event context | Pass | Event Core is canonical; modules consume normalized records through context/service interfaces. |
| Modular monolith | Pass | One FastAPI deployment; no unnecessary microservices, queues or autonomous agent services. |
| AI authority | Pass | Gemini proposes/explains; Pydantic and domain rules validate; user confirms; backend commits. |
| Budget correctness | Pass | Decimal values and backend-calculated totals; AI cannot authoritatively calculate financials. |
| Timeline correctness | Pass | Backend validates timezone/date and dependency graph; cycles are rejected. |
| Vendor claims | Pass | MVP vendor data is user-entered; comparison does not imply verification or real-time availability. |
| Public GiftCircle access | Pass | Guests do not need accounts; capability token is high entropy, stored hashed and revocable; public DTO is allow-listed. |
| Reservation concurrency | Pass | Atomic operation/unique active reservation rule and concurrency test are required. |
| Group gift semantics | Pass | Pledges are not payments; host confirmation provenance is stored; over-pledging is blocked atomically. |
| Adaptive planning | Pass | Preview is side-effect free; acceptance is explicit, transactional and revision-checked. |
| Authorization | Pass | JWT validation, event membership, role checks and RLS are required. |
| Testing | Pass | Unit, API, DB/RLS, concurrency, AI, E2E, accessibility and security tests are defined. |

### Deliberate implementation notes / limitations

1. The database design specifies the RLS identity context as a transaction-local application setting after FastAPI has verified the Supabase JWT. Public token lookup uses a candidate token-hash context checked by RLS before resolving the registry ID. These are design choices that must be validated against the actual Supabase connection/pool configuration in Phase 1; tests must prove no context leakage. The runtime role must be non-superuser and `NOBYPASSRLS`.
2. PostgreSQL partial indexes cannot express an active-reservation predicate using the volatile current time. Expiry, if enabled, must be handled transactionally by application logic or a database routine before enforcing the unique active reservation constraint.
3. The MVP uses host manual confirmation for offline gift receipt. It must not describe that as provider-verified payment. Payment-provider webhooks are future scope.
4. Full collaborator invitation UX is marked Should; schema and authorization roles are defined now, but the first release may prioritize owner-only journeys if time is constrained.
5. Event deletion, guest-data retention and support/dispute policy require a final product/legal decision before public launch.

**Phase 0 status: DOCUMENTATION BASELINE COMPLETE.** This package defines the requirements and implementation contracts. It does not create application features and does not authorize starting Phase 1 automatically.

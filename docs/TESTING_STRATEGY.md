# UtsavAI — Testing Strategy and Acceptance Criteria

**Version:** 1.0  
**Date:** 31 October 2026

## 1. Testing goals

- Prove correctness of deterministic planning operations and financial calculations.
- Prove private event isolation and role-based access control.
- Prove public GiftCircle supports guests without accounts while protecting private data.
- Prove concurrency safety for reservations, contributions and adaptive updates.
- Prove AI output is structured, validated and never applied without user approval.
- Prove core workflows are accessible, responsive and understandable.

## 2. Test pyramid

| Level | Focus | Tools (recommended) |
|---|---|---|
| Unit | Domain rules, validators, budget math, dependency graph, impact rules, token helpers | pytest, Pydantic test helpers |
| Component | React components, forms, client state and error handling | Vitest, React Testing Library |
| API contract | FastAPI request/response schema, auth, errors and OpenAPI stability | pytest, FastAPI TestClient/httpx |
| Database integration | Constraints, RLS, migrations, transactions, custom request context and concurrency | Disposable Supabase/Postgres test project, pytest, SQL tests/pgTAP where available |
| AI contract/evaluation | Schema-validity, domain-validity, prompt injection, groundedness and regressions | Recorded fixtures, mocked provider, curated Gemini eval set |
| End-to-end | Host and guest critical journeys | Playwright |
| Accessibility | Keyboard, semantic labels, focus, contrast and screen-reader basics | axe-core, Playwright, manual keyboard review |
| Security/performance | IDOR, rate limits, dependency scans, latency, abusive public traffic | Static/dependency scanning, OWASP test cases, load test tool |

## 3. Unit test requirements

### Event Core

- Event date range validation and timezone parsing.
- Supported event category validation and wedding template defaults.
- Event revision increment and stale-revision behavior.
- Role capability matrix.
- Cross-event reference rejection.

### BudgetAI

- Exact decimal addition/subtraction and category totals.
- Planned vs committed vs paid vs cancelled semantics.
- Remaining budget and overspend warnings.
- Zero, negative, malformed and excessive-precision amounts rejected where invalid.
- Currency mismatch rejected.
- AI-suggested numbers never replace deterministic summaries.

### TimelineAI

- Task status transitions.
- Due-date handling in event timezone, including daylight-saving edge cases for future markets.
- Self-dependency and cross-event dependency rejected.
- Direct and indirect dependency cycles rejected.
- Invalid/non-member assignee rejected.

### VendorConnect

- Quote amount/currency validation.
- Expired quote state/label rules.
- Quote comparisons preserve scope/date context and do not rank solely on price.

### GiftCircle

- Only active individual gift can be reserved.
- Group gift capacity uses active pledges and verified contributions according to the approved aggregation rule.
- Withdrawn/refunded contributions are excluded from active totals.
- Pledged contributions are not considered received/verified.
- Host manual confirmation records actor, timestamp and method.
- Invalid/revoked/expired token rejected.
- Public DTO excludes private fields.
- Idempotency key replay returns the original operation result; same key with different request returns 409.

### Adaptive Planning

- Every change type maps to the expected affected modules/records.
- Preview has no side effects.
- Invalid options and arbitrary client operations are rejected.
- Acceptance increments revision once and commits atomically.
- Stale base revision returns 409.
- Rollback leaves no partial changes if any validation/write fails.

## 4. API and authorization tests

For every private event endpoint, cover:

1. No token → 401.
2. Invalid/expired token → 401.
3. Valid user not a member → 404 or 403 according to the endpoint's resource-hiding policy.
4. Active viewer → read permitted, mutation denied.
5. Active editor → only permitted editor mutations succeed.
6. Owner → owner-only operations succeed.
7. Nested resource ID from another event → denied without data leakage.
8. Stale `If-Match`/revision → 409.

For public GiftCircle endpoints, cover:

1. Valid registry link returns only public-safe information.
2. Invalid, revoked, expired or private link returns generic unavailable response.
3. Public user cannot access private event, budget, vendor, audit or member endpoints.
4. Guest action is rate limited and idempotent.
5. Revoking a token invalidates future reads/writes promptly.

## 5. Database integration and concurrency tests

Run against a real disposable PostgreSQL/Supabase test environment, not only SQLite mocks.

- Run all migrations from an empty database.
- Run schema/grant/RLS policy tests for every application table.
- Validate foreign keys, check constraints, partial unique indexes and trigger behavior.
- Verify request identity context is transaction-local and does not leak across a pooled connection after commit, rollback or exception.
- **Reservation race:** issue at least 20 concurrent requests for one individual gift; exactly one active reservation succeeds; other requests receive deterministic conflict/idempotent responses.
- **Group pledge race:** issue concurrent pledges whose combined amount exceeds the target; accepted active pledges never exceed the target.
- **Idempotency race:** repeated requests with the same key create one logical operation.
- **Adaptive race:** two proposals based on the same revision; after one is accepted, the other is rejected as stale.
- **Transaction rollback:** induce a failing dependent write and verify no partial domain mutation or audit inconsistency remains.

## 6. AI tests

### 6.1 Deterministic contract tests

- Mock Gemini provider with valid, invalid, malformed, truncated and timeout responses.
- Confirm invalid JSON or Pydantic failures are never persisted as accepted domain changes.
- Confirm bounded retry/repair behavior and graceful provider errors.
- Confirm model output cannot set role, payment status, owner ID, event ID or authorization scope.
- Confirm every proposal's `base_revision` is recorded and checked on acceptance.

### 6.2 Evaluation set

Build a small, version-controlled synthetic dataset containing at least:

- 10 ordinary wedding planning requests with varied guest counts/budgets/functions.
- 5 incomplete or ambiguous requests that should trigger follow-up questions.
- 5 conflicting-constraint requests that should state trade-offs rather than claim impossible plans are feasible.
- 5 budget advice cases where deterministic totals must remain unchanged.
- 5 schedule cases with invalid, past or conflicting dates.
- 5 vendor cases where live availability/pricing is not supplied and must not be invented.
- 5 GiftCircle cases that try to mark an unpaid pledge as paid or expose another guest's details.
- 10 prompt-injection/adversarial requests.

Measure schema-valid rate, domain-valid rate, unsupported-fact rate, follow-up-question quality, user usefulness rating, latency and token/cost use. Establish baseline thresholds after the first model evaluation and keep regression cases fixed across model changes.

## 7. Frontend and accessibility tests

- Forms show inline errors and retain valid user input after validation failures.
- Primary flows are keyboard navigable; focus order is logical and focus is visible.
- Dialogs trap/restore focus appropriately.
- Buttons and inputs have accessible names; status is not represented by color alone.
- AI generated text is safely rendered and long content does not break layouts.
- Public registry is usable at 320 px viewport width and common mobile viewport sizes.
- Color contrast, heading hierarchy, landmark regions and labels meet WCAG 2.2 AA target.
- Test loading, empty, error, success and disabled states, not only happy paths.

## 8. End-to-end critical journeys

### Journey A — Host planning

Sign up/sign in → create wedding → enter preferences → generate PlanAI proposal → review and accept tasks/functions → set budget → record expense → check summary → add vendor and quote → compare quotes.

### Journey B — Guest gifting

Open public link in private browser/no login → view registry → reserve one individual item → confirm reserved state → attempt duplicate reservation → receive conflict → submit group pledge → see explicit “pledge recorded; no money collected” message.

### Journey C — Host gift reconciliation

Sign in as owner → view guest reservation and pledge → mark offline pledge as host-confirmed → verify audit record and provenance → confirm public page exposes only approved aggregate/status.

### Journey D — Adaptive planning

Change guest count with current revision → preview affected budget/timeline/vendor sections → verify no data changed → accept → verify accepted changes/revision → submit stale proposal → verify 409 and no partial state.

## 9. Non-functional tests

- Load test ordinary event reads/writes and public registry reads at expected MVP concurrency.
- Validate p95 target below 500 ms for ordinary backend CRUD/summary operations under representative test load, excluding client/network latency and Gemini generation.
- Measure Gemini latency, timeout rate and provider errors separately.
- Test rate limits, large payload rejection and invalid-token floods.
- Run dependency vulnerability and static analysis checks in CI.
- Verify secret scanning catches accidental committed keys.
- Verify logs redact bearer tokens, share tokens and guest cancellation tokens.

## 10. CI quality gates

A pull request should pass:

1. Formatting, linting and static type checks (Python and TypeScript).
2. Python unit tests and frontend component tests.
3. Database migration validation and RLS policy tests for database-affecting changes.
4. API/OpenAPI contract tests.
5. Relevant integration and concurrency tests.
6. AI contract fixtures for AI-affecting changes.
7. Build checks for frontend and backend.
8. Dependency/security scan and secret scan.

Suggested initial coverage targets: at least 80% line coverage for domain services and validators, and explicit branch tests for authorization, concurrency and financial state transitions. Coverage percentage never replaces critical-path test requirements.

## 11. Acceptance criteria by module

| Module | Release acceptance |
|---|---|
| Event Core | Owner isolation, role checks, revisions and event-context contract pass. |
| PlanAI | Valid structured proposal generated; invalid output rejected; nothing persists until user accepts. |
| BudgetAI | Backend totals reconcile exactly; expenses and categories are event-scoped; AI cannot alter totals. |
| TimelineAI | Task creation/status/dependencies work; cycles and cross-event links rejected. |
| VendorConnect | Vendor/quote CRUD and comparison work; no false external verification claims. |
| GiftCircle | Public no-login flow works; link can be revoked; duplicate reservation and group over-pledge races pass; pledge/confirmation states are distinct. |
| Adaptive | Preview side-effect free; accepted updates atomic and revision-checked; stale updates fail safely. |
| Accessibility | Host and guest journeys pass automated checks and manual keyboard review. |
| Security | No unresolved critical/high issues; RLS, auth, logging redaction and public endpoint controls pass. |

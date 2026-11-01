# UtsavAI Phase 1: Implementation Report

Date: 2026-11-01. Scope: Phase 1 (Project Foundation) only. Nothing from Phase 2 or later was started.

## 1. Implementation summary

Phase 1 delivers a working, tested foundation: a Next.js 15 web application with server-side Supabase
authentication, a FastAPI modular monolith that verifies Supabase JWTs and applies a transaction-local
database identity, PostgreSQL migrations with row-level security and least-privilege grants, private
event management (create, list, open, edit with optimistic concurrency, archive), a same-origin BFF,
automated tests at every layer, and CI.

**Status in one paragraph.** Everything that can be executed without a Supabase project was executed
and passes (136 backend tests against a real PostgreSQL 16 with real RLS, 83 frontend tests, lint, types,
production build, a running API and web server smoke test). Gates that require a live Supabase project
(real sign-up and sign-in, applying migrations to Supabase, the live pooler verification, and the browser
E2E scenario) are reported as BLOCKED, with exact steps and a ready-made verification script in Section 16.
They are not reported as passed.

## 2. Repository structure

See `README.md` for the annotated tree. 177 files: `apps/web`, `apps/api`, `supabase`, `scripts`,
`docs`, `.github/workflows`.

## 3. Technologies and dependencies

| Area | Choice (locked) |
| --- | --- |
| Frontend | Next.js 15.5, React 19, TypeScript 5.9 strict, Tailwind 3.4, Radix primitives (shadcn-style components), sonner, zod 4 |
| Auth client | `@supabase/ssr` with `getAll`/`setAll` cookies (no deprecated helpers) |
| Backend | Python 3.12, FastAPI, Pydantic 2 and pydantic-settings, psycopg 3 with connection pool, PyJWT |
| Database | PostgreSQL (Supabase-managed in deployment; PostgreSQL 16 used for local verification) |
| Quality | ruff, mypy strict, pytest, vitest, Testing Library, Playwright, eslint, tsc |
| Locking | `apps/api/uv.lock`, `apps/web/package-lock.json`, exact-pinned direct npm dependencies |

Gemini is not installed or referenced.

## 4. Features implemented

* Landing page, registration, sign-in, forgot password, reset password, email callback, sign-out.
* Session persistence and refresh in middleware; protected `/dashboard`, `/events`, `/events/new`, `/events/[id]`, `/profile`.
* Dashboard with personalised welcome, upcoming events from the API, empty state, quick navigation.
* Event creation form (all required fields, client validation, server error mapping, loading states, time zone aware).
* Event workspace with saved details, Overview, in-place editing, archive with confirmation, and clearly disabled
  PlanAI, BudgetAI, TimelineAI, VendorConnect and GiftCircle navigation.
* My Events list with Active and Archived views and pagination. Profile page (display name, locale, time zone).
* Global layout, light theme in burgundy and warm neutrals, toasts, skeleton loading, error boundaries, not-found page,
  skip link, keyboard and screen-reader friendly forms.

## 5. Database migrations created

Six files in `supabase/migrations/` (details in `docs/DATABASE_SETUP.md`): foundation, profiles, events, event_members,
audit_logs, rls_and_grants. Applied from scratch twice in verification to identical schemas.

## 6. API endpoints implemented

`GET /api/v1/health`, `GET /api/v1/health/ready`, `GET /api/v1/meta`, `GET|PATCH /api/v1/me`,
`POST|GET /api/v1/events`, `GET|PATCH|DELETE /api/v1/events/{event_id}`. Browser access via `/api/bff/me`,
`/api/bff/events`, `/api/bff/events/{id}`.

## 7. Authentication architecture

See `docs/AUTHENTICATION_SETUP.md`. Supabase Auth, server-only session handling, HTTP-only cookies, token forwarded by
the BFF, JWT verified by FastAPI against the project JWKS.

## 8. RLS and authorization implementation

Two independent layers. Service layer: role permission matrix (`owner`, `editor`, `viewer`) in `app/core/domain.py`.
Database layer: RLS policies keyed to `app.current_user_id()`, a dedicated `utsavai_app` role with NOSUPERUSER and
NOBYPASSRLS, column-level grants, no DELETE, deferred owner-membership invariant, trigger-enforced revision and
archive rules. Details and policy table in `docs/DATABASE_SETUP.md`.

## 9. Security measures

JWT validation (algorithm allow-list, issuer, audience, expiry, role, UUID subject); identity never taken from bodies or
headers (`extra=forbid`, tested); transaction-local identity with pool reset and startup role check; parameterised SQL only
(identifiers allow-listed); BFF origin check and route allow-list; HTTP-only Secure SameSite cookies; validated redirects;
security headers on both services; request size limits; structured logs without credentials; generic auth errors to prevent
account enumeration; production configuration validation (https, SSL, explicit CORS, no privileged DB user); dependency audits;
secret scan; `npm audit` high-severity findings fixed (zod upgraded, nested PostCSS overridden) leaving 0 production vulnerabilities.

## 10. Test cases executed

| Suite | Count | Scope |
| --- | --- | --- |
| Backend unit | 72 | config, JWT, schemas, domain rules, preconditions, cursors, API behaviour without SQL, OpenAPI validity |
| Backend integration | 64 | migrations, constraints, triggers, grants, RLS policies, pool identity isolation, event and profile APIs, role matrix, archive rules, two-user workflow |
| Frontend | 83 | env validation, route protection, redirects, datetime, form schemas, auth forms, event form, archive dialog, event list and workspace, profile, BFF proxy, API client, cookies, contract |

## 11. Actual test results (executed 2026-11-01)

```text
apps/api   ruff check                : All checks passed
apps/api   ruff format --check       : 51 files already formatted
apps/api   mypy (strict)             : Success, no issues in 36 source files
apps/api   pytest                    : 136 passed
apps/web   eslint --max-warnings 0   : clean
apps/web   tsc --noEmit              : clean
apps/web   vitest                    : 11 files, 83 tests passed
apps/web   contract check            : passed
apps/web   next build                : compiled, 13 routes + middleware
scripts    scan_secrets.sh           : clean
npm audit --omit=dev                 : 0 vulnerabilities
pip-audit (locked prod deps)         : No known vulnerabilities found
migrations x2 from scratch           : identical schemas (apart from pg_dump random tokens)
```

Runtime smoke test with the built applications: landing, sign-in, sign-up and forgot-password return 200; `/dashboard`,
`/events`, `/events/new`, `/events/{id}` and `/profile` return 307 to `/sign-in?next=...`; BFF without a session returns a 401 envelope;
cross-origin BFF mutation returns 403; the real API server returned `ready` from a database round trip, `meta`, and 401 without a token;
security headers present.

## 12. CI status

`.github/workflows/ci.yml` defines six jobs (backend, database, frontend, openapi, secrets, optional e2e). Each command was
executed locally with identical arguments. The workflow has **not yet run on GitHub Actions** because no repository was available
in this environment. Status: PARTIAL (see Section 17).

## 13. Environment variables required

Full list in `.env.example` and `docs/DEVELOPMENT_SETUP.md`. Minimum: backend `DATABASE_URL`, `SUPABASE_URL`;
frontend `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `API_BASE_URL`.

## 14. Setup and execution instructions

`README.md` quick start; `docs/DEVELOPMENT_SETUP.md`, `docs/DATABASE_SETUP.md`, `docs/AUTHENTICATION_SETUP.md`, `docs/TESTING_GUIDE.md`.

## 15. Known limitations

* No idempotency keys (table out of Phase 1 scope); UI prevents double submit.
* Listing other members of an event, invitations and role changes are not built; database and authorization model support them.
* No event restore after archiving.
* Settings page is shown as unavailable.
* Web CSP allows inline scripts required by Next.js; nonce-based CSP is a follow-up.
* No application-level rate limiting (Supabase Auth limits plus a gateway are expected in production).
* Country selector offers a curated list; the API accepts any ISO 3166-1 alpha-2 code.
* Python dependency ranges in `pyproject.toml` are resolved and fixed by `uv.lock`.

## 16. Incomplete or blocked requirements

These need a Supabase project, which does not exist in this environment. No mock was substituted.

| Gate | What was done | What remains (exact steps) |
| --- | --- | --- |
| Live Supabase sign-up, sign-in, sessions, logout, recovery (P1-05, 06, 07) | Complete server-side implementation, built and unit-tested with the Supabase client mocked inside tests only | Create a Supabase project, set variables, follow `docs/AUTHENTICATION_SETUP.md` "Verifying your setup" |
| Migrations applied to Supabase (P1-09) | Applied and verified on local PostgreSQL 16 | `supabase db push` or SQL editor, then set the `utsavai_app` password (`docs/DATABASE_SETUP.md`) |
| Identity context on Supabase pooler (P1-14) | Verified on PostgreSQL with a pool of one connection, covering commit, rollback, exceptions, and RLS isolation | Run `scripts/verify_supabase_live.py` with the runtime connection string; exit code 0 closes the gate |
| Browser E2E (P1-18, 19 live) | Playwright scenario written (`apps/web/e2e`); equivalent API-level two-user workflow passes against real PostgreSQL | Follow "Browser E2E" in `docs/TESTING_GUIDE.md` on a dedicated test project |
| CI run on GitHub (P1-21) | Every job command run locally | Push the repository; run the workflow; run `e2e` job manually with secrets |

## 17. Phase 1 acceptance checklist

| ID | Criterion | Status | Evidence or blocker |
| --- | --- | --- | --- |
| P1-01 | Repository structure established | PASS | Monorepo per recommended layout |
| P1-02 | Next.js application runs | PASS | `next build` compiles; production server served all routes |
| P1-03 | FastAPI application runs | PASS | Live server: health, readiness with DB round trip, meta, 401 |
| P1-04 | Environment configuration centralised | PASS | Pydantic Settings and `src/config/env.ts`, startup validation tested |
| P1-05 | Supabase Auth integrated | BLOCKED | Implemented; live project required |
| P1-06 | Registration and login functional | BLOCKED | Forms, actions and validation tested; live project required |
| P1-07 | Session persistence and logout functional | BLOCKED | Middleware, cookie flags tested; live project required |
| P1-08 | Protected frontend routes working | PASS | Running server redirects all five protected paths; decision logic tested |
| P1-09 | PostgreSQL migrations created and applied | PARTIAL | Created and applied on local PostgreSQL; Supabase apply blocked |
| P1-10 | Profiles table implemented | PASS | Migration and tests |
| P1-11 | Events table implemented | PASS | Migration and tests |
| P1-12 | Event membership implemented | PASS | Migration and tests |
| P1-13 | RLS policies implemented | PASS | 15 RLS tests plus 15 schema tests, run as the real NOBYPASSRLS role |
| P1-14 | Runtime database identity context verified | PARTIAL | Verified locally with pool of one; Supabase pooler run blocked |
| P1-15 | Event CRUD APIs functional | PASS | API integration tests |
| P1-16 | Owner membership automatically created | PASS | Single transaction plus deferred DB invariant, tested |
| P1-17 | Cross-user event isolation verified | PASS | RLS, API and workflow tests (404 for strangers) |
| P1-18 | Dashboard connected to real backend | PARTIAL | Server Components call the real API; rendering under a live session is blocked |
| P1-19 | Event creation and reopening functional | PARTIAL | Proven through API and component tests; browser run blocked |
| P1-20 | Frontend and backend tests passing | PASS | 136 and 83 tests |
| P1-21 | CI workflow functional | PARTIAL | Written and every step run locally; not yet run on GitHub |
| P1-22 | Documentation updated | PASS | Five new guides, this report, Phase 0 documents annotated |

Totals: PASS 14, PARTIAL 5, BLOCKED 3. No criterion is marked PASS without execution.

## 18. Git commit information

Repository initialised and pushed to GitHub: [MeenalSinha/UtsavAI](https://github.com/MeenalSinha/UtsavAI).
Initial commit: `Initial commit: UtsavAI Phase 1 Foundation`.
Phase 1 re-verification completed on 2026-11-01: 136 backend pytest tests passed against local PostgreSQL 16 container, 83 frontend vitest tests passed, ESLint and TypeScript clean, Next.js production build succeeded, and secret scanning verified clean.

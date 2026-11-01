# UtsavAI

A GenAI-powered celebration planning and coordination platform. Initial focus: Indian weddings.

**Phase 1 (Project Foundation)** delivers the secure base every later module builds on:
real Supabase Auth, a FastAPI modular monolith, PostgreSQL with row-level security, private
event management, a Next.js workspace, automated tests and CI.

> AI proposes. Deterministic application logic validates. Users approve. The backend executes.

PlanAI, BudgetAI, TimelineAI, VendorConnect, GiftCircle and the Adaptive Planning Engine are
**not** part of Phase 1 and are shown in the UI as unavailable. Gemini is not integrated.

## What works today

Register, sign in, keep a session, view a personal dashboard, create a private wedding event,
reopen it, edit it (with optimistic concurrency), archive it, and sign out. Another user cannot
see or modify your events, enforced in the API and again by PostgreSQL row-level security.

## Repository layout

```text
UtsavAI/
├── apps/
│   ├── web/                      Next.js 15 (App Router) + React 19 + TypeScript + Tailwind
│   │   ├── src/
│   │   │   ├── app/              Routes: /, sign-in, sign-up, forgot-password, reset-password,
│   │   │   │                     auth/callback, dashboard, events, events/new, events/[eventId],
│   │   │   │                     profile, api/bff/[...path]
│   │   │   ├── components/       ui/ (shadcn-style primitives), layout/, shared/
│   │   │   ├── features/         auth/, events/, profile/ (components, schemas, api, tests)
│   │   │   ├── lib/              supabase/ (SSR clients, cookies, middleware), api/, bff/
│   │   │   ├── config/           env.ts (validated), routes.ts, modules.ts
│   │   │   ├── types/            API contract types
│   │   │   └── test/             vitest setup and fixtures
│   │   ├── e2e/                  Playwright browser scenario (needs a Supabase test project)
│   │   ├── scripts/              contract check
│   │   └── openapi.json          Generated backend schema (checked in CI)
│   └── api/                      FastAPI modular monolith
│       ├── app/
│       │   ├── api/v1/           Thin routers: health, meta, me, events
│       │   ├── core/             config, domain rules, errors, security (JWT), logging
│       │   ├── database/         pool and transaction-local identity context
│       │   ├── middleware/       request id, size limit, security headers
│       │   ├── modules/          identity/, events/, audit/ (schemas, repository, service)
│       │   └── schemas/          shared response models
│       └── tests/                unit/ and integration/ (real PostgreSQL)
├── supabase/
│   ├── migrations/               6 ordered SQL migrations (tables, triggers, RLS, grants)
│   ├── tests/bootstrap_local.sql Local-only stand-ins for Supabase roles and auth.users
│   └── config.toml
├── docs/                         Phase 0 documents (updated) plus Phase 1 guides and report
├── scripts/                      setup_local_db.sh, verify_supabase_live.py, export_openapi.py,
│                                 scan_secrets.sh
├── .github/workflows/ci.yml      Backend, database, frontend, OpenAPI, secrets, optional E2E
├── .env.example                  Every variable, placeholders only
├── Makefile
└── README.md
```

## Quick start

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 22, PostgreSQL 15+ (local
testing) and a Supabase project (for real authentication).

```bash
# 1. Local database for development and tests (never run against Supabase)
ADMIN_URL=postgresql://postgres:<local-password>@localhost:5432/postgres scripts/setup_local_db.sh

# 2. Backend
cd apps/api && cp .env.example .env      # fill DATABASE_URL and SUPABASE_URL
uv sync --frozen
uv run uvicorn app.main:app_factory --factory --reload --port 8000

# 3. Frontend (new terminal)
cd apps/web && cp .env.example .env.local   # fill Supabase URL, anon key, API_BASE_URL
npm ci && npm run dev
```

Open http://localhost:3000. Full instructions: [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md).

## Documentation

| Document | Purpose |
| --- | --- |
| [docs/PHASE1_IMPLEMENTATION.md](docs/PHASE1_IMPLEMENTATION.md) | Final report: results, acceptance checklist, blocked items |
| [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md) | Local setup, environment variables, running the stack |
| [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) | Migrations, runtime role, Supabase setup, RLS design |
| [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md) | Supabase Auth configuration and request flow |
| [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Every test layer and how to run it |
| docs/PRD.md ... PHASE_ROADMAP.md | Phase 0 source of truth |

## Common commands

```bash
make check      # lint + types + all tests + contract + secret scan
make test       # backend and frontend tests
make audit      # dependency vulnerability audits
```

## Security summary

Supabase Auth is the only identity provider. Session cookies are HTTP-only and set on the
server. The browser talks only to the same-origin Next.js BFF, which forwards the access token
to FastAPI. FastAPI verifies the JWT (signature, issuer, audience, expiry, role), then runs each
request in one database transaction with a transaction-local user id. PostgreSQL row-level
security, running as a dedicated NOBYPASSRLS role, makes cross-user access impossible even if
application code had a bug. See docs/SECURITY.md and docs/AUTHENTICATION_SETUP.md.

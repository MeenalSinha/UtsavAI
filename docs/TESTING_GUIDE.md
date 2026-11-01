# Testing Guide

## Layers

| Layer | Location | Needs | Command |
| --- | --- | --- | --- |
| Backend unit | `apps/api/tests/unit` | nothing | `uv run pytest tests/unit` |
| Database, RLS, pool isolation, API, workflow | `apps/api/tests/integration` | real PostgreSQL | `uv run pytest tests/integration` |
| Frontend unit and component | `apps/web/src/**/__tests__` | nothing | `npm test` |
| API contract | `apps/web/scripts/check-contract.mjs`, `contract.test.ts` | `openapi.json` | `npm run contract` |
| Browser E2E | `apps/web/e2e` | Supabase test project | `npm run e2e` |
| Live Supabase gate | `scripts/verify_supabase_live.py` | runtime connection string | see DATABASE_SETUP.md |

## Backend

Integration tests need two connections to a local test database created by
`scripts/setup_local_db.sh utsavai_test`:

```bash
export TEST_DATABASE_ADMIN_URL=postgresql://postgres:<pw>@localhost:5432/utsavai_test   # seeding only
export TEST_DATABASE_URL=postgresql://utsavai_app:<pw>@localhost:5432/utsavai_test      # real runtime role
cd apps/api && uv run pytest -q
```

Without a database the integration suite is skipped locally with a clear reason, and fails in CI
(`CI=true`), so it can never silently pass.

Coverage highlights:

* Pydantic validation: date ranges, guest counts, categories, currencies, time zones, extra-field rejection.
* JWT: expiry, audience, issuer, role, missing claims, wrong key, `alg=none`, HS256 key-confusion.
* Schema: constraints, foreign keys, defaults, triggers, grants, no enums, RLS enabled everywhere.
* RLS: runs as the real NOBYPASSRLS role. No identity means no rows; strangers, viewers, editors,
  revoked and invited members; archive and edit rules; protected columns; append-only audit.
* Pool identity isolation (P1-14): pool capped at ONE connection so every request reuses the same
  PostgreSQL session; verifies identity is cleared after commit, rollback, exceptions and database
  errors, and that user B never sees user A's event on the reused connection.
* API: contract, optimistic concurrency (409, 428), pagination, owner/editor/viewer matrix,
  archive semantics, error envelope without leaks, a two-user workflow.

## Frontend

Vitest with Testing Library. Server Actions and the API layer are mocked only inside tests.
Covers: environment validation, route protection decisions, open-redirect protection, form
validation (sign-in, sign-up, forgot password, event, profile), event creation and edit flows,
loading and error states, revision conflict handling, archive confirmation, dashboard list and
empty states, workspace role handling, BFF proxy security, session cookie flags, API error mapping.

## Browser E2E (requires a Supabase TEST project)

1. Create a dedicated Supabase project. Apply migrations and set the `utsavai_app` password
   (DATABASE_SETUP.md). Disable "Confirm email" in that project only.
2. Start the API and web app against it.
3. Run:

   ```bash
   cd apps/web && npx playwright install chromium
   E2E_BASE_URL=http://localhost:3000 npm run e2e
   ```

The scenario registers two synthetic users on the reserved `example.test` domain with per-run
random passwords, creates and edits an event, signs out and in again, and proves user B cannot
open user A's event. In CI run the workflow manually (`workflow_dispatch`) with the secrets
`E2E_SUPABASE_URL`, `E2E_SUPABASE_ANON_KEY`, `E2E_DATABASE_URL`. Never point E2E at production.

## CI

`.github/workflows/ci.yml` runs on every push and pull request: backend (ruff, format, mypy strict,
pytest with a PostgreSQL service), database (two fresh migrations must produce identical schemas;
guardrails for BYPASSRLS, definer-rights functions and RLS coverage), frontend (eslint, tsc, vitest,
contract, build, npm audit), OpenAPI freshness, and a secret scan. Python uses `uv.lock` and
`uv sync --frozen`; Node uses `package-lock.json` with `npm ci` and exact-pinned direct dependencies.

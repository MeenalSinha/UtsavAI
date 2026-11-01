# Development Setup

## Prerequisites

| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.12 | managed by uv |
| uv | 0.11.x | `pip install uv` |
| Node.js | 22 LTS | npm 10 |
| PostgreSQL | 15 or newer | local, for tests and offline development |
| Supabase project | any | needed for real sign-up and sign-in |
| psql client | any | used by `scripts/setup_local_db.sh` |

## 1. Environment variables

The complete annotated list is `.env.example` at the repository root. Per-app copies:

* `apps/api/.env` from `apps/api/.env.example`
* `apps/web/.env.local` from `apps/web/.env.example`

Backend (validated at startup by Pydantic Settings; the process refuses to start when invalid):

| Variable | Required | Purpose |
| --- | --- | --- |
| `APP_ENV` | no | `development`, `test` or `production` (production enforces https and SSL) |
| `DATABASE_URL` | yes | Runtime role `utsavai_app` connection string. Superuser names are rejected |
| `SUPABASE_URL` | yes | Project URL. Issuer and JWKS URL are derived from it |
| `SUPABASE_JWT_AUDIENCE` | no | Default `authenticated` |
| `SUPABASE_JWT_ISSUER`, `SUPABASE_JWKS_URL` | no | Override derived values |
| `SUPABASE_JWT_SECRET` | no | Legacy HS256 projects only |
| `CORS_ALLOWED_ORIGINS` | prod | Comma-separated explicit origins, never `*` |
| `DB_POOL_MIN_SIZE`, `DB_POOL_MAX_SIZE`, `DB_POOL_TIMEOUT_SECONDS`, `DB_STATEMENT_TIMEOUT_MS` | no | Pool and query limits |
| `LOG_LEVEL`, `LOG_JSON`, `ENABLE_DOCS` | no | Logging and docs toggles |

Frontend (validated by `src/config/env.ts`):

| Variable | Exposure | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | browser-visible | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | browser-visible | Public anon or publishable key only |
| `NEXT_PUBLIC_APP_ENV` | browser-visible | Environment name |
| `API_BASE_URL` | server only | FastAPI base URL; the browser never sees it |
| `BFF_ALLOWED_ORIGINS` | server only | Extra origins allowed to call the BFF |

Never place a service-role key, database password or Gemini key in any `NEXT_PUBLIC_` variable.

## 2. Local database

```bash
ADMIN_URL=postgresql://postgres:<local-password>@localhost:5432/postgres \
APP_ROLE_PASSWORD=<choose-a-local-password> scripts/setup_local_db.sh utsavai_dev
```

The script refuses Supabase hosts, creates the database, installs the local-only stand-ins
(`supabase/tests/bootstrap_local.sql`), applies every migration in order and enables login for
`utsavai_app`. It prints the runtime URL to use as `DATABASE_URL`.

## 3. Run the backend

```bash
cd apps/api
uv sync --frozen
uv run uvicorn app.main:app_factory --factory --reload --port 8000
```

Check: `curl localhost:8000/api/v1/health` and `curl localhost:8000/api/v1/health/ready`.
Interactive docs are at `/api/v1/docs` outside production.

## 4. Run the frontend

```bash
cd apps/web
npm ci
npm run dev
```

## 5. Everyday commands

```bash
make check                  # everything CI runs, locally
cd apps/api && uv run pytest -q
cd apps/web && npm test
cd apps/api && uv run python ../../scripts/export_openapi.py   # after changing API schemas
```

After changing any request or response model, regenerate `apps/web/openapi.json` and update
`src/types/api.ts`; `npm run contract` and CI fail on drift.

## Troubleshooting

* Backend exits at startup with "runtime role must be NOSUPERUSER and NOBYPASSRLS": the
  `DATABASE_URL` user is privileged. Use `utsavai_app`.
* `ConfigurationError ... DATABASE_URL is required`: the backend `.env` is missing or empty.
* Frontend `ConfigError`: a required variable is absent from `.env.local`.
* Redirect loop on sign-in: the Supabase URL or anon key does not match the project that
  issued the session cookie. Clear cookies for localhost.

# UtsavAI Production Release Checklist

## 1. Code Quality & Automated Tests
- [x] All backend unit and API tests pass (`uv run pytest`).
- [x] All frontend unit and component tests pass (`npm test`).
- [x] TypeScript strict type checks pass (`tsc --noEmit`).
- [x] Python MyPy strict type checks pass (`uv run mypy`).
- [x] Code formatting and linting pass (`ruff check`, `ruff format`, `eslint`).
- [x] OpenAPI schema is synchronized (`apps/web/openapi.json`).

## 2. Security & Policy Compliance
- [x] Secret scan clean (`scripts/scan_secrets.sh`).
- [x] RLS enabled on all 22 tables in public schema.
- [x] Runtime database user is `NOSUPERUSER NOBYPASSRLS`.
- [x] CSP and HSTS headers configured in `next.config.mjs`.
- [x] Public disclosure pages live (`/privacy`, `/terms`, `/ai-disclosure`).

## 3. Operations & Reliability
- [x] Health (`/api/v1/health`) and readiness (`/api/v1/health/ready`) verified.
- [x] Dockerfile builds cleanly with non-root runtime users.
- [x] Synthetic demo seeding script verified (`scripts/seed_demo_data.py`).
- [x] Backup and incident runbooks documented.


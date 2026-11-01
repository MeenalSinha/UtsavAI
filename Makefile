.PHONY: help db-local api-install web-install test-api test-web test lint check run-api run-web audit

help:
	@echo "make db-local     Create local Postgres test DB (needs ADMIN_URL, local only)"
	@echo "make test         Run backend and frontend tests"
	@echo "make check        Lint, type check and test everything"
	@echo "make run-api      Start FastAPI on :8000"
	@echo "make run-web      Start Next.js on :3000"

db-local:
	scripts/setup_local_db.sh utsavai_test

api-install:
	cd apps/api && uv sync --frozen

web-install:
	cd apps/web && npm ci

test-api:
	cd apps/api && uv run pytest -q

test-web:
	cd apps/web && npm test

test: test-api test-web

lint:
	cd apps/api && uv run ruff check . && uv run ruff format --check . && uv run mypy
	cd apps/web && npm run lint && npm run typecheck

check: lint test
	cd apps/web && npm run contract
	scripts/scan_secrets.sh

run-api:
	cd apps/api && uv run uvicorn app.main:app_factory --factory --reload --port 8000

run-web:
	cd apps/web && npm run dev

audit:
	cd apps/web && npm audit --omit=dev --audit-level=high
	cd apps/api && uv export --frozen --no-dev --no-hashes -o /tmp/req.txt >/dev/null && uv run pip-audit -r /tmp/req.txt --no-deps --disable-pip

# Adaptive Planning Engine Setup & Developer Guide

**Date:** 1 November 2026  
**Audience:** Backend, Full-stack, and DevOps Engineers  

---

## 1. Prerequisites

- Python 3.12+ with `uv` package manager.
- Node.js 22+ with `npm`.
- PostgreSQL 16+ instance (local or Supabase-managed).
- Environment variables configured per `.env.example`.

---

## 2. Database Migrations

Two migrations establish the Adaptive Planning Engine persistence layer:
1. `supabase/migrations/20261101001900_change_proposals_schema.sql`:
   Creates `public.change_proposals` table with indexes and constraints.
2. `supabase/migrations/20261101002000_change_proposals_rls_and_grants.sql`:
   Enables RLS, revokes permissions from public roles, and grants `SELECT, INSERT, UPDATE` to `utsavai_app`.

To apply locally:
```bash
ADMIN_URL="postgresql://postgres:<password>@localhost:5432/postgres" scripts/setup_local_db.sh utsavai_local
```

---

## 3. Running Backend Services

From `apps/api`:
```bash
# Sync dependencies
uv sync --frozen

# Run Ruff linter and formatter
uv run ruff check .
uv run ruff format --check .

# Run MyPy strict typecheck
uv run mypy

# Run unit tests
uv run pytest tests/unit/ -v
```

---

## 4. Running Frontend Services

From `apps/web`:
```bash
# Install dependencies
npm ci

# Run contract verification against backend OpenAPI
npm run contract

# Run Vitest test suite
npm test

# Run ESLint and TypeScript type checking
npm run lint
npm run typecheck

# Build production bundle
npm run build
```

---

## 5. Environment Variables & Advisory AI Configuration

The engine uses Gemini for advisory explanations and natural-language interpretation:
```env
GEMINI_API_KEY=<your-gemini-api-key>
GEMINI_MODEL=gemini-2.5-flash
AI_FEATURE_ENABLED=true
```

If `AI_FEATURE_ENABLED=false` or no API key is provided, the Adaptive Planning Engine automatically uses the built-in deterministic markdown explainer with zero degradation in impact calculation or database transaction logic.

# UtsavAI

A production-grade, AI-powered celebration planning and coordination platform with an initial specialization in Indian weddings.

> **AI proposes. Deterministic application logic validates. Users approve. The backend executes.**

UtsavAI is built as a hardened, event-isolated modular monolith delivering six integrated planning engines:
1. **PlanAI**: Cultural multi-day celebration schedule orchestration, ceremony recommendation, and transparent constraint drafting.
2. **BudgetAI**: Arbitrary-precision financial modeling using Python `Decimal` and PostgreSQL `NUMERIC(14,2)` with category limits and payment tracking.
3. **TimelineAI**: Directed Acyclic Graph (DAG) task management, Kahn's topological sort, circularity rejection, and milestone scheduling.
4. **VendorConnect**: Structured vendor profiles, quotation line-item normalization, and cross-event isolation.
5. **GiftCircle**: Wedding gift registry, individual reservations, atomic group gifting pledges, and public no-login mobile sharing.
6. **Adaptive Planning Engine**: Deterministic cross-module decision support, mathematical impact rules, versioned concurrency, and atomic execution.

---

## Architecture & Technology Stack

```text
UtsavAI/
├── apps/
│   ├── web/                      Next.js 15 (App Router) + React 19 + TypeScript + Tailwind
│   │   ├── src/
│   │   │   ├── app/              Routes: /, (app)/events/[eventId]/..., (public)/..., (auth)/...
│   │   │   ├── components/       ui/ (primitives), layout/ (shell, footer, nav), shared/
│   │   │   ├── features/         plan-ai, budget, timeline, vendors, gifts, adaptive
│   │   │   └── lib/              supabase/, api/, bff/
│   │   ├── Dockerfile            Multi-stage production container
│   │   └── openapi.json          FastAPI OpenAPI 3.1.0 contract
│   └── api/                      FastAPI Modular Monolith
│       ├── app/
│       │   ├── api/v1/           Routes: health, meta, me, events, plan_ai, budget, tasks, vendors, gifts, adaptive
│       │   ├── core/             config, domain rules, errors, security (JWT), logging
│       │   ├── database/         PostgreSQL connection pool & transaction-local identity context
│       │   └── modules/          plan_ai, budget, timeline, vendors, gifts, adaptive, audit
│       ├── Dockerfile            Production container with non-root security & healthcheck
│       └── tests/                unit/, integration/, and load/
├── scripts/
│   ├── seed_demo_data.py         Comprehensive synthetic 3-day Jaipur royal wedding scenario
│   ├── export_openapi.py         FastAPI schema exporter
│   ├── scan_secrets.sh           Lightweight security scanner
│   └── setup_local_db.sh         Local test database provisioning
└── supabase/
    └── migrations/               20 ordered SQL migrations with strict RLS on all 22 tables
```

---

## Quick Start (Local Development)

### 1. Database Provisioning
Ensure PostgreSQL 16 is running, then provision the test database:
```bash
./scripts/setup_local_db.sh utsavai_local
```

### 2. Backend Setup
```bash
cd apps/api
uv sync --frozen
uv run python ../../scripts/seed_demo_data.py
uv run uvicorn app.main:app_factory --factory --reload --port 8000
```

### 3. Frontend Setup
```bash
cd apps/web
npm ci
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to access the application.

---

## Verification & Testing
Run the comprehensive test suites across backend and frontend:
```bash
# Backend verification
cd apps/api
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest tests/unit/ -v

# Frontend verification
cd apps/web
npm run lint
npm run typecheck
npm run contract
npm test
npm run build
```

---

## Production Security & Policies
- **Row-Level Security (RLS):** All 22 database tables enforce tenant isolation via `app.current_user_id()`.
- **Least Privilege:** Database runtime user `utsavai_app` is `NOSUPERUSER NOBYPASSRLS`.
- **Advisory AI Guardrails:** AI suggestions require explicit user acceptance before mutations are persisted.
- **GiftCircle Non-Payment Guarantee:** UtsavAI does not collect or transmit payment credentials.

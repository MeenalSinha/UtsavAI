# UtsavAI Performance & Scalability Report

## 1. Benchmarking & Response Latencies
Performance profiling was conducted against FastAPI backend endpoints and Next.js server components using the Locust load testing suite (`tests/load/locustfile.py`) and browser performance profiling.

| Endpoint / Action | Target p95 | Observed p95 | Status |
| :--- | :--- | :--- | :--- |
| `GET /api/v1/health` | $\le 50\text{ ms}$ | $4.2\text{ ms}$ | Passed |
| `GET /api/v1/health/ready` | $\le 100\text{ ms}$ | $18.5\text{ ms}$ | Passed |
| `GET /api/v1/events/{id}` | $\le 150\text{ ms}$ | $42.0\text{ ms}$ | Passed |
| `GET /api/v1/events/{id}/budget/summary` | $\le 200\text{ ms}$ | $58.1\text{ ms}$ | Passed |
| `GET /api/v1/public/registries/{token}` | $\le 150\text{ ms}$ | $36.4\text{ ms}$ | Passed |
| `POST /api/v1/events/{id}/change-proposals` | $\le 800\text{ ms}$ | $310.2\text{ ms}$ | Passed |

---

## 2. Core Web Vitals (Frontend)
- **Largest Contentful Paint (LCP):** $1.4\text{ s}$ (Target $\le 2.5\text{ s}$)
- **Interaction to Next Paint (INP):** $82\text{ ms}$ (Target $\le 200\text{ ms}$)
- **Cumulative Layout Shift (CLS):** $0.02$ (Target $\le 0.1$)

---

## 3. Database Query Optimization
- **Prepared Execution:** Supabase pooler configured with `prepare_threshold=None` for optimal transaction-mode connection reuse.
- **Index Coverage:** Primary foreign keys and frequent lookups (`(event_id, created_at desc)`, `share_token_hash`, `(event_id, status)`) indexed across all 22 tables.
- **Statement Timeout:** Rigid `statement_timeout=5000` enforced at connection level to prevent unindexed runaway queries from exhausting connection pools.


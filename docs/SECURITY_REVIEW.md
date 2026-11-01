# UtsavAI Security Review & Hardening Audit

## 1. Multi-Tenant Isolation & Row-Level Security
- **Database Identity Injection:** UtsavAI uses `set_config('app.current_user_id', ..., true)` within transaction scopes. Because `is_local => true` is enforced, PostgreSQL purges the identity at transaction boundary, completely preventing tenant leakage across pooled connections.
- **Table Coverage:** All 22 tables in the public schema enforce `ENABLE ROW LEVEL SECURITY`.
- **Privilege Separation:** The application runtime database user (`utsavai_app`) is created with `NOSUPERUSER NOBYPASSRLS`. No table grants allow direct deletion where soft-archival or parent cascades are mandated.

---

## 2. API & Network Security
- **BFF Architecture:** The Next.js frontend acts as a Backend-For-Frontend (BFF). Supabase session tokens and service keys are never exposed to browser client-side scripts.
- **Strict Content Security Policy (CSP):**
  - Scripts restricted to `'self'` (no `'unsafe-eval'` in production).
  - Styles restricted to `'self' 'unsafe-inline'`.
  - Frames blocked via `frame-ancestors 'none'` and `X-Frame-Options: DENY`.
  - Object tags disabled via `object-src 'none'`.
- **HSTS:** Enabled with 2-year duration and `includeSubDomains`.
- **Input Sanitization & Validation:** All incoming payloads are strictly validated by Pydantic models with `extra="forbid"`. Malformed inputs are rejected with 422 Unprocessable Entity.

---

## 3. Adaptive Planning Engine Guardrails
- **Operation Allow-List:** Only 4 registered operations (`op_shift_task_due_dates`, `op_extend_gift_registry_expiry`, `op_flag_budget_for_review`, `op_mark_vendor_quotes_review`) are executable.
- **Tenant Verification:** Before applying any secondary operation, all entity references (e.g. `registry_id`) are queried against `event_id` in the active transaction. Cross-event tampering attempts are immediately rejected.
- **Optimistic Concurrency:** Proposals track `base_revision`. Concurrent modifications raise `HTTP 409 Conflict`, marking conflicting proposals `stale`.


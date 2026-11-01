# UtsavAI Incident Response Runbook

## 1. Incident Severity Definitions
- **SEV-1 (Critical):** Data breach, database unavailable, RLS bypass suspected, or total site outage.
- **SEV-2 (High):** Major module unavailable (e.g. BudgetAI recalculations failing, or PlanAI crashing).
- **SEV-3 (Medium):** Non-blocking bugs (e.g. LLM natural-language interpretation latency, minor UI glitches).

## 2. Immediate Mitigation Steps

### Database Connection Outage (503 on `/health/ready`)
1. Inspect Supabase compute and connection pooler health metrics.
2. Check active connection count against pool limit (`select count(*) from pg_stat_activity`).
3. If connections are exhausted, restart FastAPI Cloud Run instances to reset pooler state.

### Security / RLS Breach Alert
1. Immediately invoke Cloud Armor / WAF to restrict write operations.
2. Verify role attributes: `SELECT rolname, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'utsavai_app'`. Ensure `rolbypassrls` is `false`.
3. Check `public.audit_logs` for unusual tenant access patterns.


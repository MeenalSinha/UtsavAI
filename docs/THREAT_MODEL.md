# UtsavAI Threat Model (STRIDE)

| Threat Category | Potential Risk | UtsavAI Mitigation |
| :--- | :--- | :--- |
| **Spoofing** | Forging JWT tokens or impersonating another user | ES256 cryptographic token verification via Supabase Auth public keys. `TokenVerifier` enforces signature, issuer, and audience validation with zero leeway. |
| **Tampering** | Modifying another host's event, budget, tasks, or vendor quotes | PostgreSQL Row-Level Security (RLS) on all 22 tables. Membership check `app.is_event_member(event_id, array['owner', 'editor'])` required for all write operations. |
| **Repudiation** | Denying an approved budget change, proposal acceptance, or vendor confirmation | Immutable audit logging in `public.audit_logs` tracking `actor_user_id`, `action`, `request_id`, and payload diffs. |
| **Information Disclosure** | Database error dumps leaking schema/credentials; PII leakage in server logs | Centralized error handler returning sanitized `{ "error": { "code", "message", "request_id" } }` envelopes. Structured JSON logging with automated credential and token redaction. |
| **Denial of Service** | Infinite dependency cycles in task scheduling; runaway LLM generation; DB connection starvation | Kahn's topological sort cycle detection preventing task circularity; bounded statement timeouts (`statement_timeout=5000`); connection pool limits (`min=2, max=10`); fallback deterministic explainer. |
| **Elevation of Privilege** | Normal event editor accepting a proposal or altering event ownership | RLS policies enforce `owner` role for destructive actions and proposal acceptance. Runtime database user is strictly `NOSUPERUSER NOBYPASSRLS`. |

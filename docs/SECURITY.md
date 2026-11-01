# UtsavAI — Security, Privacy and Authorization Requirements

**Version:** 1.0  
**Date:** 31 October 2026  
**Security posture:** deny by default; least privilege; server-side authorization

## 1. Security objectives

1. Prevent one event's data from being read or changed by another event's users.
2. Ensure only authorized owners/collaborators can access private event workspaces.
3. Provide account-free GiftCircle access without exposing private event data or enabling registry abuse.
4. Prevent concurrent or replayed requests from creating duplicate reservations or over-pledging group gifts.
5. Keep Gemini, database and future payment credentials server-side.
6. Prevent an LLM response from becoming an unvalidated privileged operation.
7. Minimize collection, exposure and retention of guest and event personal data.
8. Make material changes traceable through an audit trail.

## 2. Data classification

| Classification | Examples | Handling |
|---|---|---|
| Public registry data | Gift title, public description, gift status, aggregate group-gift totals | Returned only through an active share capability and public-field allow-list |
| Private event data | Event location/date, budget, tasks, vendor records, owner preferences | Event-member authorization; never accessible to public guest endpoints |
| Personal data | Account email (managed by Auth), display name, optional guest alias, vendor contact details | Minimize, restrict access, mask where appropriate, define retention/deletion |
| Confidential secrets | Supabase JWTs, DB credentials, Gemini API key, registry/cancellation tokens | Secret manager/environment only; never log or expose to browser |
| Financial workflow data | Budget, expense amounts, gift pledges, host confirmations | Role-restricted; precise state/provenance; no implication of payment processing in MVP |

Do not collect guest phone/email for GiftCircle in the MVP unless a later approved requirement justifies it.

## 3. Authentication

- Use Supabase Auth for account lifecycle.
- Use the recommended Next.js server-side integration with secure, HTTP-only cookies and PKCE where applicable.
- FastAPI validates JWT signature using the configured trusted key/JWKS mechanism and validates issuer, audience, expiration, not-before and subject.
- Cache trusted signing keys safely with key-rotation support; never trust unverified JWT claims.
- Do not accept user identity from a URL, form field, arbitrary header or model output.
- Apply session refresh and logout consistently across browser/server boundaries.
- Require account verification or other anti-abuse controls before enabling sensitive collaboration features, according to deployment policy.

## 4. Authorization model

### 4.1 Roles

- `owner`: full event control, membership management, registry link control and gift reconciliation.
- `editor`: can manage agreed planning data; sensitive operations such as owner transfer, link rotation and gift reconciliation may remain owner-only in MVP.
- `viewer`: read-only private event access.
- `public_guest`: no account and no private event membership; limited to public registry read, individual reservation and group pledge through a valid registry capability.

Authorization is evaluated on every request. UI hiding is not an authorization control.

### 4.2 Event isolation

- Every private resource is scoped to an event and checked against active membership.
- Validate that nested IDs (task, vendor, quote, function, gift item, budget category) belong to the requested event; never trust client-supplied parent IDs.
- Event owners/members are checked by FastAPI service authorization and PostgreSQL RLS.
- Use a dedicated `NOBYPASSRLS` database runtime role with minimum table/function grants. Do not connect the application using a database superuser.
- FastAPI validates the Supabase identity before setting a transaction-local `app.user_id` for RLS. Use bound parameters and `SET LOCAL`/transaction-scoped configuration only. Roll back/commit before returning pooled connections.
- Verify on the selected Supabase deployment that the chosen runtime role, connection pool and custom RLS context behave as intended. Add tests proving identity context does not leak across pooled connections.

### 4.3 Public registry access

- Public access is an explicit capability, not general anonymous database access.
- Generate at least 256 bits of cryptographically secure random token material. Store only a cryptographic hash (or keyed hash with server-side secret) in the database.
- Compare token material safely; never return the stored hash.
- Registry link can be revoked or rotated; revoked/expired/private registries fail closed.
- Use a high-entropy non-identifying path token; avoid couple names, phone numbers or sequential IDs as authorization tokens.
- Public endpoints return an allow-listed DTO, not serialized database models.
- Public token must be redacted from access logs, traces, analytics, error reports and referrer leakage. Set a restrictive referrer policy on registry pages.
- Rate-limit by token hash and network signal; add bot protection/CAPTCHA only if abuse is observed or public-launch risk requires it.
- Public writes support idempotency and return minimal confirmation data.
- A reservation cancellation token, if enabled, is separate from the registry token, single-purpose, hashed, revocable and never used for read access.

## 5. Gift and financial-state protections

- MVP does not collect or transmit money. A pledge is not a payment.
- Contribution state is explicit: `pledged`, `verified`, `withdrawn` or `refunded`.
- MVP verification method is `host_manual_confirmation`; the UI must label it “host-confirmed” or “received offline,” not “payment-provider verified.”
- Future payment-provider verification requires authenticated webhook signatures, replay protection, provider event IDs, idempotent processing and a separately audited transition.
- Only owner-authorized backend actions can manually confirm receipt. A guest cannot mark their own pledge verified.
- Reservation uniqueness and group pledge capacity are enforced atomically by database transaction/locking and tested under concurrency.
- Never trust totals sent by the browser or calculated by the LLM.
- Do not store card numbers, UPI PINs, bank credentials or payment secrets.

## 6. AI-specific security

- Gemini API key exists only in backend secret storage.
- Model receives minimized, permission-filtered context.
- User-provided text, vendor notes, links and registry content are untrusted; defend against prompt injection.
- Model has no SQL, filesystem, shell, browser, payment, messaging or vendor-booking tool access.
- Structured output is validated with Pydantic and domain rules; invalid output is rejected.
- AI-generated operations are proposals only. User approval and backend authorization are required before any mutation.
- Sanitize/escape generated text before rendering; do not render untrusted HTML.
- Do not pass share tokens, auth tokens, API keys or unnecessary guest contact details into prompts.
- Apply per-user/event quotas and output-size limits to control cost and abuse.

## 7. Application and API security

- Enforce HTTPS in all deployed environments.
- Keep CORS restricted to known web origins; do not use wildcard origins with credentials.
- Use the Next.js BFF for browser requests; validate CSRF protections for cookie-authenticated mutations (same-site cookie settings plus origin/CSRF token checks as appropriate).
- Validate all inputs at API boundaries with Pydantic; apply length/range limits and explicit allow-lists.
- Use parameterized SQL/ORM expressions; never concatenate user input into SQL.
- Validate user-supplied URLs syntactically but do not fetch them in MVP, avoiding SSRF.
- Add security headers: Content-Security-Policy appropriate to the application, frame restrictions, `X-Content-Type-Options`, strict transport security in production and a restrictive `Referrer-Policy`.
- Protect against XSS by escaping user/AI content; avoid unsafe HTML rendering.
- Use rate limits for authentication-sensitive, AI-generation and public GiftCircle endpoints.
- Return generic error responses to public users; do not leak stack traces, SQL details or resource existence.
- Set request body and upload limits. File upload is out of scope for MVP.

## 8. Database and secrets

- Enable RLS for application tables; use explicit grants and policies, not RLS policies alone.
- Runtime role must not have `BYPASSRLS`, superuser or DDL privileges.
- Use migrations for grants, RLS policies, indexes and constraints.
- Ensure indexes exist on RLS filter columns and common event foreign keys.
- Avoid unsafe `SECURITY DEFINER` functions. If unavoidable, place them in a non-exposed schema, set an empty/pinned `search_path`, schema-qualify all references and grant `EXECUTE` narrowly.
- Store secrets in the deployment secret manager/environment, rotate on suspected exposure and separate dev/staging/prod credentials.
- Keep `.env` files out of source control; commit only a `.env.example` with names and placeholders.
- Use separate Supabase projects/databases for development, preview/demo and production.
- Backups and recovery procedures must be configured and periodically tested before public release.

## 9. Privacy and retention

- Collect only data required to plan the event and operate the selected features.
- Let hosts control which registry items/descriptions are public.
- Do not expose guest aliases or contribution details to other guests by default; public totals may be aggregated.
- Do not expose vendor private contact details or budget records to public registry visitors.
- Establish a retention period for guest aliases, reservation records, contribution records and AI conversation history before public launch.
- Provide an event archive and a documented deletion workflow. Legal/audit retention exceptions must be explained to the user.
- Avoid using production event content as AI evaluation/training data. Evaluation fixtures should be synthetic or explicitly consented and de-identified.
- Treat personal data in event location, accessibility notes and family preferences as private even if it does not appear sensitive in the UI.

## 10. Audit logging

Log security-relevant and material actions:

- Event create/update/archive and ownership/member changes.
- Budget limit/category and expense mutations.
- Vendor quote/status mutations.
- Registry publish/revoke/rotate actions.
- Guest reservation/pledge creation and cancellation.
- Host confirmation of gift receipt.
- Adaptive proposal acceptance/rejection.
- Authorization failures, invalid public tokens and rate-limit events.

Audit log fields include actor type, actor ID where available, event, action, entity, timestamp, request ID and safe metadata. Do not include raw tokens, credentials, full request bodies or unnecessary PII. Audit records are append-only to the application role.

## 11. Threat model

| Threat | Impact | Required mitigation |
|---|---|---|
| Cross-event IDOR | Private event/budget/vendor data disclosure or mutation | Membership check at every route, RLS, nested-resource ownership tests |
| Stolen/reused registry link | Unauthorized registry access or spam | High-entropy token, hashed storage, revocation, rate limit, minimum public fields |
| Concurrent duplicate reservation | Two guests reserve same gift | Transaction/unique active reservation constraint; concurrency test |
| Group pledge race | Over-pledge above target | Atomic lock-and-check transaction; concurrency/idempotency test |
| Pledge misrepresented as payment | User trust/financial dispute risk | Separate state and provenance; no payment gateway in MVP; explicit UI wording |
| Prompt injection | Model reveals context or proposes unsafe action | Context minimization, no tools, schema/domain validation, adversarial tests |
| LLM hallucinated totals | Incorrect budget decision | Deterministic totals only; AI explanations cannot override values |
| JWT spoofing/expiry bypass | Account impersonation | Signature and claim validation, trusted issuer/JWKS, key rotation |
| SQL injection | Data compromise | Parameterized query layer, least-privilege DB role, testing |
| XSS from user/AI text | Session/data compromise | Output escaping, Markdown sanitization, CSP and tests |
| Secrets in logs/source | Account/provider compromise | Secret manager, scanning, redaction, rotation |
| Database connection context leak | Cross-user data access | Transaction-local context, pool reset, identity-isolation integration tests |
| Public endpoint abuse/cost attack | Availability and spend impact | Rate limiting, quotas, payload bounds, monitoring |

## 12. Security verification gates

Before MVP release:

- No unresolved critical/high severity security findings.
- JWT, role and event isolation tests pass.
- RLS policy tests prove allowed and denied access for authenticated and public contexts.
- Pooled DB connection context does not leak between users or public requests.
- Public registry endpoints expose only allow-listed fields.
- Gift reservation and contribution concurrency tests pass.
- Prompt-injection and unsafe-output tests pass.
- Secrets scan and dependency vulnerability scan pass.
- Production secrets, backups, logging redaction, rate limits and HTTPS are configured.

---

## Phase 1 Implementation Notes

Controls implemented and verified in Phase 1:

* Asymmetric JWT verification with an algorithm allow-list, issuer, audience, expiry and role checks;
  tests cover `alg=none`, key confusion and tampering.
* Transaction-local database identity (`set_config(..., true)`), a dedicated NOBYPASSRLS role, startup
  refusal of privileged roles, pool reset on connection return, and a pool-of-one leakage test.
* RLS on every table, column-level grants, no DELETE for the runtime role, append-only audit log.
* HTTP-only, SameSite=Lax, Secure cookies; server-only Supabase client; BFF origin checks and route
  allow-list; validated post-login redirect targets.
* Security headers on the web app (CSP, frame denial, nosniff, referrer policy, HSTS in production) and API.
* Request size limits, structured logs without headers or bodies, error envelope without internals.
* Dependency pinning with lockfiles, `npm audit` and `pip-audit` in CI, secret scan in CI.

Known limitations (tracked for later phases):

* The web CSP allows `'unsafe-inline'` scripts because Next.js emits inline bootstrap scripts; a
  nonce-based CSP is a hardening follow-up.
* Application-level rate limiting is not implemented; Supabase Auth rate limits protect sign-in and
  sign-up, and a gateway or WAF should rate-limit the API in production.
* Listing members of an event, invitations and role changes are not implemented (database model is ready).

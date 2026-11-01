# UtsavAI — REST API Specification

**Version:** 1.0  
**Date:** 31 October 2026  
**Base path:** `/api/v1`  
**Transport:** HTTPS, JSON, UTF-8

## 1. API conventions

### 1.1 Authentication

- Private endpoints require `Authorization: Bearer <Supabase access token>` after the Next.js BFF has validated the user's server-side session.
- FastAPI verifies the token signature, issuer, audience, expiry and subject. Never accept `user_id` from a request body as proof of identity.
- Public GiftCircle endpoints use a high-entropy share token in the URL path. The token is a bearer capability and is never logged.
- Authentication endpoints (sign-up, sign-in, sign-out, password recovery and session refresh) are provided by Supabase Auth, not reimplemented in FastAPI.

### 1.2 Headers

| Header | Use |
|---|---|
| `Authorization` | Supabase bearer JWT for private routes |
| `Content-Type: application/json` | JSON request bodies |
| `Accept: application/json` | JSON responses |
| `X-Request-ID` | Optional client correlation ID; backend validates length/format or generates one |
| `Idempotency-Key` | Required for replay-sensitive create/accept operations |
| `If-Match` | Optional/required revision precondition for event-level updates; format `"<revision>"` |

### 1.3 Response conventions

- Successful reads/writes return resource JSON or a documented envelope.
- List responses use `{ "data": [...], "next_cursor": null }`.
- Create responses normally return `201 Created`; updates return `200 OK`; deletes return `204 No Content`.
- Monetary values are decimal strings, not JSON floating-point numbers, and include a currency code.
- All timestamps are ISO 8601 UTC strings; clients display them in the event time zone.
- Resource identifiers are UUID strings.

### 1.4 Error envelope

```json
{
  "error": {
    "code": "RESOURCE_CONFLICT",
    "message": "This gift has already been reserved.",
    "details": { "resource_id": "uuid" },
    "request_id": "req_01..."
  }
}
```

| HTTP | Meaning | Common codes |
|---:|---|---|
| 400 | Malformed request | `INVALID_REQUEST` |
| 401 | Missing/invalid/expired authentication or public capability | `UNAUTHENTICATED`, `INVALID_SHARE_LINK` |
| 403 | Authenticated but not permitted | `FORBIDDEN` |
| 404 | Resource absent or intentionally hidden | `NOT_FOUND` |
| 409 | Stale revision, duplicate reservation, idempotency mismatch or capacity conflict | `REVISION_CONFLICT`, `RESOURCE_CONFLICT`, `IDEMPOTENCY_CONFLICT`, `CAPACITY_EXCEEDED` |
| 422 | Field/domain validation failed | `VALIDATION_ERROR`, `INVALID_DEPENDENCY`, `INVALID_STATE_TRANSITION` |
| 429 | Rate limit exceeded | `RATE_LIMITED` |
| 502/503 | Upstream AI/database dependency unavailable | `AI_PROVIDER_ERROR`, `DEPENDENCY_UNAVAILABLE` |

Do not reveal whether a private resource exists when the caller has no permission; use a consistent 404 response where appropriate.

## 2. Core resource contracts

### 2.1 Event response

```json
{
  "id": "b8d2f1b4-28e4-4b77-a9a4-5f26dc8cbade",
  "event_type": "wedding",
  "title": "Aarav and Meera's Wedding",
  "start_at": "2027-02-12T10:00:00Z",
  "end_at": "2027-02-14T22:00:00Z",
  "timezone": "Asia/Kolkata",
  "location": { "name": "Jaipur", "city": "Jaipur", "region": "Rajasthan", "country_code": "IN" },
  "expected_guest_count": 300,
  "currency": "INR",
  "status": "planning",
  "revision": 4,
  "created_at": "2026-10-31T07:30:00Z",
  "updated_at": "2026-10-31T08:00:00Z"
}
```

### 2.2 Money contract

```json
{ "amount": "1500000.00", "currency": "INR" }
```

The API accepts canonical decimal strings with at most two decimal places for MVP currencies. It rejects NaN, Infinity, negative amounts where prohibited and currency mismatches.

## 3. Identity and profile

| Method | Endpoint | Purpose | Auth |
|---|---|---|---|
| GET | `/me` | Current profile and minimal account metadata | Required |
| PATCH | `/me` | Update display name, locale or preferred time zone | Required |

`GET /me` response:

```json
{
  "user_id": "uuid",
  "display_name": "Meera",
  "preferred_locale": "en-IN",
  "timezone": "Asia/Kolkata"
}
```

## 4. Events and shared context

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/events` | Create event and owner membership |
| GET | `/events` | List current user's events |
| GET | `/events/{event_id}` | Get event details |
| PATCH | `/events/{event_id}` | Update event fields; require revision precondition |
| DELETE | `/events/{event_id}` | Archive event (not immediate hard delete) |
| GET | `/events/{event_id}/context` | Get permission-filtered event summary for workspace |
| GET | `/events/{event_id}/members` | List event memberships |
| POST | `/events/{event_id}/members` | Invite collaborator (if invite UX enabled) |
| PATCH | `/events/{event_id}/members/{user_id}` | Change role/status |
| DELETE | `/events/{event_id}/members/{user_id}` | Revoke member access |
| GET | `/events/{event_id}/preferences` | Get preferences |
| PUT | `/events/{event_id}/preferences` | Replace validated preferences |
| POST | `/events/{event_id}/functions` | Create event function |
| PATCH | `/events/{event_id}/functions/{function_id}` | Update function |
| DELETE | `/events/{event_id}/functions/{function_id}` | Remove function |

Create event request:

```json
{
  "event_type": "wedding",
  "title": "Aarav and Meera's Wedding",
  "start_at": "2027-02-12T10:00:00+05:30",
  "end_at": "2027-02-14T22:00:00+05:30",
  "timezone": "Asia/Kolkata",
  "location": { "name": "Jaipur", "city": "Jaipur", "region": "Rajasthan", "country_code": "IN" },
  "expected_guest_count": 300,
  "currency": "INR"
}
```

Update request uses only permitted fields and `If-Match: "4"`. Response returns the updated event and new revision. A stale revision returns 409.

## 5. PlanAI

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/events/{event_id}/ai/conversations` | Create conversation |
| GET | `/events/{event_id}/ai/conversations` | List current user's conversations |
| GET | `/events/{event_id}/ai/conversations/{conversation_id}` | Read conversation messages |
| POST | `/events/{event_id}/ai/conversations/{conversation_id}/messages` | Send user message and receive assistant response/proposal |
| POST | `/events/{event_id}/plans/generate` | Generate initial structured plan proposal |
| POST | `/events/{event_id}/ai/proposals/{proposal_id}/accept` | Accept selected AI proposal operations (PlanAI/TimelineAI) |

Generate plan request:

```json
{
  "request": "Suggest a three-day wedding plan for around 300 guests.",
  "include": ["functions", "tasks", "themes", "planning_notes"],
  "base_revision": 4
}
```

Response:

```json
{
  "proposal_id": "uuid",
  "status": "ready_for_review",
  "base_revision": 4,
  "summary": "A three-day outline with four suggested functions.",
  "assumptions": ["Guest count is approximate."],
  "follow_up_questions": ["Do you want a separate reception?"],
  "proposed_functions": [
    { "client_ref": "fn_1", "name": "Mehendi", "starts_at": null, "ends_at": null, "notes": "Suggested function" }
  ],
  "proposed_tasks": [
    { "client_ref": "task_1", "title": "Shortlist venues", "due_at": "2026-11-15T12:00:00Z", "priority": "high", "depends_on": [] }
  ],
  "model_metadata": { "model": "configured-model", "prompt_version": "planai-v1", "schema_version": 1 }
}
```

The response uses illustrative values. `proposal_id` identifies a durable row in `ai_proposals`; the validated structured payload is stored there with its `base_revision`, `proposal_type`, schema version and status. `model_metadata` should not expose secret provider configuration. The UI must allow the user to select which items to accept.

Accept proposal request:

```json
{
  "base_revision": 4,
  "selected_function_refs": ["fn_1"],
  "selected_task_refs": ["task_1"]
}
```

The backend maps only known proposal references from the persisted `ai_proposals` row to typed domain commands, revalidates them and commits within a transaction. The generic acceptance route is used for both PlanAI and TimelineAI proposals. An AI message alone is never an executable command.

## 6. BudgetAI

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/events/{event_id}/budget` | Get budget and categories |
| PUT | `/events/{event_id}/budget` | Create/update total limit and category allocations |
| POST | `/events/{event_id}/expenses` | Create expense |
| GET | `/events/{event_id}/expenses` | List expenses with filters |
| PATCH | `/events/{event_id}/expenses/{expense_id}` | Update expense |
| DELETE | `/events/{event_id}/expenses/{expense_id}` | Cancel/delete according to audit policy |
| GET | `/events/{event_id}/budget/summary` | Deterministic budget totals |
| POST | `/events/{event_id}/budget/suggestions` | Request AI cost-saving suggestions based on computed summary |

Budget summary response:

```json
{
  "total_limit": { "amount": "1500000.00", "currency": "INR" },
  "planned_allocation": { "amount": "1420000.00", "currency": "INR" },
  "committed": { "amount": "390000.00", "currency": "INR" },
  "paid": { "amount": "210000.00", "currency": "INR" },
  "planned_expenses": { "amount": "45000.00", "currency": "INR" },
  "remaining_against_limit": { "amount": "900000.00", "currency": "INR" },
  "allocation_warning": false,
  "over_budget": false,
  "categories": [
    { "category_key": "catering", "name": "Catering", "planned": "450000.00", "committed": "120000.00", "paid": "80000.00" }
  ],
  "calculated_at": "2026-10-31T08:00:00Z"
}
```

All values are backend-calculated from persisted decimal data. `committed` and `paid` are mutually exclusive expense states; `remaining_against_limit` equals total limit minus (committed amounts + paid amounts). Planned expenses are displayed separately and do not count as committed spend. AI suggestion response must be clearly separated from this authoritative summary.

Create expense request:

```json
{
  "budget_category_id": "uuid",
  "description": "Venue advance",
  "amount": "100000.00",
  "currency": "INR",
  "expense_date": "2026-10-31",
  "status": "committed"
}
```

## 7. TimelineAI

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/events/{event_id}/tasks` | List tasks |
| POST | `/events/{event_id}/tasks` | Create task |
| PATCH | `/events/{event_id}/tasks/{task_id}` | Update task/status/assignee |
| DELETE | `/events/{event_id}/tasks/{task_id}` | Cancel/archive task |
| POST | `/events/{event_id}/tasks/{task_id}/dependencies` | Add dependency after cycle validation |
| DELETE | `/events/{event_id}/tasks/{task_id}/dependencies/{dependency_id}` | Remove dependency |
| POST | `/events/{event_id}/timeline/generate` | Generate task/timeline proposal |

Create task request:

```json
{
  "function_id": "uuid",
  "title": "Finalize catering shortlist",
  "description": "Compare the shortlisted quotations.",
  "due_at": "2026-11-20T12:00:00Z",
  "priority": "high",
  "assigned_user_id": null,
  "depends_on_task_ids": []
}
```

## 8. VendorConnect

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/events/{event_id}/vendors` | List event vendors |
| POST | `/events/{event_id}/vendors` | Add vendor record |
| GET | `/events/{event_id}/vendors/{vendor_id}` | Read vendor record |
| PATCH | `/events/{event_id}/vendors/{vendor_id}` | Update vendor details/status |
| DELETE | `/events/{event_id}/vendors/{vendor_id}` | Archive/remove vendor |
| POST | `/events/{event_id}/vendors/{vendor_id}/quotes` | Add quotation |
| PATCH | `/events/{event_id}/vendors/{vendor_id}/quotes/{quote_id}` | Update quote |
| GET | `/events/{event_id}/vendor-quote-comparison` | Compare entered quotations |

Create vendor request:

```json
{
  "category": "catering",
  "name": "Sample Caterer",
  "contact_name": "Vendor contact",
  "email": null,
  "phone": null,
  "website_url": null,
  "notes": "Introduced by family member"
}
```

Create quote request:

```json
{
  "amount": "450000.00",
  "currency": "INR",
  "scope_summary": "Dinner catering for approximately 300 guests.",
  "valid_until": "2026-12-15"
}
```

Vendor comparisons must show quote scope, currency, date and missing fields; lowest amount alone must not be presented as the best vendor.

## 9. GiftCircle — private host endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/events/{event_id}/gift-registry` | Read registry and private management fields |
| PUT | `/events/{event_id}/gift-registry` | Create/update registry settings |
| POST | `/events/{event_id}/gift-registry/items` | Add item |
| PATCH | `/events/{event_id}/gift-registry/items/{item_id}` | Update item |
| DELETE | `/events/{event_id}/gift-registry/items/{item_id}` | Deactivate item |
| POST | `/events/{event_id}/gift-registry/share-link` | Generate/rotate share token and return raw URL once |
| DELETE | `/events/{event_id}/gift-registry/share-link` | Revoke public link |
| GET | `/events/{event_id}/gift-contributions` | Private contribution list |
| POST | `/events/{event_id}/gift-contributions/{contribution_id}/confirm` | Host confirms receipt of an offline contribution |
| PATCH | `/events/{event_id}/gift-reservations/{reservation_id}` | Host updates fulfilment status |

Create gift item request:

```json
{
  "title": "Refrigerator",
  "description": "A refrigerator for the new home.",
  "item_type": "product",
  "gift_mode": "group",
  "product_url": "https://example.com/item",
  "target_amount": "35000.00",
  "currency": "INR",
  "priority": "high_priority"
}
```

Host confirmation request:

```json
{
  "confirmation_note": "Confirmed received offline on 12 February.",
  "verification_method": "host_manual_confirmation"
}
```

Response must preserve the verification provenance. It must not claim the payment was verified by a payment provider.

## 10. GiftCircle — public guest endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/public/registries/{share_token}` | Get public-safe registry and item availability |
| POST | `/public/registries/{share_token}/items/{item_id}/reserve` | Reserve an individual gift |
| POST | `/public/registries/{share_token}/items/{item_id}/contributions` | Submit a group-gift pledge |
| POST | `/public/registries/{share_token}/reservations/{reservation_id}/cancel` | Cancel with one-time cancellation capability, if enabled |

Public registry response (safe subset):

```json
{
  "title": "Aarav and Meera's GiftCircle",
  "event_label": "Wedding celebration",
  "items": [
    {
      "id": "uuid",
      "title": "Refrigerator",
      "description": "For the new home.",
      "gift_mode": "group",
      "target_amount": "35000.00",
      "currency": "INR",
      "pledged_amount": "10000.00",
      "confirmed_amount": "5000.00",
      "remaining_amount": "20000.00",
      "status": "open"
    }
  ]
}
```

Public response must never include guest identifiers, aliases of other guests, private notes, event budget, vendor records or registry token hashes.

Reserve request:

```json
{
  "guest_alias": "A cousin",
  "idempotency_key": "unique-client-action-id"
}
```

Pledge request:

```json
{
  "guest_alias": "A friend",
  "amount": "5000.00",
  "currency": "INR",
  "idempotency_key": "unique-client-action-id"
}
```

Pledge response:

```json
{
  "contribution_id": "uuid",
  "status": "pledged",
  "amount": "5000.00",
  "currency": "INR",
  "message": "Your contribution pledge has been recorded. UtsavAI has not collected money."
}
```

A reservation/pledge endpoint must be rate-limited, idempotent, validated against the share token's registry and committed atomically. Duplicate reservation returns 409; reused idempotency key with different payload returns 409.

## 11. Adaptive Planning Engine

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/events/{event_id}/change-proposals` | Analyze requested change and build preview |
| GET | `/events/{event_id}/change-proposals/{proposal_id}` | Read proposal |
| POST | `/events/{event_id}/change-proposals/{proposal_id}/accept` | Apply approved proposal atomically |
| POST | `/events/{event_id}/change-proposals/{proposal_id}/reject` | Reject proposal |

Create proposal request:

```json
{
  "base_revision": 4,
  "request_text": "Increase guests from 300 to 450 but keep the budget at ₹15 lakh.",
  "requested_changes": { "expected_guest_count": 450 }
}
```

Preview response:

```json
{
  "proposal_id": "uuid",
  "status": "proposed",
  "base_revision": 4,
  "affected_modules": ["budget", "timeline", "vendors"],
  "affected_records": [],
  "warnings": ["Catering assumptions need review."],
  "suggested_options": [
    { "option_id": "option_1", "label": "Keep budget fixed and review optional categories", "requires_user_selection": true }
  ],
  "explanation": "The higher guest count may affect catering and venue assumptions."
}
```

Accept request:

```json
{
  "base_revision": 4,
  "selected_option_ids": ["option_1"],
  "accepted_changes": { "expected_guest_count": 450 }
}
```

The server must not trust arbitrary operations supplied by the client. It loads the stored proposal, validates selected option IDs and fields, checks revision and role, recalculates deterministic outputs and commits the allowed changes. If the event revision is no longer 4, return 409.

## 12. Pagination, filtering and sorting

List endpoints should accept a consistent query pattern:

- `limit` (default 25, maximum 100)
- `cursor` (opaque, server-generated)
- optional validated filters such as `status`, `category`, `due_before`, `due_after`
- stable sort order, normally `created_at DESC` or `due_at ASC, id ASC`

Do not interpolate user-provided sort-column names directly into SQL. Map allowed sort values to fixed query expressions.

## 13. API acceptance requirements

- OpenAPI schema is generated from FastAPI routes and Pydantic models.
- Request and response schemas are versioned and tested.
- Every private endpoint tests unauthenticated, non-member, viewer, editor and owner behavior as appropriate.
- Every public GiftCircle endpoint tests valid, invalid, expired and revoked tokens.
- Every write endpoint validates foreign-key ownership and event scope.
- Every sensitive create/accept operation supports idempotency.
- Monetary fields are decimal strings and are validated server-side.
- Error responses are stable and do not leak secrets or private resource existence.
- The TypeScript client types are generated from or checked against the OpenAPI specification; do not maintain an independent divergent contract.

---

## Phase 1 Implementation Notes

Implemented endpoints: `GET /health`, `GET /health/ready`, `GET /meta`, `GET|PATCH /me`,
`POST|GET /events`, `GET|PATCH|DELETE /events/{event_id}`. OpenAPI is generated by FastAPI and
committed at `apps/web/openapi.json`; CI fails when it is stale.

Differences and additions relative to the sections above:

1. **`If-Match` is mandatory** on `PATCH /events/{id}` (value is the event revision, quoted or bare).
   Missing header: `428 PRECONDITION_REQUIRED`. Malformed: `400 INVALID_REQUEST`. Stale: `409 REVISION_CONFLICT`
   with `details.current_revision`. `ETag` is returned on `POST`, `GET` and `PATCH`.
2. **Event responses add `my_role`** (`owner | editor | viewer`) and `archived_at`.
3. **`GET /meta`** (public, non-secret) publishes categories, currencies, statuses, transitions, locales
   and limits so the frontend never duplicates domain rules.
4. **Listing:** `limit` (1-100), opaque `cursor`, `sort` (`start_at` ascending by default, or `created_at`
   descending), `status` (repeatable) and `include_archived`. Archived events are excluded by default.
5. **Validation:** request bodies reject unknown fields (`owner_user_id`, `revision` and similar return
   `422`). A single validation problem is reported as the top-level message, for example
   "The event date range is invalid."; several are summarised with `details.fields`.
6. **Authorization responses:** a caller with no membership receives `404 NOT_FOUND` (existence is not
   revealed); a member lacking permission receives `403 FORBIDDEN`.
7. **Archived events** can be read by members. `PATCH` returns `422 INVALID_STATE_TRANSITION`. `DELETE` is idempotent.
8. **`Idempotency-Key` is not implemented in Phase 1** (the table is out of the Phase 1 scope). The UI
   prevents double submission; the header is accepted by CORS for forward compatibility only.
9. **Browser access** goes through the same-origin BFF at `/api/bff/*`, which mirrors `/me` and `/events`.

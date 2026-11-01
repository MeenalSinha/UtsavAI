# UtsavAI — User Personas and End-to-End Flows

**Version:** 1.0  
**Date:** 31 October 2026

## 1. Personas

### Persona A — Couple / host (primary)

**Context:** Planning a multi-function Indian wedding while balancing family expectations, time and a fixed budget. Often coordinates through WhatsApp and wants a practical plan rather than a complex project-management tool.

**Goals:** Create a plan quickly, understand spending, track responsibilities, compare vendor quotes, avoid duplicate gifts and adapt to changes.

**Pain points:** Information is scattered; decisions are repeated across chats; changes create hidden downstream work; the couple may not know what guests intend to gift.

**Needs:** Simple onboarding, editable recommendations, exact totals, clear status labels, mobile-friendly experience and control over guest-visible information.

### Persona B — Family planner / co-organizer

**Context:** Helps the couple manage selected tasks, quotes or schedules.

**Goals:** Know what they are responsible for, update progress and avoid changing unrelated event details.

**Needs:** Scoped access, assigned tasks and a clear audit history. Their access must be removable by the owner.

### Persona C — Guest

**Context:** Opens a GiftCircle link from a WhatsApp invitation, usually on a mobile browser.

**Goals:** Understand what the couple needs, reserve an available item or contribute towards a group gift quickly.

**Needs:** No mandatory account, simple actions, confirmation of reservation/pledge, privacy and an understandable explanation that a pledge is not a payment.

### Persona D — Professional planner (future)

**Context:** Manages several events and needs reusable workflows and delegated team access.

**MVP treatment:** Not a target persona. Event ownership and membership are designed so this can be added later without changing the core event model.

## 2. Shared design conventions

- The event is the scope boundary for planning data.
- All event dates are stored as timezone-aware timestamps where a time is required; the event's IANA time-zone identifier controls display and local date calculations.
- The host is the event owner. Collaborators receive the minimum role needed.
- AI content is labelled as a suggestion until accepted.
- Any estimate has an assumption/source note.
- Public GiftCircle views contain only explicitly public fields.
- A group-gift pledge is not a payment. The guest sees a confirmation of pledge submission, not a payment receipt.

## 3. Flow 1 — Host creates an event

**Entry:** Landing page → Sign up / Sign in → Create event.

1. User authenticates with Supabase Auth.
2. User chooses the event type (MVP enables Wedding), enters title, date range, time zone, location, expected guest count and currency.
3. Frontend validates basic inputs; FastAPI validates authoritative constraints.
4. Backend creates event, owner membership, default event preferences and initial revision in a transaction.
5. User lands on the event workspace with an onboarding checklist.

**Success state:** Event exists and is accessible only to the owner and authorized members.

**Failure states:** Invalid time zone/date range → field-level validation; duplicate/retried create → idempotency handling; unauthorized request → 401/403.

## 4. Flow 2 — Host generates a plan with PlanAI

**Entry:** Event workspace → PlanAI.

1. User enters a natural-language request, e.g. “Plan a three-day wedding for about 300 guests in Jaipur with a total budget of ₹15 lakh.”
2. Backend builds a permission-filtered context from the event and relevant module records.
3. Backend sends a constrained prompt and versioned JSON Schema to Gemini.
4. Response is parsed and validated with Pydantic, including cross-field/domain validation.
5. If invalid, backend may attempt one bounded repair/regeneration; it must not apply invalid content.
6. UI presents the draft, assumptions and follow-up questions.
7. User selects suggestions to accept. Backend revalidates the selected changes and persists them as normal records.

**Success state:** A validated proposal is reviewed and selected items are saved; the user can edit them.

**Failure states:** Gemini timeout/rate limit → retryable message; invalid schema → no save; user changes event during generation → proposal marked stale if the revision no longer matches.

## 5. Flow 3 — Budget management

**Entry:** Event workspace → Budget.

1. Host sets a total limit and category allocations.
2. Backend stores monetary values as numeric decimal amounts with the event's currency.
3. Host adds expenses and selects category, date and status (planned, committed, paid or cancelled).
4. Backend calculates category totals, paid/committed totals and remaining budget from stored records.
5. UI highlights overspend and missing allocations.
6. Host may ask BudgetAI for cost-saving ideas; AI receives a computed summary and proposes options only.
7. Host edits and confirms any budget changes; backend reruns constraints and recalculates totals.

**Success state:** Every displayed total reconciles with the source expense records.

**Failure states:** Stale revision → 409; invalid amount/currency → 422; Gemini unavailable → manual budget tools remain usable.

## 6. Flow 4 — Timeline and tasks

**Entry:** Event workspace → Timeline.

1. TimelineAI receives event dates, functions, existing tasks and accepted planning assumptions.
2. It returns proposed milestones/tasks and suggested due dates.
3. Backend validates due dates, function links and dependencies; cycle detection is deterministic.
4. Host reviews and accepts selected tasks.
5. Host assigns tasks to collaborators where collaboration is enabled.
6. Task status changes are persisted and audit logged.
7. UI uses the event time zone to show due dates and overdue status.

**Success state:** Tasks are editable, dependencies are valid and status is visible.

**Failure states:** Dependency cycle or invalid date → reject affected proposal with a clear explanation; invalid assignee → 403/422.

## 7. Flow 5 — Vendor comparison

**Entry:** Event workspace → Vendors.

1. Host adds a vendor record with category, name and optional contact details.
2. Host adds one or more quotations, including amount, scope, currency and validity date.
3. Backend validates currency against the event currency and stores each quote.
4. UI compares quotes, including scope and validity, and displays missing information.
5. Host changes vendor status (identified, contacted, quoted, shortlisted, booked, declined).

**Success state:** Host can see and compare the quotes they entered.

**Failure states:** Invalid quote or currency mismatch → 422; expired quote is labelled based on its validity date, not silently treated as available.

## 8. Flow 6 — Host creates and shares GiftCircle registry

**Entry:** Event workspace → GiftCircle.

1. Host creates registry settings and chooses whether the registry is public, group gifting is enabled and the link expiry (if supported in MVP).
2. Host adds items, choosing individual reservation or group gifting and entering any target amount.
3. Backend validates values and persists items.
4. Backend generates a cryptographically random high-entropy share token; only its hash is stored.
5. Host copies the link into a digital invitation or WhatsApp message.
6. Host can revoke or rotate the link. A revoked/expired link returns a generic unavailable response.

**Success state:** Registry is shareable without exposing private event data.

## 9. Flow 7 — Guest reserves an individual gift (no account)

**Entry:** Guest taps public GiftCircle link on mobile.

1. Browser opens `/g/{share_token}`.
2. Backend validates token hash, registry status and expiry; rate limits public access.
3. Public-safe item list is returned. The page does not request login.
4. Guest selects an available individual item and optionally enters a display alias.
5. Backend performs an atomic reservation operation. A partial unique index permits at most one active reservation per item.
6. Guest receives a reservation confirmation and a high-entropy cancellation capability if cancellation is supported.
7. Registry view updates to show the item as reserved, without exposing other guests' personal data.

**Success state:** One active reservation exists and duplicate concurrent attempts receive a conflict response.

**Failure states:** Link invalid → generic unavailable page; item already reserved → show updated availability; request throttled → retry later; request replay → idempotency key prevents duplicate action.

## 10. Flow 8 — Guest pledges to a group gift (no account)

**Entry:** Public registry → Group gift item.

1. Guest sees target amount, confirmed amount and/or available contribution capacity according to registry display settings.
2. Guest enters a positive pledge amount and optional alias.
3. Backend locks or atomically updates the relevant group-gift accounting row and checks remaining capacity.
4. A contribution record is created with status `pledged`.
5. Guest receives a pledge confirmation that explicitly says no money was collected by UtsavAI.
6. Host sees the pledge in a private reconciliation view.
7. If an offline transfer/gift is received, host can mark it `verified` with method `host_manual_confirmation`; audit log records who confirmed it and when. This is a host attestation, not payment-provider verification.

**Success state:** Pledge and received/confirmed values are distinct in storage and UI.

**Failure states:** Target capacity reached → 409 with current remaining capacity; malformed amount → 422; duplicate request → idempotent response.

## 11. Flow 9 — Host reconciles gifts

1. Host opens private GiftCircle management.
2. Host can see individual-item reservation status and group-gift pledges.
3. Host records offline receipt/confirmation with optional private note.
4. Backend requires the host's authorized role, records verification method and actor, and writes audit log.
5. Public view updates only to the configured aggregate/status; no private note or guest contact information is exposed.

## 12. Flow 10 — Adaptive replanning after a change

**Example:** Guest count increases from 300 to 450 while the budget ceiling remains fixed.

1. Host submits a change request with the current event revision.
2. Backend validates the requested field changes and builds a current event context snapshot.
3. Deterministic impact rules identify affected modules and records (for example catering assumptions, seating/venue tasks, budget categories and deadlines).
4. AI may provide human-readable rationale or alternative ideas, but cannot authoritatively calculate new totals.
5. Backend returns a change proposal with affected items, before/after values, warnings and optional suggested changes.
6. Host accepts or rejects. Preview alone does not mutate domain records.
7. On acceptance, backend starts a transaction, checks `base_revision`, checks permissions and domain constraints, applies only accepted change operations, increments revision and appends audit events.
8. If the revision changed since preview, return 409 and require a fresh preview.

**Success state:** Host understands the impact and explicitly approves a consistent update.

## 13. Role and access matrix

| Action | Owner | Editor collaborator | Viewer collaborator | Public guest |
|---|---:|---:|---:|---:|
| Read private event workspace | Yes | Yes | Yes | No |
| Edit event settings | Yes | Limited/No by default | No | No |
| Manage budget and tasks | Yes | Yes | No | No |
| Manage vendors | Yes | Yes | No | No |
| Manage registry/items | Yes | Optional owner-only initially | No | No |
| View public registry | Yes | Yes | Yes | Yes, via valid link |
| Reserve individual gift | No special guest account needed | No special guest account needed | No special guest account needed | Yes |
| Pledge group gift | No special guest account needed | No special guest account needed | No special guest account needed | Yes |
| Verify/reconcile a pledge | Yes | Owner-only initially | No | No |
| Revoke public registry link | Yes | No | No | No |

## 14. UX and accessibility acceptance notes

- All primary host journeys must work at mobile widths without horizontal page scrolling.
- Public registry actions must have clear labels, visible focus and confirmation feedback.
- Form errors must be associated with their fields and announced to assistive technology.
- Status must never be indicated by color alone.
- Guest-facing content must explain “pledged” versus “received/confirmed” in plain language.
- The guest flow should not force account creation, app installation or unnecessary personal-data collection.

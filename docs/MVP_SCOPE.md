# UtsavAI — MVP Scope and Prioritization

**Version:** 1.0  
**Date:** 31 October 2026

## 1. MVP objective

Deliver one coherent, demonstrable Indian wedding-planning journey in which an authenticated host creates an event, receives an editable AI-generated plan, manages deterministic budget and timeline data, records vendor quotations, shares a public gift registry and previews the impact of a requirement change.

The MVP must prove that the modules share one event context. It must not attempt to become a complete wedding marketplace or payment platform.

## 2. In-scope capabilities

| Capability | MVP behavior | Priority |
|---|---|---:|
| Authentication | Supabase Auth sign-up, sign-in, sign-out and session refresh | Must |
| Event workspace | Create, view, update and archive a wedding event; capture date/time zone, location, budget currency and guest count | Must |
| PlanAI | Generate a draft plan and ideas from event context; validate structured output; let user accept selected proposals | Must |
| BudgetAI | One event budget, categories, planned/committed/paid expenses, exact summary and overspend warnings | Must |
| TimelineAI | Tasks, due dates, status, priority, assignee and task dependencies; generate draft tasks | Must |
| VendorConnect | Event-scoped vendor shortlist, user-entered contacts, quotes, statuses and comparison | Must |
| GiftCircle registry | Create/edit a registry, add gifts, share/revoke public link | Must |
| GiftCircle guest flow | Guest views registry without login, reserves individual item or pledges to group gift | Must |
| Gift reconciliation | Host manually records offline receipt; store confirmation method and actor | Must |
| Adaptive Planning | Preview impact of guest-count/date/budget/function changes; accept/reject; atomic application | Must |
| Audit trail | Record material mutations, role changes, gift reservations and pledge confirmations | Must |
| Responsive/accessibility | Core host and guest journeys support mobile and keyboard use | Must |
| Collaborators | Database roles owner/editor/viewer; basic invitation flow if time permits | Should |

## 3. Explicitly out of scope

- Payment collection, UPI checkout, card processing, escrow, payouts, refunds and automated payment webhooks.
- Public vendor marketplace, vendor self-service accounts, vendor verification, ranking and review systems.
- Live vendor availability, venue inventory, product price feeds or inventory synchronization.
- Automated purchase of gifts or vendor services.
- RSVP management, seating plans, guest lists with meal preferences, transport and accommodation bookings.
- Native mobile applications; the web experience is responsive and link-friendly.
- Full event communications suite, bulk WhatsApp/SMS sending or email campaign management.
- Advanced AI agents, autonomous tool execution, long-running agent loops or multi-agent orchestration.
- Multi-currency budgets or currency conversion.
- Accounting, GST, invoicing, tax calculations or legal contract management.
- Public user-generated event feeds, social networking or guest chat.
- Professional planner agency workspaces and multi-client portfolio management.
- Image-generation for invitations/decor and uploaded document OCR.

## 4. MVP module definition

### 4.1 PlanAI

**Inputs:** event type, date range, timezone, location, expected guest count, functions, style preferences, cultural context supplied by the user, budget summary and user's message.

**Outputs:** structured suggestions for functions, tasks, themes, planning notes, assumptions and follow-up questions.

**Guardrails:** outputs are proposals. AI cannot create or modify persisted records directly. Unsupported external facts must be presented as suggestions, not verified facts.

### 4.2 BudgetAI

**Inputs:** event budget, categories, expense records and user constraints.

**Outputs:** deterministic budget summary plus optional AI explanation and cost-saving ideas.

**Guardrails:** monetary amounts use decimal/numeric storage, never binary floating-point for persisted calculations. AI cannot produce authoritative totals. The backend computes all totals and validates all changes.

### 4.3 TimelineAI

**Inputs:** event dates, functions, task list, task dependencies and milestone rules.

**Outputs:** draft task list and suggested due dates.

**Guardrails:** server validates dates, time zone, dependency references and cycles. AI-proposed due dates are not saved until accepted.

### 4.4 VendorConnect

**Inputs:** host-entered vendor details, categories and quotations.

**Outputs:** sortable comparison of submitted quotes and a shortlist status.

**Guardrails:** do not label a vendor as verified or available unless a future verification integration establishes that fact. The MVP stores information supplied by the host.

### 4.5 GiftCircle

**Inputs:** couple-created registry items, public share-link token and optional guest alias.

**Outputs:** public registry, reservation state, group-gift pledged totals and host-side reconciliation view.

**Guardrails:** no guest account; no payment collection; pledged amount is not received money. Host confirmation must be labelled as manual/offline confirmation. Provider verification is reserved for a future payment integration.

### 4.6 Adaptive Planning Engine

**Inputs:** proposed change, current event revision and current related records.

**Outputs:** deterministic impact map plus optional AI explanation/recommendations.

**Guardrails:** no mutation during preview. Acceptance requires explicit host confirmation, fresh revision and all domain validations. Stale proposals return HTTP 409 and must be regenerated.

## 5. MVP release slices

| Slice | Includes | Done when |
|---|---|---|
| A — Foundation | Auth, event CRUD, event members/roles, database migrations, design system shell | A user can securely create and reopen an event. |
| B — Planning core | PlanAI prompt flow, schema validation, proposal review/acceptance | A natural-language request generates a validated editable plan. |
| C — Operational planning | Budget and timeline services/UI | Totals, expenses, task dependencies and due dates pass deterministic tests. |
| D — Vendor records | Vendor shortlist and quote comparison | The host can compare entered quotes and manually track booking status. |
| E — GiftCircle | Public registry, reservation, group pledge, host reconciliation | Guest flow works without login and concurrent requests are safe. |
| F — Adaptation | Change impact preview, acceptance and revision checks | Guest/date/budget changes update the approved affected records only. |
| G — Release readiness | Integration/E2E/security/accessibility tests, observability and deployment | All release gates pass and demo data is isolated from real user data. |

## 6. Future roadmap candidates

| Future feature | Reason to defer |
|---|---|
| Payment gateway and webhook reconciliation | Requires provider selection, compliance review, refund/dispute handling and reliable idempotency. |
| Public vendor directory and verified profiles | Requires vendor onboarding, verification operations, ranking policy and abuse controls. |
| RSVP and guest management | Significant personal-data, invitation and attendance workflow expansion. |
| Digital invitations and WhatsApp provider integration | Shareable public links are sufficient for MVP; outbound messaging needs provider/consent design. |
| Multi-currency and internationalization | Adds exchange-rate source, conversion date and accounting semantics. |
| Multi-event planner workspace | Requires agency-level tenancy, billing and delegated administration. |
| Product catalogue and affiliate commerce | Requires current catalogue feeds, product attribution, price freshness and commercial disclosures. |
| AI-generated invitation/decor imagery | Adds image-generation cost, moderation, asset storage and licensing considerations. |
| Advanced analytics and forecast models | Needs sufficient quality historical data and evaluation criteria. |
| Guest thank-you automation | Requires contact collection, message consent and delivery provider. |
| Calendar integration and reminders | Requires OAuth scopes, sync conflict handling and provider-specific testing. |

## 7. Scope control rules

1. A feature is not MVP merely because it appears in a UI mockup; it must have a real backend contract, persistence and tests.
2. Avoid placeholder AI responses presented as real output. Demo fixtures must be visibly labelled as demo data.
3. Do not introduce microservices, message queues or workflow engines unless a measured MVP requirement demands them.
4. Do not add a payment form until provider integration, payment states, webhook verification and refund policy are designed.
5. Keep product recommendations and estimates labelled with their source and freshness.
6. Build the smallest end-to-end path before adding advanced configuration.

## 8. MVP acceptance gates

- A new host can create a wedding event and generate a structured plan.
- A host can edit and save categories/expenses; displayed totals match independent calculations exactly.
- A host can create and track tasks; invalid dependency cycles are rejected.
- A host can store vendor quotes and compare like-for-like fields.
- A guest can open a public registry without authentication and cannot access private event records.
- A concurrent test cannot create two active reservations for one individual gift.
- A concurrent test cannot over-pledge a group gift beyond its target.
- Pledged contributions remain unverified until a host-confirmation action or a future provider webhook; the MVP UI clearly distinguishes these.
- Adaptive preview does not mutate state; acceptance is revision-checked and atomic.
- AI unavailability does not break ordinary event, budget, timeline, vendor or gift management.
- Critical flows meet keyboard, mobile layout and screen-reader labeling checks.

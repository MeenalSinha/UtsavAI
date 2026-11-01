# UtsavAI — Product Requirements Document

**Document status:** Phase 0 baseline  
**Version:** 1.0  
**Date:** 31 October 2026  
**Product:** UtsavAI  
**Initial market and persona:** Indian wedding hosts and families

## 1. Product summary

UtsavAI is a GenAI-powered celebration planning workspace. It helps a host turn natural-language requirements into an actionable event plan, then coordinate the budget, schedule, vendors and gifts in one shared event context. Its defining capability is **controlled adaptive planning**: when a user changes an important requirement, UtsavAI identifies affected parts of the plan, explains the consequences and proposes updates. The user reviews and approves those updates; deterministic application logic—not the language model—performs calculations and state changes.

The first release is optimized for Indian weddings. The underlying event model is category-neutral so birthdays, anniversaries and community events can be added through configuration, templates and validation rules rather than a new architecture.

**Product promise:** Plan smarter. Spend better. Celebrate together.

## 2. Problem statement

Planning a multi-function wedding requires a host and family to coordinate many connected decisions: guest count, budget, venue, food, vendors, function schedules, tasks and gifts. These decisions are commonly spread across spreadsheets, chat groups, notes and vendor conversations. This fragmentation makes it difficult to maintain one reliable view of the plan. A change in one area can create downstream costs or deadlines that are easy to miss.

Gift coordination is a particularly overlooked part of the experience. Couples may receive duplicate or unsuitable gifts, while guests have little visibility into what is actually needed. High-value gifts may be difficult for one guest to fund alone.

## 3. Product goals

1. Convert a host's natural-language event requirements into a useful, editable plan.
2. Give the host one source of truth for budget, tasks, schedules, vendor quotes and gift coordination.
3. Make budget and schedule calculations deterministic, explainable and testable.
4. Identify the impact of requirement changes across connected modules before applying them.
5. Make GiftCircle usable by guests through a public share link without requiring guest accounts.
6. Keep the product usable on mobile devices, including common WhatsApp-driven guest journeys.
7. Establish a modular monolith that can support additional event categories without premature microservices.

## 4. Non-goals for the MVP

- A full public vendor marketplace, vendor onboarding portal or vendor ranking marketplace.
- Payment processing, escrow, payouts, refunds or tax/invoice management.
- AI autonomously booking vendors, spending money, sending invitations or changing event data.
- Native iOS/Android applications.
- Multi-event enterprise administration or wedding-planner agency operations.
- Automated scraping or purchasing from third-party product catalogues.
- Public social feeds, guest messaging, seating charts, RSVP management or travel booking.
- A guarantee that suggested prices or vendor availability are current. Estimates must be labelled as estimates and entered or verified by users.

## 5. Users and personas

### 5.1 Primary: Couple / event host

- Planning an Indian wedding with multiple functions and a finite budget.
- Wants a clear plan, practical suggestions and a single place to track progress.
- May be comfortable with WhatsApp and mobile-first workflows but not project-management software.
- Needs to control what information is visible to guests.

### 5.2 Secondary: Family planner / co-organizer

- Helps manage tasks, vendors, budget entries or schedules.
- Needs access appropriate to their role, not necessarily full ownership.
- May use the product alongside the couple and coordinate through external channels.

### 5.3 Secondary: Wedding guest

- Opens a public GiftCircle link from a digital invitation or WhatsApp.
- Should be able to view available gifts, reserve an item or pledge a group-gift contribution without creating an account.
- Should not see the couple's private event plan, budget, vendor details or other guests' personal information.

### 5.4 Future: Professional planner / vendor

- Could manage multiple client events or maintain a business profile.
- This is not a first-release persona; the data model should not prevent later support.

## 6. Product principles

- **One event context:** all modules read from the same canonical event and its related records.
- **AI proposes; users decide:** AI output is advisory until explicitly accepted.
- **Deterministic core:** totals, availability, reservations, contribution limits and deadlines are enforced by application/database logic.
- **Privacy by default:** public guest experiences expose only the minimum fields required.
- **Explainability:** show assumptions, estimates and the reason a recommendation was made.
- **Progressive complexity:** simple default workflows first; advanced controls can be added later.
- **Accessible and mobile-first:** responsive layouts, keyboard support, clear labels and sufficient contrast.

## 7. MVP capabilities and requirements

### 7.1 Shared event workspace

- A signed-in user can create, view, update and archive an event.
- A wedding event captures title, event date range, time zone, location, expected guest count, currency and planning preferences.
- Each event has one owner and required start/end timestamps. A minimal collaborator role model is defined in the architecture; collaborator invitation UX may be deferred if delivery time is constrained.
- Every module is scoped to an event. Requests must verify membership and role before returning or changing data.
- Event state has a monotonically increasing revision used for optimistic concurrency and adaptive-plan staleness checks; material changes to planning-context records advance it, while AI chat/read operations do not.

### 7.2 PlanAI

- Accepts a natural-language description plus structured event context.
- Generates an editable first-draft plan: function suggestions, workstreams, task proposals, planning assumptions and idea recommendations.
- Returns schema-constrained data with clear assumptions and confidence/quality caveats where appropriate.
- Does not create tasks, expenses, bookings or registry items until the user accepts the relevant proposal.
- Does not invent confirmed venue/vendor availability, live market prices or factual claims about a supplier.

### 7.3 BudgetAI

- Allows the host to set a total budget and category allocations.
- Tracks planned, committed and paid expenses separately.
- Provides deterministic totals, remaining budget and category variance.
- Can ask the AI to suggest ways to reduce or reallocate costs, but all arithmetic and constraint checks are performed by backend services.
- Warns when proposed allocations or recorded expenses exceed the budget; it does not silently change the user's budget.

### 7.4 TimelineAI

- Generates draft tasks and suggested due dates from event dates and functions.
- Supports task status, priority, assignee, due date and dependencies.
- Rejects self-dependencies and cycles.
- Displays overdue and upcoming tasks using the event's time zone.
- AI-generated schedules are proposals; accepted tasks are stored as normal application records.

### 7.5 VendorConnect

- Lets the host maintain an event-scoped vendor shortlist.
- Captures vendor name, category, user-entered contact details, notes, status and quotations.
- Supports quote comparison by price, scope, currency and validity date.
- Clearly labels user-entered vendor information and does not imply external verification.
- Does not process vendor payments or make bookings in the MVP. A host may manually mark a vendor as booked.

### 7.6 GiftCircle

- One registry per event in the MVP; the schema permits future multiple-registry support if required.
- Host creates and edits gift items, including title, description, optional product URL, gift mode and target amount.
- Host generates, revokes or rotates a high-entropy public share link.
- Guests can view the public-safe registry without an account.
- A guest can reserve an individual gift. An atomic server-side operation prevents two active reservations for the same item.
- A guest can pledge a contribution to a group gift. The system prevents aggregate active pledges from exceeding the remaining target unless an explicit overfunding policy is later adopted.
- Pledges are **not payments**. The MVP does not collect money. A host can manually mark a pledge as received/confirmed offline; the record must retain that it was host-confirmed, not payment-provider verified.
- Public pages do not expose guest email addresses, phone numbers, private notes, host financial data or other guests' individual pledge details.
- Guest identity is optional and limited to a display name/alias. No guest account is required.

### 7.7 Adaptive Planning Engine

- Accepts a proposed change such as updated guest count, date, budget, location or function list.
- Computes affected records/modules using explicit dependency rules.
- Produces a change preview with impact summary, affected items, assumptions and proposed adjustments.
- Allows the host to accept or reject the proposal.
- Applying a proposal is atomic, validates permissions and constraints, and checks that the base event revision is still current.
- AI may explain and recommend changes but cannot bypass validation or commit a change.

## 8. Key user journeys

1. Host signs up, creates a wedding event and enters core requirements.
2. PlanAI generates a draft plan; host reviews and accepts selected suggestions.
3. Host sets budget categories and records expenses; BudgetAI summarizes the position and suggests options.
4. TimelineAI creates task proposals; host accepts, assigns and tracks them.
5. Host adds vendors and compares quotations.
6. Host creates a GiftCircle registry and shares its public link in a WhatsApp invitation.
7. Guests reserve individual gifts or submit group-gift pledges without accounts.
8. Host reviews reservations and pledges, manually reconciles offline gifts, and marks receipt using the correct confirmation method.
9. Host changes a material requirement; Adaptive Planning previews consequences; host approves an update.

## 9. Functional requirements

| ID | Requirement | Priority | Acceptance summary |
|---|---|---:|---|
| FR-01 | Authenticated event CRUD | Must | Owner can create/read/update/archive only their event; invalid access is denied. |
| FR-02 | Shared event context | Must | AI and modules receive a consistent, permission-filtered event context. |
| FR-03 | Structured PlanAI output | Must | Generated plan validates against a versioned schema; invalid output is not applied. |
| FR-04 | Budget calculations | Must | Totals and variances are calculated server-side from persisted monetary records. |
| FR-05 | Timeline and dependencies | Must | Tasks can be tracked; dependency cycles are rejected. |
| FR-06 | Event-scoped vendor records | Must | Quotes can be created and compared; no unsupported availability claims. |
| FR-07 | Public GiftCircle view | Must | Valid share token exposes only the active public registry fields. |
| FR-08 | Duplicate gift prevention | Must | Concurrent reservation attempts produce at most one active reservation. |
| FR-09 | Group-gift pledge tracking | Must | Active pledges are bounded atomically by remaining target. |
| FR-10 | Pledge/receipt distinction | Must | Unpaid pledges cannot be represented as verified or received. Manual confirmation records the confirmer and method. |
| FR-11 | Adaptive preview and approval | Must | A plan change is previewed and approved before being applied. |
| FR-12 | Accessibility and responsive UI | Must | Core flows work by keyboard and on narrow viewports. |
| FR-13 | Collaborator invitation UX | Should | Role-based access is supported; full invitation UX can be deferred if needed. |

## 10. Non-functional requirements

- **Security:** authenticated access, event-level authorization, least privilege, RLS, secret management, rate limits and safe public registry capabilities.
- **Reliability:** deterministic operations remain available when Gemini is unavailable; AI features return a clear retryable error rather than corrupting state.
- **Performance:** ordinary event CRUD and summaries should target p95 under 500 ms excluding network variance; AI generation is separately measured and may take longer.
- **Consistency:** critical reservations, pledges, budget mutations and accepted change proposals use database transactions and concurrency controls.
- **Maintainability:** modular monolith, typed contracts, migrations, structured logs and documented domain services.
- **Observability:** request IDs, structured errors, metrics for AI latency/token use, validation failures and public registry abuse; never log raw secrets.
- **Accessibility:** target WCAG 2.2 AA for core web flows, with keyboard navigation, semantic structure, focus visibility and non-color status cues.
- **Portability:** avoid coupling domain logic to a single LLM model or event category.

## 11. Product success measures

MVP success should be measured by task completion and correctness rather than vanity engagement:

- Percentage of test wedding scenarios that produce a valid, editable plan.
- Percentage of generated AI artefacts passing Pydantic validation on first attempt and after bounded retry.
- Exact agreement between displayed budget totals and independently computed test fixtures.
- Zero duplicate active reservations under concurrency tests.
- Zero group-gift over-pledging under concurrency tests.
- Percentage of change proposals whose affected modules match the test dependency matrix.
- Completion rate for the host's primary journey and guest's public registry journey.
- Accessibility defects found in the critical journey.

## 12. Assumptions and decisions made for Phase 0

| Area | Phase 0 decision |
|---|---|
| Initial event vertical | Indian weddings; category-neutral core event model. |
| MVP currency | One ISO 4217 currency per event; default INR. No multi-currency conversion. |
| Time zone | Required IANA time-zone identifier; display and due-date rules use event time zone. |
| Guest accounts | Not required for public GiftCircle interactions. |
| Payments | No payment gateway in MVP. Pledges and host-confirmed offline receipt are separate states. |
| Vendor data | Entered by the host; not externally verified. |
| AI authority | Suggestion-only. User confirmation and deterministic validation required for mutations. |
| Availability/pricing | No live vendor/product catalogue in MVP; user-supplied quotes and estimates only. |
| Collaboration | Owner-first; schema supports owner/editor/viewer. Full invite UX is lower priority than core solo-host flows. |
| Data retention | User can delete/archive an event; retention and deletion workflow must be finalized before public launch. |

## 13. Open decisions before public launch

These do not block the architecture baseline but must be resolved before production rollout:

1. Which payment provider, if any, will support real GiftCircle payments in a later phase, and who is merchant of record?
2. What is the final policy for reservation expiry and guest cancellation links?
3. What is the guest-data retention period after an event ends?
4. Which email/SMS provider will deliver collaborator invitations and reminders?
5. Will the first public launch support only INR and India, or additional markets/currencies?
6. What escalation and support process applies to disputes about offline gift receipt or vendor information?

## 14. Release definition

The MVP is ready for release candidate review when all Must requirements are implemented, critical end-to-end flows pass, no unresolved critical/high security findings remain, RLS and concurrency tests pass, AI outputs are validated and user-approved, public GiftCircle access is privacy-reviewed, and documentation/deployment configuration is complete.

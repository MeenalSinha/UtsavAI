# Atomic Application Design & Transaction Guarantees

**Version:** 1.0.0  
**Date:** 1 November 2026  

---

## 1. Principle of Atomicity

Cross-module replanning must never leave an event in a partially updated or corrupt state (e.g. guest count updated in `events`, but budget limit failed, or tasks shifted while functions failed to add).

All operations in `accept_change_proposal` execute strictly inside a single PostgreSQL transaction block. If any step fails, the entire transaction rolls back cleanly.

---

## 2. Transaction Sequence

```text
Host (Owner) ───► POST /events/{id}/change-proposals/{id}/accept
                          │
  ┌───────────────────────▼────────────────────────────────────────┐
  │ BEGIN TRANSACTION (Isolated, caller RLS context)               │
  │                                                                │
  │ 1. Lock Event:                                                 │
  │    SELECT * FROM events WHERE id = :event_id FOR UPDATE;       │
  │                                                                │
  │ 2. Lock Proposal:                                              │
  │    SELECT * FROM change_proposals WHERE id = :prop_id          │
  │    AND event_id = :event_id FOR UPDATE;                        │
  │                                                                │
  │ 3. Guard Checks:                                               │
  │    - Is caller owner? (Raises 403 if not)                      │
  │    - Is proposal status 'proposed'? (Raises 400 if not)        │
  │    - Is event.revision == proposal.base_revision?              │
  │      (If mismatched: UPDATE status='stale', raise 409 Conflict)│
  │                                                                │
  │ 4. Apply Primary Mutations:                                    │
  │    - UPDATE events SET guest_count, dates, location            │
  │      (Triggers events_before_update: revision = revision + 1)  │
  │    - UPDATE budgets SET total_limit = :new_limit (if present)  │
  │    - INSERT / UPDATE / ARCHIVE event_functions (if present)    │
  │                                                                │
  │ 5. Apply Selected Secondary Mitigations:                       │
  │    - Shift task due dates: UPDATE tasks SET due_at = ...       │
  │    - Extend registry expiry: UPDATE gift_registries ...        │
  │    - Record review checkpoints for budget and vendors          │
  │                                                                │
  │ 6. Finalize Proposal Status:                                   │
  │    - UPDATE change_proposals SET status = 'accepted',          │
  │      accepted_at = now(), accepted_revision = :new_rev;        │
  │    - UPDATE other pending proposals SET status = 'stale';      │
  │                                                                │
  │ 7. Audit Logging:                                              │
  │    - INSERT INTO audit_logs (action = change_proposal.accepted)│
  │                                                                │
  │ COMMIT TRANSACTION                                             │
  └───────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
            HTTP 200 OK (ChangeProposalOut)
```

---

## 3. Rollback Behavior

Any SQL exception, constraint violation (e.g. `end_at < start_at`), or unexpected error causes PostgreSQL to immediately abort the transaction. No partial writes survive.

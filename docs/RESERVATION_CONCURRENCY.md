# Gift Reservation Concurrency & Anti-Collision Architecture

## 1. The Multi-Guest Collision Problem

During active wedding invitations, hundreds of guests may view the registry simultaneously. Multiple guests may click "Reserve Gift" on the same physical item within milliseconds of each other. 

GiftCircle provides deterministic guarantees that:
1. An individual gift item can be actively reserved by **at most one guest**.
2. Concurrent reservation attempts are serialized at the database level.
3. The winning reservation succeeds, and all other concurrent attempts receive an immediate `409 Conflict` error without corrupted state.

---

## 2. Multi-Layer Collision Prevention

### Layer 1: Partial Unique Index
PostgreSQL enforces a partial unique constraint on active reservations:

```sql
create unique index idx_unique_active_gift_reservation
  on public.gift_reservations (gift_item_id)
  where status = 'reserved';
```

Any attempt to insert a second active reservation for the same gift item is rejected by PostgreSQL with a `unique_violation` constraint error (`23505`).

### Layer 2: Row-Level Locking (`SELECT ... FOR UPDATE`)
Before checking eligibility or inserting, the repository acquires an exclusive row lock on the target gift item:

```sql
select id, registry_id, gift_mode, is_active, target_amount, currency
from public.gift_items
where id = %s
for update;
```

This ensures that concurrent requests for the same item are processed sequentially rather than concurrently.

### Layer 3: Application Pre-check and Exception Mapping
If `active_reservation` exists, the service immediately aborts with `ConflictError("This gift has already been reserved by another guest.")`. If a race condition reaches the insert phase, the database `unique_violation` is cleanly mapped to a 409 Conflict.

---

## 3. Reservation Expiry & Release Lifecycle

Reservations maintain a deterministic state machine:
- `reserved`: The item is claimed by a guest.
- `cancelled`: The guest released the item using their cancellation code, or the host released it from the private dashboard.
- `expired`: Time-limited hold has lapsed without fulfillment (if an expiration timestamp was configured).
- `fulfilled`: The gift was delivered or received on wedding day.

When a reservation transitions from `reserved` to `cancelled` or `expired`, the partial unique index immediately permits new guest reservations.

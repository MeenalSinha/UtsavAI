# Group Gifting Accounting & Capacity Enforcement

## 1. Principles of Group Gifting

Group gifts allow friends, coworkers, or extended family to collaboratively contribute towards honeymoon funds, expensive heirloom appliances, or celebration experiences.

Financial integrity principles:
1. **Capacity Cap**: The total of all open pledges plus verified receipts must never exceed the host-defined `target_amount`.
2. **Deterministic Arithmetic**: All amounts are represented and calculated using PostgreSQL `NUMERIC(12,2)` and Python `Decimal`. Floating-point numbers are strictly prohibited.
3. **Pledges vs Receipts**: A guest pledge is a declaration of intent, not an executed transaction. It does not touch credit cards or bank APIs.
4. **Offline Host Verification**: The host confirms receipt when gifts or funds are handed over in person or via direct personal settlement.

---

## 2. Capacity Invariant Formula

For any group gift item with a target amount $T$:

$$\text{Pledged} = \sum_{\text{status} = 'pledged'} \text{amount}$$

$$\text{Verified} = \sum_{\text{status} = 'verified'} \text{amount}$$

$$\text{Total Contributed} = \text{Pledged} + \text{Verified}$$

$$\text{Remaining Capacity} = \max(0.00, T - \text{Total Contributed})$$

When a guest attempts to pledge an amount $P$:

$$\text{Valid if and only if } P \le \text{Remaining Capacity}$$

If $P > \text{Remaining Capacity}$, the request is rejected with `409 Conflict`:
`"Your pledge of ₹P exceeds the remaining target capacity of ₹Remaining."`

---

## 3. Concurrency Protection under Concurrent Pledges

To prevent race conditions where two concurrent guests pledge amounts that individually fit but collectively exceed the remaining capacity:
1. The transaction acquires an exclusive row-level lock on the `gift_items` row:
   ```sql
   SELECT id, target_amount, currency FROM public.gift_items WHERE id = %s FOR UPDATE;
   ```
2. The current sum of `pledged` and `verified` contributions is computed while holding the lock.
3. The remaining capacity is evaluated.
4. If valid, the new contribution is inserted with `status = 'pledged'`.
5. The row lock is released upon transaction commit.

This guarantees strict serializability of group gift contributions without deadlocks.

---

## 4. Idempotency Protection

To protect against duplicate pledges caused by network timeouts or impatient double-clicks, every public contribution requires an `idempotency_key` (UUID):
- Stored in `public.idempotency_records` alongside the SHA-256 hash of the request parameters.
- Replaying the same key with identical parameters returns the cached 201 response.
- Replaying the same key with different parameters returns a 409 Conflict.

# Public Access Security Architecture

## 1. Zero-Trust Token Strategy

Wedding gift registries must be accessible to extended families, distant relatives, and wedding guests without forcing them to create an account, verify an email, or install software. At the same time, registries contain personal celebration details and must remain protected against unauthorized enumeration and cross-event data leaks.

To satisfy both requirements, GiftCircle implements a **Hash-Only Capability Token** architecture.

---

## 2. Token Lifecycle & Storage Rules

1. **Generation**:
   - A raw token is generated using Python's `secrets.token_urlsafe(32)`, providing 256 bits of cryptographically secure entropy.
2. **Hashing**:
   - The token is hashed with SHA-256 (`hashlib.sha256(token.encode()).hexdigest()`) to yield a 64-character lowercase hex digest.
3. **Database Storage**:
   - Only the 64-character hex digest is stored in `public.gift_registries.share_token_hash`.
   - The raw token is **never stored**, **never logged**, and **never returned** by read APIs (`GET /events/{event_id}/gift-registry`). It is only transmitted once to the host when generated or rotated.
4. **Immediate Invalidation**:
   - When a host rotates or revokes a share link, the `share_token_hash` is either overwritten with a new hash or set to `NULL` (and `revoked_at` is set to `now()`).
   - Any guest attempting to access the old URL will immediately receive a generic `404 Not Found`.

---

## 3. PostgreSQL Capability-Based RLS

Public guest requests are processed through `Database.public_transaction(share_token_hash, request_id)`:

```sql
SELECT set_config('app.share_token_hash', %s, true);
```

The database enforces capability-based Row-Level Security:

```sql
create or replace function app.current_share_token_hash() returns text as $$
  select current_setting('app.share_token_hash', true);
$$ language sql stable;

create policy guest_read_registry on public.gift_registries
  for select to utsavai_app
  using (
    status = 'active'
    and is_public = true
    and share_token_hash is not null
    and share_token_hash = app.current_share_token_hash()
    and (expires_at is null or expires_at > now())
  );
```

Items, reservations, and contributions inherit this capability restriction by checking membership in an active, non-expired registry matching `app.current_share_token_hash()`.

---

## 4. Guest Cancellation Token Security

When an individual gift is reserved, a separate random 32-byte secret is generated:
- The secret is hashed with SHA-256 and stored in `gift_reservations.cancellation_token_hash`.
- The raw secret is returned only to the guest who performed the reservation.
- To cancel or release the reservation, the guest must supply this cancellation secret.
- This prevents malicious or accidental releases by unauthorized visitors.

---

## 5. Security Invariants
- Zero `SECURITY DEFINER` procedures.
- Zero `BYPASSRLS` roles.
- Zero `DELETE` table grants for `utsavai_app`.
- Public guest actions are recorded in `public.audit_logs` with `actor_type = 'public_guest'` and `actor_user_id = NULL`.

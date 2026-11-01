# GiftCircle API Specification

GiftCircle exposes two distinct API surfaces:
1. **Host Endpoints** (`/api/v1/events/{event_id}/gift-registry`): Authenticated endpoints guarded by Supabase JWTs and workspace role permissions (`GIFT_REGISTRY_READ`, `GIFT_REGISTRY_MANAGE`).
2. **Public Guest Endpoints** (`/api/v1/public/registries/{share_token}`): Unauthenticated endpoints guarded by capability-based RLS matching the SHA-256 hash of `share_token`.

---

## 1. Host API Endpoints

### 1.1 Get Registry
- **Endpoint**: `GET /api/v1/events/{event_id}/gift-registry`
- **Response**: `200 OK` with `GiftRegistryOut`

### 1.2 Create Registry
- **Endpoint**: `POST /api/v1/events/{event_id}/gift-registry`
- **Body**:
  ```json
  {
    "title": "Aarav & Meera Wedding Wishlist",
    "welcome_message": "Thank you for celebrating with us!",
    "delivery_address": "123 Heritage Lane, Jaipur",
    "allow_group_gifting": true
  }
  ```
- **Response**: `201 Created`

### 1.3 Update Registry
- **Endpoint**: `PATCH /api/v1/events/{event_id}/gift-registry`
- **Body**: Partial fields (`title`, `welcome_message`, `delivery_address`, `allow_group_gifting`, `status`)
- **Response**: `200 OK`

### 1.4 Generate / Rotate Share Link
- **Endpoint**: `POST /api/v1/events/{event_id}/gift-registry/share-link`
- **Response**: `201 Created`
  ```json
  {
    "registry_id": "uuid",
    "share_token": "raw-32-byte-token",
    "share_url": "http://localhost:3000/g/raw-32-byte-token",
    "expires_at": null
  }
  ```

### 1.5 Revoke Share Link
- **Endpoint**: `DELETE /api/v1/events/{event_id}/gift-registry/share-link`
- **Response**: `204 No Content`

### 1.6 Wishlist Items CRUD
- `GET /api/v1/events/{event_id}/gift-registry/items`
- `POST /api/v1/events/{event_id}/gift-registry/items`:
  ```json
  {
    "name": "Espresso Machine",
    "description": "Dual boiler",
    "item_type": "physical",
    "gift_mode": "individual",
    "target_amount": 45000.00,
    "currency": "INR",
    "priority": "high"
  }
  ```
- `PATCH /api/v1/events/{event_id}/gift-registry/items/{item_id}`
- `DELETE /api/v1/events/{event_id}/gift-registry/items/{item_id}` (soft-deactivates `is_active = false`)

### 1.7 Reservations & Contributions
- `GET /api/v1/events/{event_id}/gift-registry/reservations`
- `POST /api/v1/events/{event_id}/gift-registry/reservations/{reservation_id}/cancel` (Host release)
- `GET /api/v1/events/{event_id}/gift-registry/contributions`
- `POST /api/v1/events/{event_id}/gift-registry/contributions/{contribution_id}/verify`:
  ```json
  {
    "verification_method": "offline_cash",
    "verification_notes": "Received cash envelope at reception"
  }
  ```

### 1.8 Overview Summary
- **Endpoint**: `GET /api/v1/events/{event_id}/gift-registry/overview`
- **Response**: `200 OK` with counts and totals (`total_pledged`, `total_verified`, item counts).

---

## 2. Public Guest API Endpoints

### 2.1 View Public Registry
- **Endpoint**: `GET /api/v1/public/registries/{share_token}`
- **Security**: No auth headers. RLS matches `sha256(share_token)` against `gift_registries.share_token_hash`.
- **Response**: `200 OK` with `PublicGiftRegistryOut`

### 2.2 Reserve Individual Gift
- **Endpoint**: `POST /api/v1/public/registries/{share_token}/items/{item_id}/reserve`
- **Body**:
  ```json
  {
    "idempotency_key": "uuid",
    "guest_alias": "Sunil Uncle",
    "notes": "Looking forward to celebrating!"
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "reservation_id": "uuid",
    "gift_item_id": "uuid",
    "cancellation_token": "64-char-raw-secret",
    "message": "Your reservation has been recorded!..."
  }
  ```

### 2.3 Cancel Reservation
- **Endpoint**: `POST /api/v1/public/registries/{share_token}/reservations/{reservation_id}/cancel`
- **Body**:
  ```json
  {
    "cancellation_token": "64-char-raw-secret"
  }
  ```
- **Response**: `204 No Content`

### 2.4 Contribute to Group Gift
- **Endpoint**: `POST /api/v1/public/registries/{share_token}/items/{item_id}/contribute`
- **Body**:
  ```json
  {
    "idempotency_key": "uuid",
    "guest_alias": "Priya & Friends",
    "amount": 25000.00,
    "currency": "INR"
  }
  ```
- **Response**: `201 Created` with `PublicContributionConfirmationOut`

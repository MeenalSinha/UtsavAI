# Shared Event Context Contract

## Purpose
The **Shared Event Context** is the authoritative, centralized data aggregation service that powers all downstream UtsavAI modules (PlanAI, BudgetAI, TimelineAI, VendorConnect, GiftCircle, Adaptive Planning Engine).

It eliminates fragmented queries and ensures consistent, tenant-isolated state projection without mutating or duplicating core PostgreSQL tables.

---

## Endpoint
`GET /api/v1/events/{event_id}/context`

### Permissions Required
* Authenticated user must have an active membership in `event_memberships`.
* Roles: `owner`, `editor`, `planner`, `viewer`.

---

## Contract Schema (`SharedEventContext`)

```json
{
  "event": {
    "id": "uuid",
    "event_type": "wedding",
    "title": "Aarav & Meera's Wedding",
    "start_at": "2027-02-12T10:00:00+05:30",
    "end_at": "2027-02-14T22:00:00+05:30",
    "timezone": "Asia/Kolkata",
    "location": {
      "name": "Jaipur Palace",
      "city": "Jaipur",
      "region": "Rajasthan",
      "country_code": "IN"
    },
    "expected_guest_count": 350,
    "currency": "INR",
    "revision": 4,
    "status": "planning"
  },
  "preferences": {
    "style_tags": ["Traditional", "Royal & Grand"],
    "cultural_context": {
      "tradition": "Hindu (North Indian / Rajasthani)",
      "regional_customs": "Marwari customs, Baaraat with Dhol",
      "special_ceremonies": "Haldi, Mehendi, Sangeet Night, Saat Phere, Reception"
    },
    "priorities": {
      "key_priorities": ["Guest Experience & Hospitality", "Traditional Authenticity"],
      "notes": "Emphasis on authentic Rajasthani catering and royal hospitality"
    },
    "accessibility_notes": {
      "accommodations": ["Dedicated seating for elderly", "Wheelchair access to mandap"],
      "additional_notes": "Ground-floor rooms for grandparents"
    },
    "schema_version": 1
  },
  "functions": [
    {
      "id": "uuid",
      "name": "Sangeet & Cocktail Night",
      "starts_at": "2027-02-12T18:00:00+05:30",
      "ends_at": "2027-02-12T23:30:00+05:30",
      "location_name": "Palace Courtyard",
      "notes": "Live Rajasthani folk music and DJ",
      "sort_order": 1
    }
  ],
  "permissions": {
    "role": "owner",
    "can_edit": true,
    "can_generate_plan": true,
    "can_accept_plan": true,
    "can_manage_preferences": true,
    "can_manage_functions": true
  }
}
```

---

## Architectural Guarantees
1. **Concurrency and Stale State Guard:** The `revision` integer represents the monotonic revision counter of the parent event. Every modification to functions or preferences increments this revision. Plan proposals bind to a `base_revision`; if the event revision advances, the proposal is marked stale.
2. **Deterministic Role Filtering:** Viewers receive `can_edit: false`, `can_generate_plan: false`, `can_accept_plan: false`.
3. **No Private Leakage:** Only event-scoped operational data is exposed; no user auth credentials, hashes, or unrelated account metadata are leaked into the context payload.


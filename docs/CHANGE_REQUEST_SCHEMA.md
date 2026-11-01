# Change Request Schema & Data Contract

**Version:** 1.0.0  
**Specification Date:** 1 November 2026  

---

## 1. Overview

Adaptive planning mutations are never passed as arbitrary SQL or unvalidated key-value pairs. All change requests submitted to `POST /events/{event_id}/change-proposals` must adhere to the strongly-typed `TypedChangeRequest` schema.

---

## 2. JSON Schema Definition

```json
{
  "schema_version": 1,
  "base_revision": 3,
  "request_text": "Increase guest count from 200 to 350 and add Sangeet Celebration",
  "event_changes": {
    "expected_guest_count": 350,
    "start_at": "2027-02-15T10:00:00Z",
    "end_at": "2027-02-16T10:00:00Z",
    "timezone": "Asia/Kolkata",
    "location_name": "Rambagh Palace Grand Hall",
    "city": "Jaipur",
    "region": "Rajasthan",
    "country_code": "IN"
  },
  "budget_changes": {
    "total_limit": "2500000.00"
  },
  "function_changes": [
    {
      "action": "add",
      "name": "Sangeet Celebration",
      "function_type": "ceremony",
      "start_at": "2027-02-15T18:00:00Z",
      "end_at": "2027-02-15T23:00:00Z",
      "expected_guest_count": 350
    }
  ]
}
```

---

## 3. Field Specifications

### 3.1 Top-Level Fields
| Field | Type | Required | Description |
|---|---|---|---|
| `schema_version` | integer | Yes | Version of change schema (default: 1) |
| `base_revision` | integer | Yes | Event revision at time of generation |
| `request_text` | string | Yes | 1–4000 characters description |
| `event_changes` | object | No | Event-level attribute adjustments |
| `budget_changes` | object | No | Budget adjustments |
| `function_changes` | array | No | List of function operations |

### 3.2 Event Changes (`event_changes`)
- `expected_guest_count`: Integer between 1 and 100,000.
- `start_at`: ISO 8601 UTC timestamp.
- `end_at`: ISO 8601 UTC timestamp (must be $\ge$ `start_at`).
- `timezone`: Valid IANA timezone string.
- `location_name`: Max 160 characters.
- `city`, `region`: Max 120 characters.
- `country_code`: ISO 3166-1 alpha-2 code (2 uppercase letters).

### 3.3 Budget Changes (`budget_changes`)
- `total_limit`: Fixed-point Decimal string, 2 decimal places, $\ge 0.00$. Floating-point numbers are prohibited.

### 3.4 Function Changes (`function_changes[]`)
- `action`: One of `"add"`, `"update"`, `"archive"`.
- `function_id`: UUID (required for `"update"` and `"archive"`).
- `name`: Max 160 characters.
- `function_type`: Max 80 characters.
- `start_at`, `end_at`: ISO 8601 timestamps.
- `expected_guest_count`: Optional function-specific attendee count.

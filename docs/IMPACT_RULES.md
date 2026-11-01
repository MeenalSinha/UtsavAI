# Deterministic Impact Rules Catalog

**Version:** 1.0.0  
**Rules Engine Version:** `1.0.0`  
**Date:** 1 November 2026  

---

## 1. Design Philosophy

The Adaptive Planning Impact Engine evaluates changes deterministically using actual persisted database state from the active celebration. It never fabricates prices, vendor capacities, or task dependencies.

---

## 2. Rule Catalog

### 2.1 Event & Planning Rules (`event_rules.py`)

| Code | Trigger Condition | Severity | Calculation Item | Recommended Action |
|---|---|---|---|---|
| `WARN_EVENT_GUEST_CAPACITY_SHIFT` | Guest count change $\ge 25\%$ | `medium` ($\ge 25\%$), `high` ($\ge 50\%$) | Metric: "Guest Count" (delta) | Review vendor quotes and catering allocations to ensure venue and catering scale properly. |
| `ERR_EVENT_INVALID_DATE_RANGE` | `end_at < start_at` | `critical` | N/A | Correct event start and end timestamps so that end follows start. |
| `WARN_EVENT_DATE_SHIFT` | Shift in event start date $> 0.01$ days | `medium` ($> 0$), `high` ($> 7$ days) | Metric: "Event Schedule Shift" (days delta) | Reschedule timeline tasks and notify vendors regarding revised event dates. |
| `WARN_EVENT_LOCATION_CHANGED` | Change in location name, city, or region | `medium` | N/A | Verify venue confirmation and notify vendors about the location update. |
| `WARN_FUNCTION_ARCHIVED` | Celebration function marked for archival | `medium` | N/A | Review tasks associated with the function before completing proposal acceptance. |

---

### 2.2 BudgetAI Rules (`budget_rules.py`)

| Code | Trigger Condition | Severity | Calculation Item | Generated Options |
|---|---|---|---|---|
| `ERR_BUDGET_BELOW_COMMITTED` | Proposed total limit strictly below `committed_expenses + paid_expenses` | `critical` | Metric: "Budget Total Limit" | N/A (Blocks or severely warns host against impossible reduction) |
| `WARN_BUDGET_BELOW_PROJECTED` | Proposed limit below projected total expenses | `high` | Metric: "Projected Headroom" | Review planned expenses and allocations. |
| `WARN_BUDGET_GUEST_PRESSURE` | Guest count increased without proportional limit raise | `medium` | Metric: "Per-Guest Allocation" | `opt_flag_budget_for_review` |

---

### 2.3 TimelineAI Rules (`timeline_rules.py`)

| Code | Trigger Condition | Severity | Calculation Item | Generated Options |
|---|---|---|---|---|
| `WARN_TIMELINE_TASK_DEADLINE_OUT_OF_BOUNDS` | Active task due date falls outside revised celebration window | `high` | Metric: "Timeline Tasks To Shift" | `opt_reschedule_tasks` (shifts deadlines by date delta) |
| `WARN_TIMELINE_ORPHANED_TASKS` | Task associated with a function marked for archival | `medium` | N/A | Unlink or reassign tasks associated with the archived function. |

---

### 2.4 VendorConnect Rules (`vendor_rules.py`)

| Code | Trigger Condition | Severity | Calculation Item | Generated Options |
|---|---|---|---|---|
| `WARN_VENDOR_QUOTE_EXPIRED` | Quotation `valid_until` is earlier than revised event start date | `high` | Metric: "Expiring Vendor Quotes" | `opt_mark_vendor_quotes_review` |
| `WARN_VENDOR_GUEST_CAPACITY` | Headcount delta $\ge 25$ on catering/venue quotes | `medium` | N/A | Contact catering and venue vendors to update headcount. |

---

### 2.5 GiftCircle Rules (`gift_rules.py`)

| Code | Trigger Condition | Severity | Calculation Item | Generated Options |
|---|---|---|---|---|
| `WARN_GIFT_REGISTRY_EARLY_EXPIRY` | Public registry `expires_at` falls before revised celebration end date | `high` | Metric: "Gift Registry Expiry" (buffer days) | `opt_extend_gift_registry` (extends registry to end + 14d) |

---

## 3. Allow-Listed Operations Catalog

Secondary operations included in `suggested_options` use strict, server-side recognized operation codes:
- `op_shift_task_due_dates`: Payload `{ "shift_seconds": <int> }`.
- `op_extend_gift_registry_expiry`: Payload `{ "registry_id": <uuid>, "new_expires_at": <iso8601> }`.
- `op_flag_budget_for_review`: Payload `{ "reason": <str> }`.
- `op_mark_vendor_quotes_review`: Payload `{ "affected_quote_count": <int> }`.

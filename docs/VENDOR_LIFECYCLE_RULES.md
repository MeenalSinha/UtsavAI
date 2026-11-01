# Vendor Lifecycle & State Transition Rules

## 1. Vendor Engagement States

Vendors progress through the following discrete engagement states:

```
[identified] -> [contacted] -> [quoted] -> [shortlisted] -> [booked]
      \             \             \             \             /
       +-------------+-------------+-------------+-----------+---> [declined]
```

- `identified`: Discovered or suggested vendor; initial discovery phase.
- `contacted`: Initial conversations initiated; scope requirements shared.
- `quoted`: Official quotation or commercial estimate received.
- `shortlisted`: Candidate proposal selected for final comparison and negotiation.
- `booked`: Proposal formally accepted by the celebration hosts.
- `declined`: Vendor or proposal declined or not moving forward.

---

## 2. Quotation Decision States

Individual commercial proposals follow this state cycle:

- `received`: Initial quotation proposal entered into the system.
- `shortlisted`: Proposal marked as a top contender for the category.
- `accepted`: Proposal selected as the winning offer for the celebration.
- `rejected`: Proposal formally declined by the hosts.
- `expired`: Offer passed its validity deadline without acceptance.

---

## 3. Synchronized State Transitions

1. **Automatic Progression on Quote Entry**:
   - When a quotation is added for a vendor in `identified` or `contacted` state, the vendor automatically moves to `quoted`.

2. **Automatic Booking on Quote Acceptance**:
   - When a quotation is marked as `accepted`, the parent vendor is automatically transitioned to `booked`.

3. **Soft-Archiving Policy**:
   - Deleting a vendor from the UI or API sets `archived_at = now()`.
   - Direct SQL `DELETE` is blocked by least-privilege role permissions (no `DELETE` grant for `utsavai_app`).
   - Historical quotes and past ledger expenses referencing the vendor remain intact for financial reporting.


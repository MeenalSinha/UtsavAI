# Gift Reconciliation & Offline Settlement

## 1. Context & Wedding Day Realities

In Indian and multicultural weddings, gift giving is deeply intertwined with personal attendance, cultural shagun envelopes, and family gifting rituals:
- Guests often pledge to contribute to a group gift on the registry beforehand.
- The actual funds or gifts are presented in person during celebration functions (Sangeet, Reception) or transferred directly to the couple's personal account.
- The host needs a streamlined dashboard to reconcile which pledges were received and mark them as verified.

---

## 2. Contribution Lifecycle State Machine

```
      +-------------+
      |   pledged   |  (Guest declares intent on public registry)
      +------+------+
             |
     +-------+-------+
     |               |
     v               v
+----------+   +-----------+
| verified |   | cancelled |  (Host confirms offline receipt or guest withdraws)
+----------+   +-----------+
```

### State Definitions
- `pledged`: Guest has submitted a contribution intent. Counts towards the item's total pledged amount and reduces open target capacity.
- `verified`: Host has received the contribution in person or via direct bank transfer and verified it in the dashboard.
- `cancelled`: Pledge was released or withdrawn. Capacity is freed up for other guests.

---

## 3. Host Verification Process

When a host receives a gift or envelope:
1. Open the **GiftCircle** workspace on UtsavAI.
2. Select the **Group Pledges** tab.
3. Locate the guest's contribution row.
4. Click **Confirm Receipt**.
5. Select the offline settlement method:
   - `offline_cash`: Cash envelope / Shagun presented in person.
   - `upi_direct`: Direct UPI settlement between guest and couple.
   - `bank_transfer`: Direct IMPS / NEFT transfer.
   - `gift_card`: Store or brand gift card.
   - `other`: Other offline receipt.
6. Optionally enter settlement notes (e.g., "Envelope #14 from reception desk").
7. Click **Confirm Receipt**.

Upon confirmation:
- The contribution status updates to `verified`.
- The overview totals reflect the shift from `total_pledged` to `total_verified`.
- An audit log row is recorded (`gift_contribution.verified`).

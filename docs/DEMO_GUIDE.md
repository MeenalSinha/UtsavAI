# UtsavAI Demo Environment Guide

## 1. Overview
The UtsavAI demo environment provides an isolated, realistic, and fully populated Indian wedding planning scenario: **Aarav & Meera's Jaipur Royal Wedding**. It exercises every capability across all six modules with zero reliance on production data.

---

## 2. Quick Start

### Seeding Demo Data
To populate your local or staging database with the demo wedding:
```bash
cd apps/api
uv run python ../../scripts/seed_demo_data.py
```

### Cleaning Up Demo Data
To remove all synthetic demo records cleanly:
```bash
cd apps/api
uv run python ../../scripts/seed_demo_data.py --clean
```

---

## 3. Demo Dataset Specifications
- **Host User:** `demo.host@utsavai.test` (User ID: `d0000000-0000-0000-0000-000000000001`)
- **Event:** *Aarav & Meera's Jaipur Royal Wedding* (Event ID: `e0000000-0000-0000-0000-000000000001`)
- **Location:** Jaipur, Rajasthan, India (Rambagh Palace)
- **Budget:** ₹25,00,000.00 INR
- **Guests:** 300 expected attendees

### Included Module Data
1. **PlanAI Functions:**
   - Mehendi & Haldi Sunshine Ceremony (Day 1 Afternoon)
   - Sangeet Extravaganza & Musical Night (Day 1 Evening)
   - Vedic Royal Wedding Pheras & Baraat (Day 2 Evening)
   - Grand Gala Reception & Dinner (Day 3 Evening)
2. **BudgetAI:**
   - 5 Allocated Categories: Venue, Catering, Decor, Photography, Entertainment.
   - 3 Committed Expenses: Palace Deposit (₹4,00,000), Catering Tasting (₹1,50,000), Drone Token (₹50,000).
3. **TimelineAI:**
   - Pre-wedding milestones and dependent setup tasks with DAG scheduling.
4. **VendorConnect:**
   - 3 Vendors: Rambagh Palace, Rajputana Royal Caterers, Jaipur Royal Lens.
   - 3 Accepted Quotations with itemized deliverables.
5. **GiftCircle:**
   - Public Registry URL: `/g/demo-jaipur-aarav-meera`
   - Individual Gift: Dyson Airwrap (Reserved by Kabir & Ananya Verma)
   - Group Gift Fund: Maldives Honeymoon Suite (₹2,50,000 target, ₹50,000 verified pledge)
6. **Adaptive Planning Engine:**
   - Candidate Change Proposal: Increase guest count from 300 to 350.
   - Precalculated downstream impacts on catering budget, venue capacity warning, and suggested option.

# Deterministic Quotation Comparison Rules

## 1. Core Principles

The UtsavAI quotation comparison engine is **fully deterministic and strictly objective**:
1. **No Fabricated Scores**: It does not assign arbitrary numeric stars, subjective "quality" points, or AI-generated satisfaction indexes.
2. **Cheapest is Not Best**: It never automatically proclaims the lowest bidder as the "best" or "recommended" option, recognizing that celebration vendors differ widely in quality, scope, and inclusions.
3. **Factual Scope Discrepancy Warnings**: It detects and flags discrepancies in deliverables, guest capacities, and validity windows to empower human decision-makers.

---

## 2. Categorical Grouping & Pricing Spread

- Quotations from active vendors are grouped by normalized category (e.g. "Catering", "Photography", "Decor & Floral").
- For each category with quotations, the engine computes:
  - `price_range_min`: Lowest monetary proposal.
  - `price_range_max`: Highest monetary proposal.
- **Price Variance Warning**: If `price_range_max > 2 * price_range_min`, the engine flags:
  > *"Significant price variance across quotes in this category: highest quote (₹X) is over 2x the lowest (₹Y). Check for scope differences or premium package inclusions."*

---

## 3. Scope Deliverables & Guest Count Parity

- **Guest Count Extraction**: Uses regex `(\d+)\s*guests?` on each quote's `scope_summary`.
- If different vendors in the same category provide quotes based on differing guest counts (e.g., 200 guests vs 350 guests), the engine emits an explicit category alert:
  > *"Different guest capacities specified across proposals (e.g., 200 guests vs 350 guests). Ensure pricing is normalized per person before final selection."*

---

## 4. Missing Information Warnings

On each quotation item, the engine audits for missing commercial details:
- **Missing Validity Deadline**: If `valid_until` is null, warns: *"No offer validity deadline specified"*.
- **Incomplete Contact Data**: If the vendor record lacks both a phone number and an email address, warns: *"No contact phone or email recorded for this vendor"*.
- **Brief Scope Description**: If `scope_summary` is under 30 characters, warns: *"Brief scope description provided: confirm deliverables and exclusions directly with vendor"*.


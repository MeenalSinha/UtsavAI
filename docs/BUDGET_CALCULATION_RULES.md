# BudgetAI Calculation & Financial Integrity Rules

## 1. Absolute Precision Mandate
- **PostgreSQL Storage:** All currency fields in `budgets`, `budget_categories`, and `expenses` are strictly stored as `NUMERIC(12, 2)`.
- **Python Backend Engine:** All arithmetic is performed strictly using Python's standard `Decimal` type from the `decimal` module. Floating-point types (`float`) are completely forbidden for any financial calculation or storage.
- **Rounding Mode:** Where division or percentage conversion is necessary, calculations use standard round-half-up or maintain exact 2-decimal quantizations (`Decimal("0.01")`).

## 2. Expense Status Definition & Accounting Lifecycle

Each recorded expense carries one of four mutually exclusive statuses:

| Status | Description | Financial Weight / Inclusion |
| :--- | :--- | :--- |
| `planned` | Budgeted estimate for future quote or vendor booking. | Counted in `planned_expenses` and `projected_total`. |
| `committed` | Contract signed, invoice received, or legal obligation entered. | Counted in `committed_expenses`, `projected_total`, and deducted from `remaining_after_committed`. |
| `paid` | Cash, transfer, or card disbursement completed. | Counted in `paid_expenses`, `projected_total`, and deducted from `remaining_after_committed`. |
| `cancelled` | Quote declined or cancelled agreement. | **Excluded** from all active spend and headroom calculations. Retained for audit trail. |

## 3. Mathematical Formulas

Given an event budget with `total_limit`:

### 3.1 Total Category Allocations
$$\text{total\_allocated} = \sum_{c \in \text{active categories}} c.\text{planned\_amount}$$
$$\text{unallocated\_amount} = \text{total\_limit} - \text{total\_allocated}$$

### 3.2 Active Expense Aggregations
$$\text{planned\_expenses} = \sum_{e \in \text{expenses}, e.\text{status} = 'planned'} e.\text{amount}$$
$$\text{committed\_expenses} = \sum_{e \in \text{expenses}, e.\text{status} = 'committed'} e.\text{amount}$$
$$\text{paid\_expenses} = \sum_{e \in \text{expenses}, e.\text{status} = 'paid'} e.\text{amount}$$
$$\text{cancelled\_expenses} = \sum_{e \in \text{expenses}, e.\text{status} = 'cancelled'} e.\text{amount}$$

### 3.3 Projected Total & Headroom
$$\text{projected\_total} = \text{planned\_expenses} + \text{committed\_expenses} + \text{paid\_expenses}$$
$$\text{remaining\_after\_committed} = \text{total\_limit} - (\text{committed\_expenses} + \text{paid\_expenses})$$
$$\text{projected\_headroom} = \text{total\_limit} - \text{projected\_total}$$

- If $\text{projected\_headroom} \ge 0$, the event is safely within total budget.
- If $\text{projected\_headroom} < 0$, the projected expenses exceed the total budget limit, triggering an automated financial alert.

### 3.4 Per-Category Breakdown
For each category $c$:
$$\text{category\_spent} = \sum_{e \in \text{expenses}(c), e.\text{status} \in \{'committed', 'paid'\}} e.\text{amount}$$
$$\text{category\_projected} = \sum_{e \in \text{expenses}(c), e.\text{status} \ne 'cancelled'} e.\text{amount}$$
$$\text{category\_remaining} = c.\text{planned\_amount} - \text{category\_spent}$$
$$\text{is\_over\_budget} = \text{category\_spent} > c.\text{planned\_amount}$$

## 4. Deterministic Financial Alerts

The backend automatically emits deterministic alerts in `BudgetSummaryOut.alerts` based on numeric state:
1. **Budget Overrun Warning:** Emitted when `projected_headroom < 0`.
2. **Category Overrun Warning:** Emitted when `category_spent > category.planned_amount`.
3. **Over-Allocation Warning:** Emitted when `total_allocated > total_limit`.
4. **Unallocated Capital Notice:** Emitted when `unallocated_amount > 0`.

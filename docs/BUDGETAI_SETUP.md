# BudgetAI Setup & Integration Guide

## 1. Overview
BudgetAI provides intelligent, deterministic financial management for events in UtsavAI. It offers real-time budget ceilings, multi-category allocations, lifecycle expense tracking, automated overrun alerts, and Gemini AI-powered budget distribution recommendations.

## 2. API Endpoints

All endpoints are scoped under `/api/v1/events/{event_id}/`:

### 2.1 Budget Ceiling
- `GET /budget`: Retrieve current budget configuration and limits.
- `POST /budget`: Initialize a budget limit with currency (default `INR`).
- `PATCH /budget`: Update total limit ceiling (`total_limit: "1500000.00"`).

### 2.2 Category Allocations
- `GET /budget/categories`: List all categories with planned, spent, and remaining amounts.
- `POST /budget/categories`: Create a custom category (`category_key`, `name`, `planned_amount`).
- `PATCH /budget/categories/{category_id}`: Update planned amount or display name.
- `DELETE /budget/categories/{category_id}`: Delete category (blocked if active expenses exist).

### 2.3 Expense Management
- `GET /expenses`: List expenses with filters for `category_id`, `status`, and `search`.
- `POST /expenses`: Record an expense (`budget_category_id`, `description`, `amount`, `status`).
- `PATCH /expenses/{expense_id}`: Update expense details or progress status (`planned` $\to$ `committed` $\to$ `paid`).
- `DELETE /expenses/{expense_id}`: Soft-delete an expense.

### 2.4 Authoritative Summaries
- `GET /budget/summary`: Returns deterministic financial aggregations (`total_allocated`, `planned_expenses`, `committed_expenses`, `paid_expenses`, `projected_headroom`, `alerts`).

### 2.5 AI Budget Recommender
- `POST /budget/ai/generate`: Solicits Gemini AI to analyze event scale, preferences, and guest count to generate tailored category allocation proposals.
- `POST /budget/ai/proposals/{proposal_id}/accept`: Atomically accepts selected category recommendations and writes them to PostgreSQL.

## 3. Frontend Architecture
The user interface is accessible at `/events/{eventId}/budget`:
- **Financial Metric Cards:** Real-time summary cards for total ceiling, committed & paid, and projected headroom.
- **Progress Gauge:** Visual spending barometer with warning thresholds.
- **Allocation Manager:** Inline editing and progress bars for each expense bucket.
- **Expense Log:** Interactive table with category and status filtering.
- **AI Modal:** Conversational assistant for prompt-guided budget distribution with atomic approval.

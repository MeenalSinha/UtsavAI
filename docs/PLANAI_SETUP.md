# PlanAI Setup & Operational Guide

## Overview
PlanAI is UtsavAI's conversational wedding planning intelligence module. It synthesizes event metadata, cultural traditions, aesthetic preferences, and budget priorities into a structured itinerary and actionable task list.

### Core Philosophy
> **"AI proposes. Deterministic logic validates. Users approve. The backend executes."**

LLMs are never given write access to the PostgreSQL database. Every recommendation is produced as an immutable proposal, inspected and selectively accepted by the event owner, and committed via transactional database repositories.

---

## Architecture

```
User Request
    │
    ▼
FastAPI PlanAI Router (/api/v1/events/{id}/plans/generate)
    │
    ├─► SharedEventContext Aggregator (Database PostgreSQL 16)
    │
    ├─► Prompt Assembler (prompts/plan_generation_v1.md)
    │
    ├─► StructuredGenerationProvider (Gemini 2.5 Flash with response_schema)
    │
    ▼
Domain Validator (apps/api/app/modules/plan_ai/schemas.py)
    ├─► Pydantic V2 Schema Validation
    ├─► Client Ref Uniqueness Checks
    ├─► DAG Cycle Detection (DFS on Task Dependencies)
    ├─► Self-dependency Checks
    └─► Function Reference Integrity Checks
    │
    ▼
ai_proposals (Status: 'proposed', base_revision: current_event_revision)
    │
    ▼
Frontend Proposal Review Workspace
    ├─► User selects ceremonies & tasks via checkboxes
    │
    ▼
Acceptance Endpoint (/api/v1/events/{id}/ai/proposals/{proposal_id}/accept)
    │
    ├─► Optimistic Concurrency Check (base_revision == event.revision)
    ├─► Atomic Transaction:
    │     - INSERT into event_functions
    │     - Map client_ref -> generated UUIDs
    │     - INSERT into tasks (origin = 'ai_accepted')
    │     - INSERT into task_dependencies
    │     - UPDATE ai_proposals status = 'accepted'
    │     - Bump parent event revision & updated_at
    │     - Record audit_logs
    │
    ▼
PostgreSQL 16 Authoritative Event State
```

---

## Prompt Engineering (`apps/api/app/modules/plan_ai/prompts/`)

### 1. `plan_generation_v1.md`
- **Role:** Master Indian Wedding Planner with 20+ years of regional and cultural expertise.
- **Context Injection:** Injects event details (type, dates, location, guest count, currency), existing preferences (tradition, regional customs, ceremonies, style tags, priorities, accessibility notes), and currently configured functions.
- **Constraints:**
  - Strict JSON conforming to `PlanProposalPayload`.
  - Realistic multi-day Indian wedding scheduling (e.g. Mehendi -> Haldi -> Sangeet -> Pheras -> Reception).
  - Explicit assumption documentation (weather, indoor alternatives).
  - Practical vendor and timeline warnings (high season booking leads, sound permits, elder mobility).
  - Unique `client_ref` identifiers (e.g. `fn_mehendi`, `task_audio_sangeet`).
  - Strict DAG dependencies with zero self-references or cycles.

### 2. `conversation_v1.md`
- Handles conversational responses, wedding etiquette advice, clarification questions, and interactive planning discussions within the active conversation thread.

---

## Proposal Review & Selective Acceptance

Users have granular control over AI recommendations:
1. **Full or Selective Acceptance:** Users can choose to accept all ceremonies and tasks, or selectively check specific ceremonies (e.g. only Sangeet and Pheras) and tasks.
2. **Rejection:** Users can reject a proposal if they wish to re-prompt or discard the suggestions.
3. **Stale Revision Prevention:** If an event's details or existing functions change after a proposal is generated, the proposal becomes stale (`event.revision > proposal.base_revision`). The backend rejects attempts to accept stale proposals with HTTP 409 Conflict (`STALE_PROPOSAL`), prompting the user to regenerate based on the newest event context.

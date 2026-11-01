# TimelineAI Setup & Integration Guide

## 1. Overview
TimelineAI delivers automated task scheduling, milestone tracking, prerequisite dependency modeling, and Gemini AI schedule recommendations for Indian wedding planning workflows.

## 2. API Endpoints

All endpoints are scoped under `/api/v1/events/{event_id}/tasks`:

### 2.1 Task CRUD
- `GET /`: List all tasks for an event with status, priority, and dependency arrays.
- `POST /`: Create a new task (`title`, `description`, `due_at`, `priority`, `function_id`).
- `GET /{task_id}`: Retrieve task details.
- `PATCH /{task_id}`: Update task properties or advance status (`todo`, `in_progress`, `blocked`, `done`, `cancelled`).
- `DELETE /{task_id}`: Remove task and cascading dependencies.

### 2.2 Dependency Modeling
- `POST /{task_id}/dependencies`: Add a prerequisite dependency (`depends_on_task_id`). Evaluates DAG cycle check via 3-color DFS and due-date chronological sequence.
- `DELETE /{task_id}/dependencies/{depends_on_task_id}`: Remove a prerequisite link.

### 2.3 Timeline Summaries
- `GET /summary`: Aggregates total, completed, in-progress, blocked, overdue, and upcoming tasks along with percentage completion.

### 2.4 AI Timeline Assistant
- `POST /ai/generate`: Prompts Gemini AI to generate an end-to-end planning schedule with milestones and dependency links.
- `POST /ai/proposals/{proposal_id}/accept`: Atomically creates selected tasks and dependency edges in PostgreSQL within a single transaction.

## 3. Frontend Architecture
The user interface is accessible at `/events/{eventId}/timeline`:
- **Metrics Bar:** 7-column KPI bar showing total tasks, completed percentage, in-progress, todo, blocked, overdue, and upcoming 7-day deadlines.
- **Kanban Board:** Multi-column drag-and-drop / selector board for managing workflow stages (`To Do`, `In Progress`, `Blocked`, `Done`).
- **Milestone Timeline:** Chronological step-by-step Gantt-style view sorted by `due_at` with dependency markers.
- **Dependency Dialog:** Interactive prerequisite manager preventing cycle creation.
- **AI Modal:** Interactive assistant for natural language schedule generation and selective task import.

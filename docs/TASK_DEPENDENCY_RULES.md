# TimelineAI Task Dependency & Scheduling Rules

## 1. Directed Acyclic Graph (DAG) Structure

Task management in UtsavAI models scheduling prerequisites as a Directed Acyclic Graph:
- A dependency $(A, B)$ represents: **Task $A$ depends on Task $B$** (meaning $B$ is a prerequisite that must be executed or completed before $A$).
- The database table `public.task_dependencies` records `(task_id, depends_on_task_id)`.
- Self-referential edges (`task_id = depends_on_task_id`) are forbidden by check constraint `task_dependencies_no_self_ref`.

## 2. Cycle Detection Engine (Three-Color DFS)

Circular dependencies ($A \to B \to C \to A$) cause scheduling deadlocks where no task can start.
Before inserting any dependency into `public.task_dependencies`, the backend executes cycle detection using a **3-color Depth First Search** algorithm:

1. **Graph Construction:** Directed edges are assembled from all existing dependencies of the event plus the proposed candidate edge.
2. **Color State Representation:**
   - `0 (WHITE)`: Node unvisited.
   - `1 (GRAY)`: Node currently being explored in the active recursion call stack.
   - `2 (BLACK)`: Node and all descendants completely visited.
3. **Cycle Encounter:** If a DFS traversal reaches a node colored `1 (GRAY)`, a directed back-edge exists, proving a cycle.
4. **Enforcement:** When a cycle is detected, the operation is immediately aborted, rolling back the transaction and raising a `409 ConflictError`:
   `"Circular task dependency detected. Adding this dependency would create a cycle."`

## 3. Chronological Due Date Invariants

In addition to topological acyclicity, temporal consistency is enforced:
- If Task $A$ depends on Task $B$, Task $B$'s scheduled `due_at` timestamp **must not be later than** Task $A$'s `due_at` timestamp:
  $$\text{prerequisite}.\text{due\_at} \le \text{dependent}.\text{due\_at}$$
- If a user attempts to make Task $A$ dependent on a prerequisite whose due date is after Task $A$'s due date, the backend raises a `400 ValidationError`:
  `"Prerequisite task due date cannot be later than dependent task due date."`

## 4. Status Progression & Cascading Semantics

Tasks progress through five distinct states:
1. `todo`: Initial pending state.
2. `in_progress`: Active execution by event organizers or vendors.
3. `blocked`: Blocked by external circumstances or unfulfilled prerequisites.
4. `done`: Completed successfully (sets `completed_at = now()`).
5. `cancelled`: Cancelled or deemed unnecessary.

### Dependency Status Checking
- A task with active prerequisite dependencies that remain in `todo`, `in_progress`, or `blocked` is considered waiting on prerequisites.
- Completing a prerequisite (`done`) unblocks downstream dependent tasks.

## 5. Event Mutation Cascade Trigger

Every modification to `public.tasks` or `public.task_dependencies` invokes `app.task_touch_event()`, triggering an update to the parent event's `revision` counter and `updated_at` timestamp. This invalidates stale cached proposals and ensures optimistic concurrency control across modules.

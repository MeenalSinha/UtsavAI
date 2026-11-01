"""Task and Timeline service with DAG cycle detection and scheduling intelligence."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.domain import MemberRole, Permission, TaskOrigin, TaskPriority, TaskStatus
from app.core.errors import ConflictError, ForbiddenError, InvalidRequestError, NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.audit import repository as audit
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.functions import repository as functions_repo
from app.modules.tasks import repository as repo
from app.modules.tasks.schemas import (
    TaskCreate,
    TaskDependencyOut,
    TaskOut,
    TaskUpdate,
    TimelineSummaryOut,
)


def _require_active_event(event: dict[str, Any]) -> None:
    if event["status"] == "archived":
        raise ForbiddenError("Archived events are read-only.")


def _has_cycle(adjacency: dict[uuid.UUID, list[uuid.UUID]], start_node: uuid.UUID) -> bool:
    """Check if graph containing start_node has a directed cycle using 3-color DFS."""
    visited: dict[uuid.UUID, int] = {}  # 0: unvisited, 1: visiting, 2: visited

    def dfs(node: uuid.UUID) -> bool:
        visited[node] = 1
        for neighbor in adjacency.get(node, []):
            state = visited.get(neighbor, 0)
            if state == 1:
                return True
            if state == 0 and dfs(neighbor):
                return True
        visited[node] = 2
        return False

    return dfs(start_node)


def list_tasks(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    status: str | None = None,
    priority: str | None = None,
    function_id: uuid.UUID | None = None,
    assigned_user_id: uuid.UUID | None = None,
    search: str | None = None,
) -> list[TaskOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.TASK_READ)

        task_rows = repo.list_tasks(conn, event_id, status, priority, function_id, assigned_user_id, search)
        dep_rows = repo.list_event_dependencies(conn, event_id)

        deps_by_task: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
        for d in dep_rows:
            deps_by_task[d["task_id"]].append(d["depends_on_task_id"])

        return [
            TaskOut(
                id=t["id"],
                event_id=t["event_id"],
                function_id=t["function_id"],
                title=t["title"],
                description=t["description"],
                due_at=t["due_at"],
                status=TaskStatus(t["status"]),
                priority=TaskPriority(t["priority"]),
                assigned_user_id=t["assigned_user_id"],
                origin=TaskOrigin(t["origin"]),
                sort_order=t["sort_order"],
                created_at=t["created_at"],
                updated_at=t["updated_at"],
                completed_at=t["completed_at"],
                depends_on_task_ids=deps_by_task.get(t["id"], []),
            )
            for t in task_rows
        ]


def get_task(db: Database, principal: Principal, event_id: uuid.UUID, task_id: uuid.UUID) -> TaskOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.TASK_READ)

        task = repo.get_task(conn, event_id, task_id)
        if task is None:
            raise NotFoundError("Task not found.")

        deps = repo.get_task_dependencies(conn, task_id)
        return TaskOut(
            id=task["id"],
            event_id=task["event_id"],
            function_id=task["function_id"],
            title=task["title"],
            description=task["description"],
            due_at=task["due_at"],
            status=TaskStatus(task["status"]),
            priority=TaskPriority(task["priority"]),
            assigned_user_id=task["assigned_user_id"],
            origin=TaskOrigin(task["origin"]),
            sort_order=task["sort_order"],
            created_at=task["created_at"],
            updated_at=task["updated_at"],
            completed_at=task["completed_at"],
            depends_on_task_ids=list(deps),
        )


def create_task(db: Database, principal: Principal, event_id: uuid.UUID, req: TaskCreate) -> TaskOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.TASK_MANAGE)

        if req.function_id is not None:
            fn = functions_repo.get_function(conn, event_id, req.function_id)
            if fn is None:
                raise InvalidRequestError("Referenced function does not belong to this event.")

        task_row = repo.create_task(
            conn,
            event_id=event_id,
            title=req.title,
            description=req.description,
            due_at=req.due_at,
            priority=req.priority.value,
            function_id=req.function_id,
            assigned_user_id=req.assigned_user_id,
            origin=TaskOrigin.MANUAL.value,
            sort_order=req.sort_order,
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="task.created",
            entity_type="tasks",
            entity_id=task_row["id"],
            request_id=request_id,
            metadata={"title": req.title, "priority": req.priority.value},
        )

        return TaskOut(
            id=task_row["id"],
            event_id=task_row["event_id"],
            function_id=task_row["function_id"],
            title=task_row["title"],
            description=task_row["description"],
            due_at=task_row["due_at"],
            status=TaskStatus(task_row["status"]),
            priority=TaskPriority(task_row["priority"]),
            assigned_user_id=task_row["assigned_user_id"],
            origin=TaskOrigin(task_row["origin"]),
            sort_order=task_row["sort_order"],
            created_at=task_row["created_at"],
            updated_at=task_row["updated_at"],
            completed_at=task_row["completed_at"],
            depends_on_task_ids=[],
        )


def update_task(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    req: TaskUpdate,
) -> TaskOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.TASK_MANAGE)

        current = repo.get_task(conn, event_id, task_id)
        if current is None:
            raise NotFoundError("Task not found.")

        if req.function_id is not None:
            fn = functions_repo.get_function(conn, event_id, req.function_id)
            if fn is None:
                raise InvalidRequestError("Referenced function does not belong to this event.")

        # Handle completed_at timestamp
        completed_at = current["completed_at"]
        if req.status is not None:
            if req.status == TaskStatus.DONE and current["status"] != TaskStatus.DONE.value:
                completed_at = datetime.now(UTC)
            elif req.status != TaskStatus.DONE and current["status"] == TaskStatus.DONE.value:
                completed_at = None

        status_val = req.status.value if req.status is not None else None
        priority_val = req.priority.value if req.priority is not None else None

        updated = repo.update_task(
            conn,
            event_id=event_id,
            task_id=task_id,
            title=req.title,
            description=req.description,
            due_at=req.due_at,
            status=status_val,
            priority=priority_val,
            function_id=req.function_id,
            assigned_user_id=req.assigned_user_id,
            sort_order=req.sort_order,
            completed_at=completed_at,
        )
        assert updated is not None

        deps = repo.get_task_dependencies(conn, task_id)
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="task.updated",
            entity_type="tasks",
            entity_id=task_id,
            request_id=request_id,
            metadata={"status": status_val, "priority": priority_val},
        )

        return TaskOut(
            id=updated["id"],
            event_id=updated["event_id"],
            function_id=updated["function_id"],
            title=updated["title"],
            description=updated["description"],
            due_at=updated["due_at"],
            status=TaskStatus(updated["status"]),
            priority=TaskPriority(updated["priority"]),
            assigned_user_id=updated["assigned_user_id"],
            origin=TaskOrigin(updated["origin"]),
            sort_order=updated["sort_order"],
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
            completed_at=updated["completed_at"],
            depends_on_task_ids=list(deps),
        )


def delete_task(db: Database, principal: Principal, event_id: uuid.UUID, task_id: uuid.UUID) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.TASK_MANAGE)

        current = repo.get_task(conn, event_id, task_id)
        if current is None:
            raise NotFoundError("Task not found.")

        repo.cancel_task(conn, event_id, task_id)
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="task.cancelled",
            entity_type="tasks",
            entity_id=task_id,
            request_id=request_id,
            metadata={},
        )


def add_dependency(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    depends_on_task_id: uuid.UUID,
) -> TaskDependencyOut:
    if task_id == depends_on_task_id:
        raise InvalidRequestError("A task cannot depend on itself.")

    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.TASK_MANAGE)

        t1 = repo.get_task(conn, event_id, task_id)
        if t1 is None:
            raise NotFoundError("Task not found.")

        t2 = repo.get_task(conn, event_id, depends_on_task_id)
        if t2 is None:
            raise NotFoundError("Prerequisite task not found in this event.")

        # Due date sequence validation: prerequisite t2 must not be scheduled after dependent t1
        if t1["due_at"] is not None and t2["due_at"] is not None and t2["due_at"] > t1["due_at"]:
            raise ConflictError(
                f"Prerequisite task '{t2['title']}' is scheduled after dependent task '{t1['title']}'."
            )

        # Graph-based cycle detection
        existing_deps = repo.list_event_dependencies(conn, event_id)
        adjacency: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)
        for d in existing_deps:
            adjacency[d["task_id"]].append(d["depends_on_task_id"])

        # Add the proposed edge
        adjacency[task_id].append(depends_on_task_id)

        if _has_cycle(adjacency, task_id):
            raise ConflictError(
                f"Adding dependency from '{t1['title']}' to '{t2['title']}' creates a circular dependency."
            )

        repo.add_dependency(conn, task_id, depends_on_task_id)
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="task.dependency_added",
            entity_type="task_dependencies",
            entity_id=task_id,
            request_id=request_id,
            metadata={"task_id": str(task_id), "depends_on_task_id": str(depends_on_task_id)},
        )
        return TaskDependencyOut(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id,
            created_at=datetime.now(UTC),
        )


def remove_dependency(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    depends_on_task_id: uuid.UUID,
) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.TASK_MANAGE)

        t1 = repo.get_task(conn, event_id, task_id)
        if t1 is None:
            raise NotFoundError("Task not found.")

        removed = repo.remove_dependency(conn, task_id, depends_on_task_id)
        if not removed:
            raise NotFoundError("Dependency does not exist.")

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="task.dependency_removed",
            entity_type="task_dependencies",
            entity_id=task_id,
            request_id=request_id,
            metadata={"task_id": str(task_id), "depends_on_task_id": str(depends_on_task_id)},
        )


def calculate_timeline_summary(db: Database, principal: Principal, event_id: uuid.UUID) -> TimelineSummaryOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.TASK_READ)

        tasks = repo.list_tasks(conn, event_id)
        now = datetime.now(UTC)
        upcoming_window = now + timedelta(days=14)

        total = len(tasks)
        completed = 0
        pending = 0
        in_progress = 0
        blocked = 0
        cancelled = 0
        overdue = 0
        upcoming = 0
        unscheduled = 0
        high_priority = 0

        for t in tasks:
            st = t["status"]
            pr = t["priority"]
            due = t["due_at"]

            if st == TaskStatus.DONE.value:
                completed += 1
            elif st == TaskStatus.TODO.value:
                pending += 1
            elif st == TaskStatus.IN_PROGRESS.value:
                in_progress += 1
            elif st == TaskStatus.BLOCKED.value:
                blocked += 1
            elif st == TaskStatus.CANCELLED.value:
                cancelled += 1

            if st not in (TaskStatus.DONE.value, TaskStatus.CANCELLED.value):
                if pr in (TaskPriority.HIGH.value, TaskPriority.URGENT.value):
                    high_priority += 1

                if due is None:
                    unscheduled += 1
                else:
                    if due < now:
                        overdue += 1
                    elif now <= due <= upcoming_window:
                        upcoming += 1

        active = total - cancelled
        completion_pct = round((completed / active) * 100, 1) if active > 0 else 0.0

        return TimelineSummaryOut(
            total_tasks=total,
            completed_tasks=completed,
            pending_tasks=pending,
            in_progress_tasks=in_progress,
            blocked_tasks=blocked,
            cancelled_tasks=cancelled,
            overdue_tasks=overdue,
            upcoming_tasks=upcoming,
            unscheduled_tasks=unscheduled,
            high_priority_tasks=high_priority,
            completion_percentage=completion_pct,
        )

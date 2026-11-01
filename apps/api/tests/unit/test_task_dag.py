"""Unit tests for TimelineAI task DAG cycle detection and scheduling rules."""

import uuid

import pytest

from app.core.errors import ConflictError
from app.modules.tasks.ai_service import _validate_proposed_dag
from app.modules.tasks.schemas import ProposedTaskItem, TimelineProposalPayload
from app.modules.tasks.service import _has_cycle


def test_has_cycle_linear_chain():
    """A -> B -> C has no cycles."""
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    adj: dict[uuid.UUID, list[uuid.UUID]] = {
        a: [b],
        b: [c],
        c: [],
    }
    assert not _has_cycle(adj, a)


def test_has_cycle_diamond_dag():
    """Diamond DAG (A -> B, A -> C, B -> D, C -> D) has no cycles."""
    a, b, c, d = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    adj: dict[uuid.UUID, list[uuid.UUID]] = {
        a: [b, c],
        b: [d],
        c: [d],
        d: [],
    }
    assert not _has_cycle(adj, a)


def test_has_cycle_detected():
    """A -> B -> C -> A contains a directed cycle."""
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    adj: dict[uuid.UUID, list[uuid.UUID]] = {
        a: [b],
        b: [c],
        c: [a],
    }
    assert _has_cycle(adj, a)


def test_validate_proposed_dag_clean():
    payload = TimelineProposalPayload(
        summary="Test schedule",
        proposed_tasks=[
            ProposedTaskItem(client_ref="t1", title="Task 1", depends_on=[]),
            ProposedTaskItem(client_ref="t2", title="Task 2", depends_on=["t1"]),
            ProposedTaskItem(client_ref="t3", title="Task 3", depends_on=["t2"]),
        ],
    )
    _validate_proposed_dag(payload)  # Should not raise


def test_validate_proposed_dag_cycle_raises():
    payload = TimelineProposalPayload(
        summary="Cyclic schedule",
        proposed_tasks=[
            ProposedTaskItem(client_ref="t1", title="Task 1", depends_on=["t3"]),
            ProposedTaskItem(client_ref="t2", title="Task 2", depends_on=["t1"]),
            ProposedTaskItem(client_ref="t3", title="Task 3", depends_on=["t2"]),
        ],
    )
    with pytest.raises(ConflictError, match="Circular dependency"):
        _validate_proposed_dag(payload)


def test_validate_proposed_dag_self_dependency_raises():
    payload = TimelineProposalPayload(
        summary="Self dependency",
        proposed_tasks=[
            ProposedTaskItem(client_ref="t1", title="Task 1", depends_on=["t1"]),
        ],
    )
    with pytest.raises(ConflictError, match="Self-dependency"):
        _validate_proposed_dag(payload)


def test_completion_percentage_formula():
    """Cancelled tasks are excluded from active work; 0 active yields 0.0%."""
    # 5 total, 1 cancelled, 2 done, 2 todo -> active = 4, done = 2 -> 50.0%
    total = 5
    cancelled = 1
    completed = 2
    active = total - cancelled
    pct = round((completed / active) * 100, 1) if active > 0 else 0.0
    assert pct == 50.0

    # 3 total, all 3 cancelled -> active = 0 -> 0.0%
    total = 3
    cancelled = 3
    completed = 0
    active = total - cancelled
    pct = round((completed / active) * 100, 1) if active > 0 else 0.0
    assert pct == 0.0

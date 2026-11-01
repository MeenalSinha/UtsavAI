"""Locust load test suite for UtsavAI.

Simulates three core user archetypes:
1. HostUser: Authenticated host browsing event functions, budget, timeline, and proposals.
2. GuestUser: Anonymous public guest accessing GiftCircle registries and viewing gift items.
3. HealthMonitor: Infrastructure agent probing liveness and readiness endpoints.

Run:
    locust -f tests/load/locustfile.py --headless -u 50 -r 5 --run-time 1m --host http://localhost:8000
"""

from __future__ import annotations

import uuid

from locust import HttpUser, between, task


class HealthMonitor(HttpUser):
    wait_time = between(2, 5)
    weight = 1

    @task(3)
    def check_liveness(self) -> None:
        self.client.get("/api/v1/health")

    @task(1)
    def check_readiness(self) -> None:
        self.client.get("/api/v1/health/ready")


class GuestUser(HttpUser):
    wait_time = between(1, 3)
    weight = 3

    def on_start(self) -> None:
        self.token = "demo-jaipur-aarav-meera"  # noqa: S105

    @task(3)
    def view_public_registry(self) -> None:
        self.client.get(f"/api/v1/public/registries/{self.token}")

    @task(1)
    def view_registry_summary(self) -> None:
        self.client.get(f"/api/v1/public/registries/{self.token}/summary")


class HostUser(HttpUser):
    wait_time = between(1, 4)
    weight = 6

    def on_start(self) -> None:
        # Mock auth header for local load testing
        self.event_id = uuid.UUID("e0000000-0000-0000-0000-000000000001")
        self.headers = {"Authorization": "Bearer mock-load-test-token"}

    @task(4)
    def get_event_details(self) -> None:
        self.client.get(f"/api/v1/events/{self.event_id}", headers=self.headers)

    @task(3)
    def get_budget_summary(self) -> None:
        self.client.get(f"/api/v1/events/{self.event_id}/budget/summary", headers=self.headers)

    @task(2)
    def get_timeline_tasks(self) -> None:
        self.client.get(f"/api/v1/events/{self.event_id}/tasks", headers=self.headers)

    @task(2)
    def get_vendors(self) -> None:
        self.client.get(f"/api/v1/events/{self.event_id}/vendors", headers=self.headers)

    @task(1)
    def get_change_proposals(self) -> None:
        self.client.get(f"/api/v1/events/{self.event_id}/change-proposals", headers=self.headers)

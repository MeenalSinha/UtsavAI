# UtsavAI Observability & Reliability Guide

## 1. Structured Logging
In production (`APP_ENV=production`), logs are emitted in JSON format to stdout:
```json
{
  "timestamp": "2026-11-01T21:00:00.123Z",
  "level": "INFO",
  "logger": "app.modules.adaptive.service",
  "message": "change_proposal_created",
  "request_id": "req_01hxyz...",
  "event_id": "e0000000-0000-0000-0000-000000000001",
  "actor_user_id": "d0000000-0000-0000-0000-000000000001"
}
```

## 2. Health & Readiness Monitoring
- **Liveness Probe:** `GET /api/v1/health`
  - Returns service status, version (`v1.0.0-rc1`), and environment.
  - Does not execute SQL.
- **Readiness Probe:** `GET /api/v1/health/ready`
  - Executes a live database check (`db.verify_runtime_role()`).
  - Returns `200 OK` when healthy, or `503 Service Unavailable` if database is disconnected.

## 3. Distributed Tracing & Request IDs
Every request is stamped with an `X-Request-ID` header. If provided by client (e.g. BFF or reverse proxy), it is propagated; otherwise a secure unique prefix `req_<uuid>` is generated and bound to Python `contextvars`.

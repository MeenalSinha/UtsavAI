# Changelog

All notable changes to UtsavAI are documented here.

## [v1.0.0-rc1] - 2026-11-01 (Phase 7 Release Candidate)
### Added
- Comprehensive Phase 7 production finalization, quality assurance, and security hardening.
- Strict Adaptive Planning dispatcher preventing unknown operations or cross-tenant option execution.
- Dedicated database readiness check (`GET /api/v1/health/ready`).
- Public disclosure pages: Privacy Policy (`/privacy`), Terms of Service (`/terms`), and AI Usage Disclosure (`/ai-disclosure`).
- Synthetic 3-day Jaipur Royal Wedding seeding and cleanup script (`scripts/seed_demo_data.py`).
- Locust load-testing performance profile (`tests/load/locustfile.py`).
- Production Dockerfiles with non-root security boundaries and healthchecks.
- Complete operational runbooks (Backup/Recovery, Incident Response, Smoke Tests).

## [v0.6.0] - 2026-11-01 (Phase 6)
### Added
- Adaptive Planning Engine with cross-module replanning, versioned concurrency, and atomic execution.

## [v0.5.0] - 2026-11-01 (Phase 5)
### Added
- GiftCircle wedding gift registry, individual reservations, and atomic group gifting pledges.

## [v0.4.0] - 2026-11-01 (Phase 4)
### Added
- VendorConnect vendor profiles, quotations, and itemized comparison engine.

## [v0.3.0] - 2026-11-01 (Phase 3)
### Added
- BudgetAI financial modeling and TimelineAI DAG scheduling.

## [v0.2.0] - 2026-11-01 (Phase 2)
### Added
- Core Event Planning and PlanAI cultural itinerary generation.

## [v0.1.0] - 2026-11-01 (Phase 1)
### Added
- Foundation architecture, Supabase Auth, PostgreSQL RLS, Next.js App Router, FastAPI backend.

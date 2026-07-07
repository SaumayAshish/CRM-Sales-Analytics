# ADR-001: Monolithic Backend vs. Microservices

**Status:** Accepted
**Date:** 2026-07-05
**Deciders:** Saumay Ashish (BA), Senior Full-Stack Engineer

## Context
The platform needs to serve 7 modules (Lead Management, Opportunity Pipeline, Account & Contact 360, Activity Tracking, Analytics Dashboards, Workflow Automation, RBAC/Audit) to a single mid-market sales organization (single-tenant, see ADR-004). The team is one developer-equivalent (this engagement). We need a backend architecture that supports 40+ REST endpoints, 15+ tables, and 70%+ test coverage within the delivery timeline, while remaining credible to reviewers evaluating architectural judgment, not just buzzword usage.

## Options Considered
1. **Monolithic FastAPI service** — one deployable backend, modular internally by domain (routers per module: `leads`, `opportunities`, `accounts`, `activities`, `workflow`, `auth`), single Postgres database.
   - Pros: Simple deployment (one container), no network overhead between modules, transactions across entities (e.g., lead conversion touching Lead + Account + Opportunity) are trivial, matches team size of one engineer, faster to reach 40+ endpoints without integration overhead.
   - Cons: Less "resume-buzzword" appeal than microservices; scaling is vertical, not per-module.
2. **Microservices (e.g., separate Lead service, Opportunity service, Analytics service)** — each module as an independently deployable service with its own datastore or schema, communicating via REST/events.
   - Pros: Independent scaling and deployment per module; industry-standard for large SaaS at scale.
   - Cons: Massive overhead for a single-tenant, single-team project — service discovery, inter-service auth, distributed transactions for lead-to-opportunity conversion, and eventual consistency issues where the business actually needs strong consistency (audit log correctness). Would consume delivery time that should go toward feature depth and test coverage. Directly contradicts the project's explicit exclusion of microservices.
3. **Modular monolith with future extraction path** — same as Option 1, but with strict internal module boundaries (no cross-module direct DB access, only through service-layer functions) so it *could* be split later.
   - Pros: All benefits of Option 1, plus a documented seam if the project ever needed to scale out.
   - Cons: Slightly more upfront discipline in structuring internal service boundaries.

## Decision
**Option 3 — Modular monolith with clean internal boundaries.** A single FastAPI application, organized by domain module (routers, services, schemas per module), backed by one PostgreSQL database. Cross-module operations (e.g., converting a Lead into an Account + Contact + Opportunity) go through explicit service-layer functions rather than ad-hoc cross-table writes, so module boundaries stay legible even though they run in one process.

## Consequences
- Single Docker image + one docker-compose service for the backend, satisfying the "docker-compose up works in one command" Definition of Done item.
- Transactions spanning multiple entities (lead conversion, opportunity stage change with audit write) are simple ACID transactions, not distributed sagas.
- Test coverage is easier to reach because there's one test suite, one CI job, not N services each needing their own pipeline.
- Trade-off accepted: this will not demonstrate microservice orchestration skills — that is an explicit non-goal for this project, and this ADR documents why, so it reads as a deliberate engineering decision rather than a gap.
- If a future phase required independent scaling of, say, the analytics workload, the modular boundaries in this ADR are the seam where that split would happen — captured here so the decision isn't re-litigated without cause.

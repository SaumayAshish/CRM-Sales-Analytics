# Phase 2 Completion Report — Backend Core

**Date completed:** 2026-07-05
**Phase owner:** Saumay Ashish (Business Analyst) / Senior Full-Stack Engineer (delivery)

---

## 1. Deliverables Checklist

- [x] FastAPI app running on `localhost:8000` (verified via live `uvicorn` run against seeded data)
- [x] `/docs` shows all endpoints organized by module (49 routes total: 44 business endpoints + health + docs/openapi)
- [x] PostgreSQL running via docker-compose (`db` service, host port 5433 to avoid a conflicting local Postgres install)
- [x] Alembic migration creates the full 17-table schema (matches `docs/ERD.md` / `docs/Data_Dictionary.md` exactly)
- [x] Seed script populates 10,120 records (20 users, 100 accounts, 500 contacts, 3,000 leads, 1,500 opportunities, 5,000 activities)
- [x] JWT auth works for all 4 roles (verified end-to-end: login, protected-route access, RBAC denial)
- [x] RBAC enforced on every mutating endpoint (`require_role` dependency; 403 verified in tests and manually)
- [x] pytest coverage: **80%** (target 70%+, NFR-07) — 32/32 tests passing
- [x] Coverage report committed (`backend/COVERAGE.md`; HTML/XML gitignored as regenerable build output, uploaded as a CI artifact instead)
- [x] GitHub Actions CI (`.github/workflows/backend-ci.yml`): lint (ruff) + migration + pytest with coverage gate, `--cov-fail-under=70`
- [x] This completion report

---

## 2. What Was Built

| Area | Summary |
|---|---|
| Scaffold | `app/core` (config, security, logging, limiter), `app/api/v1/routers` (one file per module), `app/models`, `app/schemas`, `app/services`, `app/db`, `app/scripts`. `requirements.txt` + `requirements-dev.txt`. Docker Compose (`db` + `backend`). |
| Database | Sync SQLAlchemy 2.0 + psycopg2, Alembic (hand-written initial migration — Docker Desktop's daemon wasn't running when scaffolding began, so autogenerate wasn't available at that moment; the migration was still verified by actually running it against a live Postgres 16 container once Docker started, not merely inspected). 17 tables, UUID PKs, `created_at`/`updated_at` everywhere, `deleted_at` soft-delete on the 6 core entities per the Data_Dictionary addendum, FK/CHECK/partial-unique constraints matching `docs/ERD.md` exactly. |
| Auth | bcrypt hashing, JWT access (15 min) + refresh (7 day) per ADR-003, `revoked_tokens` table checked at refresh, `require_role([...])` dependency enforced server-side, slowapi in-memory rate limiting on `/auth/login` (10/minute). |
| CRUD | 6 modules (Users, Accounts, Contacts, Leads, Opportunities, Activities) + read-only lookups + a cross-cutting audit-write hook satisfying BR-14 from day one. 44 business endpoints total (exceeds the 40+ target). |
| Seed data | Deterministic (seed=42), lead-heavy funnel: Cold 1805 / Warm 1111 / Hot 84 leads, realistic pipeline-stage distribution (heavier in early stages, taper toward Closed), zero accounts with more than one primary contact (partial unique index verified). |
| Tests | 32 tests: auth unit tests (login/refresh/logout/revocation), per-module CRUD integration tests, RBAC boundary tests (403 cases) across Leads, Accounts, Opportunities, Activities, Users. Isolated per-test via a SAVEPOINT-based transaction rollback fixture (`join_transaction_mode="create_savepoint"`), so endpoint code's own `db.commit()` calls don't leak state between tests. |
| CI | GitHub Actions: Postgres 16 service container, ruff lint, Alembic migration, pytest with an enforced 70% coverage gate, coverage report uploaded as a workflow artifact. |

---

## 3. Verification Performed (Not Just "Should Work")

This phase was verified against a **real** PostgreSQL 16 instance, not just import-checked:
1. Docker Desktop's daemon was down when scaffolding began; discovered a native Windows Postgres service already bound to port 5432, which silently produced authentication failures against the container. Diagnosed via `netstat`/`tasklist`, then remapped the container's host port to 5433 (`docker-compose.yml`) — the internal `backend`↔`db` service link is unaffected since it uses the Docker network's internal port 5432.
2. Ran the hand-written Alembic migration against the live container — confirmed all 17 tables via `\dt`.
3. Ran the seed script — confirmed record counts and, importantly, caught and fixed a real bug: the initial lead-scoring formula's maximum possible score (75) barely reached the Hot threshold (70), producing **zero** Hot-band leads. Fixed the score distribution and re-seeded; verified a realistic Cold/Warm/Hot split afterward.
4. Booted the API with `uvicorn`, logged in as the seeded Admin, listed real leads, and confirmed a Viewer role gets a 403 attempting to create a lead — exercising the full auth → RBAC → DB round trip.
5. Ran the full pytest suite against a dedicated `crm_sales_analytics_test` database — 32/32 passing, 80% coverage.

---

## 4. Deviations From the Original Plan (and Why)

| Deviation | Reason |
|---|---|
| Alembic migration hand-written, not autogenerated | Docker Desktop's daemon wasn't running yet when the migration needed to be authored. Rather than block, wrote it by hand against the models, then verified it end-to-end once Docker came up — a stronger check than autogenerate-and-trust, since it confirms the migration actually executes and matches the models (verified via `Base.metadata.tables.keys()` diff). |
| Docker host port 5433, not 5432 | A native Windows Postgres service already owned port 5432 on this machine. Purely a local-environment accommodation; the `docker-compose.yml` internal service-to-service link (`backend` → `db:5432`) is unaffected. |
| Coverage HTML/XML gitignored, `COVERAGE.md` committed instead | Generated HTML coverage reports are large, regenerate on every run, and don't diff meaningfully in git. `COVERAGE.md` gives a durable, readable snapshot; CI uploads the machine-readable `coverage.xml` as a build artifact instead of a committed file. |
| Lead scoring formula tuned mid-phase | Caught via actual data inspection (not assumption) that the original formula couldn't produce Hot leads. Documented as a concrete example of "verify, don't assume" in the working process. |

---

## 5. Open Items Carried Into Phase 3

1. **Lead scoring/auto-assignment is not yet a rule *engine*** — Phase 2 persists `score`/`score_band`/`assigned_to` as plain columns (set only by the seed script), matching FR-01–FR-27 (plain CRUD). The actual rule-evaluation engine (FR-33–FR-37) reading `scoring_rules`/`scoring_criteria`/`assignment_rules` at request time is Phase 3 scope per `CLAUDE.md`.
2. **Audit log query/filter endpoints (FR-44)** deferred to Phase 3, though the audit *write* path is live now (see Phase 2 plan's reconciliation).
3. **Router test coverage is uneven** — RBAC-critical and validation-critical paths are tested; some list/filter/404 branches on Accounts/Contacts/Activities/Opportunities aren't yet. Noted in `COVERAGE.md` as a natural Phase 3 backfill point rather than testing twice.
4. **`app/schemas/common.py` (`Page`, `ErrorResponse`) is currently unused** — scaffolded for future pagination/error-envelope standardization but not yet wired into responses; flagging so it isn't mistaken for dead code review noise later.

---

## 6. Recommendation to Proceed

Phase 2 deliverables are complete, verified against a live database (not just imported), and traceable to their FR/BR origins. Recommend proceeding to Phase 3 (Backend Advanced: pipeline engine, scoring, workflow, audit) planning.

---

## 7. Approval & Sign-off

| Name | Role | Decision | Date |
|---|---|---|---|
| Saumay Ashish | Business Analyst / Product Owner | ☑ Approved | 2026-07-05 |
| (Engineering) | Senior Full-Stack Engineer | ☑ Acknowledged deliverables verified against a live database | 2026-07-05 |

# Backend Test Coverage Report

**Generated:** 2026-07-05 (Phase 3) · **Result:** 50 passed, 0 failed · **Total coverage: 78%** (target: 70%+, NFR-07)

Generated HTML/XML coverage artifacts (`htmlcov/`, `coverage.xml`) are gitignored as build output, regenerated on
every CI run (`.github/workflows/backend-ci.yml`) and uploaded there as a workflow artifact. This file is the
durable, human-readable snapshot committed to the repo.

`app/scripts/seed.py` is excluded from the coverage measurement (`.coveragerc`) as a one-off data-generation tool,
not CRUD/business-logic — verified manually against a live database instead (see `docs/PHASE_REPORTS/`).

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| app/api/deps.py | 36 | 4 | 89% |
| app/api/v1/routers/accounts.py | 93 | 45 | 52% |
| app/api/v1/routers/activities.py | 85 | 39 | 54% |
| app/api/v1/routers/analytics.py | 32 | 12 | 62% |
| app/api/v1/routers/audit_log.py | 32 | 18 | 44% |
| app/api/v1/routers/auth.py | 46 | 6 | 87% |
| app/api/v1/routers/contacts.py | 57 | 28 | 51% |
| app/api/v1/routers/lead_scoring.py | 43 | 24 | 44% |
| app/api/v1/routers/leads.py | 120 | 38 | 68% |
| app/api/v1/routers/lookups.py | 25 | 6 | 76% |
| app/api/v1/routers/notifications.py | 25 | 11 | 56% |
| app/api/v1/routers/opportunities.py | 124 | 51 | 59% |
| app/api/v1/routers/pipeline.py | 35 | 20 | 43% |
| app/api/v1/routers/users.py | 56 | 17 | 70% |
| app/api/v1/routers/workflows.py | 34 | 3 | 91% |
| app/core/* | 65 | 0 | 100% |
| app/db/* | 25 | 4 | 84% |
| app/main.py | 33 | 2 | 94% |
| app/models/* | 231 | 0 | 100% |
| app/schemas/* | 304 | 11 | 96% |
| app/services/activity_log.py | 18 | 0 | 100% |
| app/services/assignment_engine.py | 36 | 14 | 61% |
| app/services/audit.py | 8 | 0 | 100% |
| app/services/lead_workflow.py | 19 | 0 | 100% |
| app/services/notification_service.py | 8 | 0 | 100% |
| app/services/scoring_engine.py | 64 | 8 | 88% |
| app/services/stage_engine.py | 14 | 1 | 93% |
| app/services/workflow_engine.py | 81 | 37 | 54% |
| **TOTAL** | **1776** | **399** | **78%** |

## Notes for Phase 4

- Lower-coverage routers (list/get/patch/delete branches on Accounts/Contacts/Activities/Opportunities not exercised
  by every filter/404 path) — unchanged assessment from Phase 2; still a reasonable backfill point when those
  routers are touched again for the frontend's API needs.
- `workflow_engine.py`'s `_execute_action` branches for `update_field` and `create_task` are exercised indirectly by
  seed data but not by dedicated unit tests; the `send_notification` and non-matching paths are (test_workflows.py).
- `assignment_engine.py`'s `round_robin` strategy path is implemented but not unit-tested, since `least_loaded` is
  the shipped default (Phase 3 kickoff decision) — worth a test if `round_robin` is ever made configurable in the UI.

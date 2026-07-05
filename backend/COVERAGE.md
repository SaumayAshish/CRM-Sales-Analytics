# Backend Test Coverage Report

**Generated:** 2026-07-05 · **Result:** 32 passed, 0 failed · **Total coverage: 80%** (target: 70%+, NFR-07)

Generated HTML/XML coverage artifacts (`htmlcov/`, `coverage.xml`) are gitignored as build output, regenerated on
every CI run (`.github/workflows/backend-ci.yml`) and uploaded there as a workflow artifact. This file is the
durable, human-readable snapshot committed to the repo.

`app/scripts/seed.py` is excluded from the coverage measurement (`.coveragerc`) as a one-off data-generation tool,
not CRUD business logic — it was verified manually against a live database instead (see `docs/PHASE_REPORTS/phase_2.md`).

| Module | Stmts | Miss | Cover |
|---|---|---|---|
| app/api/deps.py | 37 | 4 | 89% |
| app/api/v1/routers/accounts.py | 74 | 31 | 58% |
| app/api/v1/routers/activities.py | 78 | 39 | 50% |
| app/api/v1/routers/auth.py | 46 | 6 | 87% |
| app/api/v1/routers/contacts.py | 57 | 28 | 51% |
| app/api/v1/routers/leads.py | 103 | 31 | 70% |
| app/api/v1/routers/lookups.py | 25 | 6 | 76% |
| app/api/v1/routers/opportunities.py | 102 | 43 | 58% |
| app/api/v1/routers/users.py | 56 | 17 | 70% |
| app/core/* | 47 | 0 | 100% |
| app/db/* | 25 | 4 | 84% |
| app/main.py | 25 | 2 | 92% |
| app/models/* | 187 | 0 | 100% |
| app/schemas/* | 268 | 11 | 96% |
| app/services/audit.py | 7 | 0 | 100% |
| **TOTAL** | **1094** | **222** | **80%** |

## Notes for Phase 3

Lower-coverage routers (Accounts/Contacts/Activities/Opportunities list/get/patch/delete branches) are exercised
for their RBAC-critical and validation-critical paths, but not every filter combination or 404 branch has a
dedicated test. This is a reasonable Phase 2 baseline; Phase 3's workflow-engine work will likely touch these
routers again (e.g., wiring real lead scoring into `POST /leads`), which is a natural point to backfill the
remaining branches rather than testing them twice.

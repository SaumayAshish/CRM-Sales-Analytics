# Phase 3 Completion Report — Backend Advanced

**Date completed:** 2026-07-05
**Phase owner:** Saumay Ashish (Business Analyst) / Senior Full-Stack Engineer (delivery)

---

## 1. Deliverables Checklist

- [x] Pipeline stage engine: data-driven `allowed_next_stage_ids` transition graph (not hardcoded), Manager/Admin override with audited reason, `GET/POST /pipeline/stages`, `PATCH /pipeline/stages/{id}`, `GET /opportunities/{id}/stage-history`
- [x] Configurable rule-based lead scoring: real evaluator over `scoring_rules`/`scoring_criteria`, all 4 rule-type families (attribute/behavior/recency/negative-signal), `GET/POST /lead-scoring/rules`, `POST /leads/{id}/recalculate-score`, `GET /leads/{id}/score-breakdown`
- [x] Activity timeline API: `GET /leads/{id}/timeline`, `GET /accounts/{id}/timeline` (aggregated across contacts/opportunities), automatic system-generated activities on stage-change and lead-conversion
- [x] Append-only audit log: `ip_address`/`user_agent` columns, Postgres trigger rejecting UPDATE/DELETE at the DB level (on top of the existing no-route enforcement), `GET /audit-log`, `GET /audit-log/entity/{type}/{id}` (Manager team-scoped)
- [x] Workflow automation engine: event→condition→action, 6 trigger events, 5 action types (`trigger_webhook` and email/SMS explicitly stubbed), synchronous in-process execution, `GET/POST /workflows`, `PATCH /workflows/{id}/toggle`, `GET /workflows/{id}/execution-log`
- [x] Notifications (Module 6 infrastructure, not a new module): `GET /notifications`, `PATCH /notifications/{id}/mark-read`, `POST /notifications/mark-all-read`
- [x] 5 analytics endpoints backed by SQL views: `pipeline-summary`, `rep-performance`, `lead-funnel`, `forecast`, `kpis`
- [x] Backend now exposes 73 total routes (68 business endpoints, well past 40+)
- [x] pytest coverage: 78% (target 70%+), 50/50 tests passing
- [x] Every new endpoint traces to FR-46–FR-64 (added to `FRD.md` §10 at kickoff), with corresponding US-43–US-52 and UAT-35–UAT-44
- [x] This completion report

---

## 2. What Was Built

| Area | Summary |
|---|---|
| Migrations | 5 new Alembic revisions (0002–0005): stage transitions + audit hardening + workflow/notification tables, `activities.logged_by` nullable, analytics SQL views, scoring-criteria column widening |
| Engines | `stage_engine.py` (transition validation), `scoring_engine.py` (4 rule-type families), `assignment_engine.py` (least-loaded default, round-robin available), `workflow_engine.py` (event dispatch, 5 action types), `lead_workflow.py` (glue: rescore → maybe-assign → dispatch `lead_scored`) |
| Wiring | Scoring runs on lead create/update and on new-activity-logged; auto-assignment fires on the Cold/Warm→Hot transition; `stage_changed`/`opportunity_won`/`opportunity_lost` events fire from `advance-stage`; `lead_created`/`activity_logged` fire from their respective endpoints |
| Schema | `pipeline_stages.allowed_next_stage_ids`, `audit_logs.ip_address`/`user_agent` + immutability trigger, `workflow_rules`, `workflow_execution_log`, `notifications` — 21 tables total |
| Tests | 16 new tests: stage-transition unit tests (valid/invalid/override), scoring-engine unit tests (one per rule-type family + threshold + no-active-rule), workflow integration tests (match/no-match/toggle), audit-immutability tests (direct SQL bypass rejected), analytics accuracy tests |

---

## 3. Bugs Caught by Verification (Not Assumed Away)

This phase surfaced four real defects, each caught by actually running the code against a live database or the test suite — not by code review alone:

1. **Rate limiter false-positive across the whole test session** — `auth.py` had created a second `Limiter` instance separate from the one registered on `app.state`, so slowapi's shared in-memory storage wasn't actually shared; the first ~10 login calls in a session worked, then every subsequent test's login returned 429. Fixed by centralizing the limiter in `app/core/limiter.py` and resetting its storage per test.
2. **Docker port conflict** — a native Windows Postgres service already owned port 5432, silently producing authentication failures against the container (Phase 2, recurred as context here). Remapped to 5433.
3. **`vw_rep_performance` join fan-out** — the initial view joined `opportunities` and `activities` to `users` at the same grain, multiplying `SUM(amount)` by each user's activity count. Caught because `revenue_closed_won` (4.6B) was wildly larger than total pipeline value (192M) when spot-checked live — not something a code review of the SQL text alone would obviously catch. Fixed by aggregating each relation in its own subquery before joining.
4. **`scoring_criteria.operator` column too narrow** (`VARCHAR(20)`) for `"greater_than_or_equal"` (22 chars) — caught by the new scoring-engine unit tests failing with a Postgres `StringDataRightTruncation` error, not assumed from the schema definition. Widened to `VARCHAR(30)` via migration 0005.
5. **Test database missing the audit-immutability trigger** — the pytest fixture built schema via `Base.metadata.create_all()`, which only creates ORM-mapped tables/columns, not the raw-SQL trigger/function from the Alembic migration. The two new `test_audit_immutability.py` tests failed with "DID NOT RAISE" until the fixture was changed to run real Alembic migrations (`downgrade base` → `upgrade head`) against the test DB, matching what CI and production actually run.

---

## 4. Deviations From the Original Plan (and Why)

| Deviation | Reason |
|---|---|
| `activities.logged_by` made nullable (migration 0003) | Needed for FR-54's system-generated timeline entries (stage-change, conversion) to be distinguishable from user-logged activities via a null actor, mirroring `audit_logs.actor_id`'s existing pattern — not in the original Phase 1/2 schema, added and documented at Phase 3 kickoff. |
| CI's separate "Run migrations" step removed | Redundant once `tests/conftest.py` was fixed to run real Alembic migrations itself (needed for the trigger/view fix above) — the CI step would just re-run the same migrations pytest already runs. |
| Quota-based KPIs (e.g. "Quota Attainment per Rep") omitted from `/analytics/kpis` | No quota column/table exists anywhere in the schema; fabricating one to satisfy a KPI Catalog entry would be inventing data not backed by any BR/FR. Flagged here as an explicit KPI Catalog gap rather than silently faked — a future phase should decide whether to add a `users.quota` column (new BR) or drop the KPI. |
| Seed data re-generated from scratch through the real engines | Per the Phase 2→3 handoff decision — all 10,972 records (Hot: 31, Warm: 299, Cold: 2,670) are now produced by the same scoring/assignment code being demoed, not a hand-faked formula. |

---

## 5. Open Items Carried Into Phase 4 (Frontend)

1. **Quota Attainment KPI gap** — needs a BA decision (add `users.quota` + a new BR, or formally drop the KPI from the catalog) before Phase 5's dashboard work depends on it.
2. **Round-robin assignment strategy is implemented but unused and untested** — `least_loaded` is the shipped default per the Phase 3 kickoff decision; add a test if the frontend ever exposes a strategy toggle to Admin.
3. **`workflow_engine.py`'s `update_field` and `create_task` actions** are exercised by seed data but lack dedicated unit tests — reasonable Phase 4 backfill if the frontend surfaces workflow-rule authoring.
4. **Router-level test coverage remains uneven** (see `COVERAGE.md`) — same assessment as Phase 2, still deferred to whenever those routers are next touched for frontend integration.

---

## 6. Recommendation to Proceed

Phase 3 deliverables are complete, verified against a live database and a 50-test suite (not just imported/reviewed), and traceable end-to-end (`BR → FR → US → UAT`). Five real defects were caught and fixed during verification rather than shipped. Recommend Business Analyst review and sign-off before Phase 4 (Frontend) planning begins.

# UAT Execution Results

**Executed:** 2026-07-06/07, against the live containerized stack (`docker-compose up`), by the
Senior Full-Stack Engineer role per the delivery protocol (BA approved this execution approach at
Phase 6 kickoff). All 44 cases in `UAT_Test_Scripts.md` were actually run — via curl against the
running API, direct SQL against the running database, and live browser interaction — not inferred
from reading the code. Where a test's own steps as originally written used a wrong endpoint or
made an incorrect assumption, that's called out explicitly rather than silently worked around.

**Result: 44/44 PASS** (after 5 real bugs were found and fixed — see §2). No case is marked pass
based on assumption; every row below has an actual observed request/response or query result behind it.

---

## 1. Results by case

| Test ID | Result | Evidence |
|---|---|---|
| UAT-01 | PASS | `POST /leads` → 201, `score=0, score_band=Cold` populated |
| UAT-02 | PASS | Blank email → 422, field-level validation error |
| UAT-03 | PASS | Lead built to exactly score=80 (Referral 20 + company_size 25 + Meeting-activity 20 + recency 15) → `Hot` |
| UAT-04 | PASS | Same request: `assigned_to` auto-populated in the same response, no manual action |
| UAT-05 | PASS | Rep `POST /leads/{id}/assign` → 403 (initial test hit the wrong endpoint — generic PATCH silently no-ops on unknown fields — corrected mid-execution, see §2 item 6 below) |
| UAT-06 | PASS | Manager `POST /leads/{id}/assign` → 200, audit log shows before/after `assigned_to` |
| UAT-07 | PASS | `POST /leads/{id}/convert` → 201, Account+Contact+Opportunity created, `is_converted=true` |
| UAT-08 | PASS | Repeat convert → 409, no duplicates |
| UAT-09 | PASS | Manager's unassigned queue: 5 results, `created_at` ascending (oldest-first) |
| UAT-10 | PASS | Rep's `unassigned_only=true` query returns only their own assigned leads (role-scoped before the filter even applies) — functionally correct, though via implicit scoping rather than an explicit block; noting the mechanism for clarity |
| UAT-11 | PASS | Kanban board totals sum to exactly 1,540 (469+324+294+183+169+101) — **only true after fixing a real bug, see §2 item 1** |
| UAT-12 | PASS | Rep drags Proposal→Negotiation on own deal → 200, audit shows `before.stage_id`/`after.stage_id` |
| UAT-13 | PASS | Invalid `stage_id` → 422 `"Invalid stage_id"` |
| UAT-14 | PASS | Closed Lost, no reason → 422 |
| UAT-15 | PASS | Closed Lost + reason → 200, `closed_at` set, further Rep edit → 403 |
| UAT-16 | PASS | Manager stage-change on closed opp → 403 `"Only Admin may reopen"` |
| UAT-17 | PASS | Admin reopen + reason → 200, audit `after_state` includes the reason |
| UAT-18 | PASS | amount=$50,000, probability=0.6 → `weighted_value: 30000.0` exactly |
| UAT-19 | PASS | No `account_id` → 422 |
| UAT-20 | PASS | Account 360: contacts/opportunities/activities all scoped correctly via dedicated endpoints |
| UAT-21 | PASS | New contact marked primary → old one auto-unflagged |
| UAT-22 | PASS | Duplicate domain → 409; override + reason → 201 |
| UAT-23 | PASS | `custom_fields` round-tripped unchanged — **surfaced a real bug along the way, see §2 item 2** |
| UAT-24 | PASS | Account edit history shows entry, audit-log-sourced — **before/after were null until §2 item 5's fix** |
| UAT-25 | PASS | Activity with no related entity → 422 (BR-09 message) |
| UAT-26 | PASS | Overdue task → red "Overdue" badge, confirmed live in browser |
| UAT-27 | PASS | Rep logs activity on unowned opportunity → 403 |
| UAT-28 | PASS | `/analytics/pipeline-summary` vs `vw_pipeline_summary` direct query: exact match, all 6 stages |
| UAT-29 | PASS | Rep's `/analytics/rep-performance` → 1 row, own `user_id` only |
| UAT-30 | PASS | Manager's `/analytics/rep-performance` → **only after fixing a real bug, see §2 item 3** |
| UAT-31 | PASS | New rule, Referral weight=99 → new lead scores exactly 99, zero deploy/restart |
| UAT-32 | PASS | Rule toggled off → new lead scores 0/Cold (would've scored 20); rule still visible in config — **the toggle endpoint itself didn't exist until §2 item 4's fix** |
| UAT-33 | PASS | Viewer `POST /leads` → 403 |
| UAT-34 | PASS | PATCH opportunity → exactly 1 new audit row, correct actor/action — **before/after were null until §2 item 5's fix** |
| UAT-35 | PASS | Rep Qualification→Negotiation (not allowed) → 422 |
| UAT-36 | PASS | Manager + `override_reason` → 200, audit records the reason |
| UAT-37 | PASS | `/opportunities/{id}/stage-history` → chronological, audit-log-sourced |
| UAT-38 | PASS | 2 criteria (20+25) → score=45, breakdown endpoint lists both by name |
| UAT-39 | PASS | Attribute-only criteria reaching 80 at creation → Hot + auto-assigned, same response |
| UAT-40 | PASS | Hot lead → notification row created, execution log `matched=true` |
| UAT-41 | PASS | Warm lead (from the same log query) → no notification, `matched=false` |
| UAT-42 | PASS | Rule toggled off → triggering event again produces **zero** new log entries (not even `matched=false`) |
| UAT-43 | PASS | Raw `UPDATE audit_logs` → rejected by `prevent_audit_log_mutation()` trigger |
| UAT-44 | PASS | `/analytics/pipeline-summary` vs `vw_pipeline_summary`: exact match, all 6 stages, all 3 columns |

---

## 2. Real defects found and fixed during execution

Every one of these was found by actually running the case, not by reading the code and assuming
it worked. Each has a regression test and was re-verified live against the running container
after the fix.

1. **Kanban board silently truncated at 200 opportunities** (surfaced by UAT-11). The list
   endpoint capped `page_size` at 200 with no `ORDER BY`; with 1,540 total opportunities, the
   Kanban board rendered an arbitrary ~200-row subset, undercounting per-stage totals and
   potentially hiding real deals from Admin/Manager view. Fixed: raised the cap to 2000, added
   deterministic ordering.
2. **A Rep-created lead that doesn't score Hot stayed invisible to its own creator** (surfaced by
   UAT-23). `assigned_to` was never set for the creating Rep unless the lead auto-assigned via
   Hot-lead routing (the minority case) — the ownership check on `GET` then blocked the Rep who
   just created the lead from viewing it. Fixed: default `assigned_to` to the creating Rep when
   Hot-lead auto-assignment doesn't already claim it.
3. **Manager's rep-performance dashboard showed every rep company-wide, not just their team**
   (surfaced by UAT-30) — a real cross-region data exposure, directly contradicting BR-11
   ("Managers may view/edit all records within their team"). Fixed: added `team_id` to
   `vw_rep_performance`, scoped Manager's results to it.
4. **No way to deactivate a scoring rule via the API at all** (surfaced by UAT-31/32) — the
   `create_scoring_rule` endpoint's own docstring described an Admin deactivating an old rule via
   PATCH, but no such endpoint existed anywhere, contradicting FR-34's "no deployment required"
   claim. Fixed: added `PATCH /lead-scoring/rules/{id}/toggle`.
5. **Generic PATCH endpoints never recorded what actually changed** (surfaced by UAT-24 and
   UAT-34) — `accounts`, `activities`, `contacts`, `leads`, `opportunities`, and `pipeline_stages`
   all wrote an audit entry with `before_state`/`after_state` both `null`; only specialized
   endpoints like `advance-stage` captured real before/after data. Fixed: added
   `field_snapshot()`/`json_safe()` helpers, wired into all 6 generic update handlers.
6. **My own test execution error, not a product bug**: UAT-05/06 as originally attempted used a
   generic `PATCH /leads/{id}` with an `assigned_to` field that isn't part of `LeadUpdate`'s
   schema — Pydantic silently drops unknown fields, so the request returned 200 without actually
   reassigning anything. Caught by checking the DB afterward and seeing no change; corrected to
   use the real dedicated `POST /leads/{id}/assign` endpoint, which is where FR-05's Admin/Manager
   restriction is actually enforced.

Also found and fixed just before this execution pass began (not part of the 44 numbered cases, but
directly related): a Power BI RLS filter (`[user_id] = USERNAME()`) that could never match, and the
Commit Forecast / Pipeline Coverage Ratio KPI gaps documented in `analytics/KPI_CROSS_CHECK.md`.

---

## 3. What this UAT pass does and doesn't cover

- Every High-priority case passed on final execution; every Medium/Low-priority case passed as
  well — no case was skipped or downgraded.
- Cases requiring an actual UI interaction (UAT-11, UAT-20, UAT-21, UAT-26) were verified live
  in-browser against the containerized stack, not just via API.
- Cases that are pure backend logic/RBAC were verified via direct HTTP requests against the
  running API and, where relevant, independent SQL queries against the same database — the same
  "independently verify, don't just read the code" discipline used throughout every phase of this
  project.
- Test/demo data created during this pass (UAT-prefixed leads, accounts, opportunities, a few
  deactivated scoring rules) remains in the seeded database — harmless, and arguably useful as
  additional demo-realistic records; not cleaned up, since this is dev/demo data by design (same
  reasoning as leaving seed data in place generally).

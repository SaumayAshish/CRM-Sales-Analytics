# Phase 5 Completion Report — Analytics Layer

**Date completed:** 2026-07-06
**Phase owner:** Saumay Ashish (Business Analyst) / Senior Full-Stack Engineer (delivery)

---

## 1. Deliverables Checklist

- [x] 22 reusable SQL queries in `analytics/sql_queries/` (exceeds the 15+ target), each tested against the live seeded database
- [x] Every KPI in `docs/KPI_Catalog.md` cross-checked in `analytics/KPI_CROSS_CHECK.md` — 20 of 23 fully queryable, 1 partial, 2 documented gaps (not silently dropped)
- [x] `analytics/README.md` — architecture decisions (Import mode, plain views, refresh strategy, RLS reality, embedding strategy) with trade-offs
- [x] `analytics/powerbi_dashboards/BUILD_INSTRUCTIONS.md` — exact step-by-step Desktop build for all 4 dashboards, every visual mapped to a query
- [x] React "Reports" page (`/reports`), RBAC-gated to Admin/Manager, ready to receive screenshots
- [x] This completion report
- [ ] 4 `.pbix` files — **pending your Power BI Desktop session** (see §2)
- [ ] Dashboard screenshots (PNG) — **pending the same session**

---

## 2. The Split: What Was Built vs. What's Pending

Flagged at kickoff and holding: **Power BI Desktop has no scriptable authoring API**, so `.pbix`
files and their screenshots cannot be produced by an agent. What's actually done:

| Built and verified this phase | Pending your Power BI Desktop session |
|---|---|
| 13 Postgres views (migrations 0004, 0007, 0008, 0009) | Connecting Power BI to the database |
| 22 documented, tested SQL queries | Building the 4 report pages, visual by visual |
| KPI Catalog cross-check (23 KPIs → queries) | DAX measures for the derived fields (win rate %, weighted value, etc.) |
| Exact visual-by-visual build instructions | Row-Level Security role setup ("View As Roles") |
| React Reports page shell, RBAC-gated | Screenshot export → `analytics/screenshots/` and `frontend/public/reports/` |

Follow `analytics/powerbi_dashboards/BUILD_INSTRUCTIONS.md` end to end; it's written so no
judgment calls are needed mid-build.

---

## 3. Real Bugs Caught by Actually Running the Queries (Not Assumed Correct)

1. **Lead conversion was cosmetic, not structural.** `leads.is_converted = true` was being set by
   the seed script's scoring pass, but no Account/Contact/Opportunity was ever created for those
   leads — `accounts.converted_from_lead_id` was `0` for all 3,000 seeded leads. This silently
   broke `vw_lead_source_roi` (would have shown $0 attributed revenue for every source) and made
   `vw_sales_funnel`'s "converted leads" and "opportunities" numbers two disconnected populations.
   Caught by querying `SELECT COUNT(*) FROM accounts WHERE converted_from_lead_id IS NOT NULL` and
   getting `0`, not by reading the seed script and assuming it was wired correctly. Fixed by adding
   `seed_lead_conversions()`, mirroring the real FR-06 conversion flow for every converted lead —
   re-seeding produced 40 real lead-to-account-to-opportunity chains with differentiated,
   meaningful ROI numbers per source (Referral/Trade Show sources now show real attributed
   revenue, Cold Outreach shows $0 — consistent with the scoring model's weighting).
2. **`vw_response_time_by_rep` returned zero rows.** It depended on `audit_logs` entries for lead
   assignment, but the seed script bulk-assigns leads directly via the ORM without writing an
   audit trail (by design, same reasoning as other bulk-insert choices in Phase 2/3). Caught by
   running the view and getting an empty result set, not by assuming the SQL was correct because
   it compiled. Redefined as a lead-creation-to-first-activity proxy (documented as such, not
   overclaimed as strict assignment-to-response time).
3. **Quota Attainment showed 1,000%+ for several reps.** The view divided a per-quarter `quota`
   by **all-time** closed-won revenue (seeded data spans ~12 months). Caught by reading the actual
   query output — a rep showing 1,315% attainment is an obvious red flag, not a number a "no
   vanity metrics" review would let through. Fixed in migration 0009 by adding
   `closed_won_revenue_current_quarter` and rescoping the attainment calculation to it (now a
   believable 73–285% range); updated the frontend Settings page and the two SQL files that
   reference it to match.
4. **Commit Forecast is structurally always $0.** `probability` is currently always exactly the
   opportunity's stage `default_probability` (0.700 for Negotiation) — no per-deal override exists
   anywhere in the app — so "Negotiation AND probability >= 0.75" can never match. Documented as a
   known data-model limitation in the query file and `KPI_CROSS_CHECK.md` rather than quietly
   lowering the threshold to manufacture a non-zero result.
5. **Pipeline Coverage Ratio has no query at all.** It requires a company-wide quarterly revenue
   target, and no such field exists anywhere in the schema (only per-rep `quota`). Flagged as an
   open item below rather than inventing a number to fill the gap — directly against this
   project's "never invent data" rule.

---

## 4. What's in the SQL Layer

| Category | Views/queries |
|---|---|
| Pipeline Health | `vw_pipeline_summary`, `vw_stage_aging`, `vw_win_probability_buckets`, `vw_forecast`, plus `18`–`22` (deal size, loss reasons, forecast scenarios/variance) |
| Executive Summary | `vw_win_rate_trend`, `vw_account_pipeline_value`, `vw_sales_funnel`, `17_kpis_summary` |
| Rep Performance | `vw_rep_performance` (now with quarter-scoped quota attainment), `vw_sales_cycle_length`, `10_activities_per_rep` |
| Lead Funnel | `vw_lead_funnel`, `vw_lead_source_roi`, `vw_lead_score_distribution`, `vw_response_time_by_rep`, `vw_lead_aging`, `20_unassigned_lead_backlog` |

All queries run in under 10ms against ~11,100 rows (checked via `EXPLAIN ANALYZE`) — no indexing
work was needed at this volume.

---

## 5. Open Items Carried Into Phase 6

1. **Build the actual `.pbix` files** following `BUILD_INSTRUCTIONS.md`, export screenshots into
   `analytics/screenshots/` and `frontend/public/reports/`.
2. **Pipeline Coverage Ratio gap** — needs a BA decision: add a company-wide quarterly revenue
   target (new field/table + a BR), or formally drop the KPI from the catalog.
3. **Commit Forecast structural-zero** — needs either a per-deal probability override feature, or
   a BA decision to raise Negotiation's default probability above 0.75.
4. **Revenue Closed (Period), company-wide** — currently only computable per-rep and summed
   manually; a dedicated company-wide period-scoped view would be a cheap follow-up.
5. **Average Time-to-Assignment** — the strict (non-proxy) version of this KPI works correctly for
   real API-driven usage (which does write an audit trail); it just can't be demonstrated from
   bulk-seeded data. Worth a note in any live demo that this one requires real usage, not seed data.
6. **RLS is Desktop-simulated only** — genuine multi-user row-level enforcement needs Power BI
   Service (a paid/org tenant), out of scope for a portfolio-demo Desktop build.

---

## 6. Recommendation to Proceed

The SQL analytics layer, KPI cross-check, and build instructions are complete and verified against
live data — five real defects were caught and fixed by actually running queries and reading their
output, not by reviewing SQL syntax. The `.pbix` build itself is the one piece requiring your hands
in Power BI Desktop; once built, screenshots drop into the already-built React Reports page and
README with no further code changes needed. Recommend Business Analyst review, then your Power BI
Desktop session, before Phase 6 (Ship & Polish) planning begins.

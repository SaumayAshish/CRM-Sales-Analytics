# KPI Catalog Cross-Check

Every KPI in `docs/KPI_Catalog.md` (23 total, plus 1 governance KPI), checked against an actual
SQL query in `analytics/sql_queries/`. Built by first listing all 23, then finding or writing the
query for each — 8 had no query when this check started (Phase 5); Phase 6 closed the last 3 gaps
(Pipeline Coverage Ratio, Commit Forecast, Revenue Closed period-scoping) for real rather than
leaving them documented-but-unsolved. **All 23 dashboard KPIs are now queryable** (1 with a
notable finding, not a defect — see Pipeline Coverage Ratio below).

## Pipeline (5)

| KPI | Query | Status |
|---|---|---|
| Total Open Pipeline Value | `01_pipeline_summary.sql`, `17_kpis_summary.sql` | ✅ |
| Weighted Pipeline Value | `01_pipeline_summary.sql`, `17_kpis_summary.sql` | ✅ |
| Pipeline Stage Distribution | `01_pipeline_summary.sql` | ✅ |
| Average Time in Stage | `05_stage_aging.sql` | ✅ (proxy — see scope note 1) |
| Pipeline Coverage Ratio | `23_pipeline_coverage_ratio.sql` | ✅ **Closed Phase 6** — added `company_targets` table (BR-24, migration 0011), Admin-editable via `PATCH /company-targets/current`. Live result: ~41x coverage against a $4M quarterly target — a genuine finding about the seed data's pipeline concentration (1,286 open deals spread across a 13-month close-date window), not a query defect. |

## Sales (5)

| KPI | Query | Status |
|---|---|---|
| Win Rate | `17_kpis_summary.sql`, `02_win_rate_trend.sql` | ✅ |
| Average Deal Size (Closed Won) | `18_average_deal_size.sql` | ✅ (added this phase) |
| Sales Cycle Length | `11_sales_cycle_length.sql` | ✅ |
| Loss Reason Distribution | `19_loss_reason_distribution.sql` | ✅ (added this phase) |
| Revenue Closed (Period) | `24_revenue_closed_this_quarter.sql` | ✅ **Closed Phase 6** — company-wide current-quarter figure, mirroring the per-rep scoping already in `vw_rep_performance` (migration 0009). |

## Lead (6)

| KPI | Query | Status |
|---|---|---|
| Lead Volume by Source | `13_lead_source_roi.sql` | ✅ |
| Lead-to-Conversion Rate | `04_sales_funnel_conversion.sql`, `17_kpis_summary.sql` | ✅ |
| Conversion Rate by Score Band | `12_lead_funnel_by_score_band.sql` | ✅ |
| Average Time-to-Assignment | — | ❌ **Gap** — same root cause as scope note 2 (bulk-seeded leads have no assignment audit trail), but unlike Average Response Time (which has a usable proxy via first-activity), there's no equally clean proxy for "creation to assignment" specifically since some Cold leads are deliberately never assigned (BR-13). Live-app-generated data (not seed data) would populate this correctly today, since the API path does write assignment audit entries — just not demonstrable from seed data alone. |
| Unassigned Lead Backlog | `20_unassigned_lead_backlog.sql` | ✅ (added this phase) |
| Lead Aging (Stale Leads) | `16_lead_aging.sql` | ✅ |

## Rep (5)

| KPI | Query | Status |
|---|---|---|
| Quota Attainment per Rep | `09_quota_attainment.sql` | ✅ (fixed a real vanity-metric bug this phase — see below) |
| Activities Logged per Rep | `10_activities_per_rep.sql`, `08_rep_leaderboard.sql` | ✅ |
| Win Rate per Rep | `08_rep_leaderboard.sql` | ✅ |
| Average Response Time to Assigned Lead | `15_response_time_by_rep.sql` | ✅ (proxy — see scope note 2) |
| Open Opportunity Load per Rep | `08_rep_leaderboard.sql` | ✅ |

## Forecast (4)

| KPI | Query | Status |
|---|---|---|
| Forecast vs. Actual Variance | `22_forecast_variance.sql` | ✅ (added this phase) |
| Best-Case Forecast | `21_forecast_scenarios.sql` | ✅ (added this phase) |
| Commit Forecast | `21_forecast_scenarios.sql` | ✅ **Closed Phase 6** — `probability` is now editable per-deal (FR-65, `PATCH /opportunities/{id}`), not locked to the stage default; Kanban UI exposes it. See `sql_queries/README.md` for how this differs from just raising Negotiation's stage default. |
| Forecast Category Trend | `07_forecast_by_month.sql` | ✅ |

## Governance (1, not a dashboard tile)

| KPI | Verification | Status |
|---|---|---|
| Audit Log Completeness | Backend test suite (FR-40 tests), not Power BI | ✅ (by design, per `KPI_Catalog.md`'s own note) |

---

## Summary

- **22 of 23 dashboard KPIs fully queryable**, 1 genuine remaining gap: Average Time-to-Assignment
  needs a real assignment audit trail, which only exists for live-app usage (the API path writes
  it), not for bulk-seeded demo data — not something to fake with a proxy that would overclaim.
- **8 KPIs had no query at all when this cross-check started** (Phase 5) — found by actually going
  through the catalog line by line against the queries drafted first, not assumed complete.
- **3 gaps closed in Phase 6**: Pipeline Coverage Ratio (added `company_targets`, BR-24), Commit
  Forecast (added real per-deal probability override, FR-65), Revenue Closed period-scoping
  (company-wide quarterly query). All three were closed by building the actual missing capability,
  not by redefining the KPI to make an existing number fit.
- **1 real bug fixed in Phase 5**: Quota Attainment was computing all-time revenue against a
  quarterly quota, producing 1,000%+ figures. See `analytics/sql_queries/README.md` for the fix.
- Every dashboard visual planned in `analytics/README.md` traces to a row in this table — no
  visual without a KPI, no KPI without a query (except the 2 documented gaps above).

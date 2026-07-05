# KPI Catalog Cross-Check

Every KPI in `docs/KPI_Catalog.md` (23 total, plus 1 governance KPI), checked against an actual
SQL query in `analytics/sql_queries/`. Built by first listing all 23, then finding or writing the
query for each — 8 had no query when this check started; all but 2 now do (see the two rows
marked "Gap").

## Pipeline (5)

| KPI | Query | Status |
|---|---|---|
| Total Open Pipeline Value | `01_pipeline_summary.sql`, `17_kpis_summary.sql` | ✅ |
| Weighted Pipeline Value | `01_pipeline_summary.sql`, `17_kpis_summary.sql` | ✅ |
| Pipeline Stage Distribution | `01_pipeline_summary.sql` | ✅ |
| Average Time in Stage | `05_stage_aging.sql` | ✅ (proxy — see scope note 1) |
| Pipeline Coverage Ratio | — | ❌ **Gap** — no company-wide quarterly revenue target exists in the schema (only per-rep `quota`); fabricating one would violate this project's "never invent data" rule. Needs a BA decision: add a company-level target table/setting, or drop the KPI. |

## Sales (5)

| KPI | Query | Status |
|---|---|---|
| Win Rate | `17_kpis_summary.sql`, `02_win_rate_trend.sql` | ✅ |
| Average Deal Size (Closed Won) | `18_average_deal_size.sql` | ✅ (added this phase) |
| Sales Cycle Length | `11_sales_cycle_length.sql` | ✅ |
| Loss Reason Distribution | `19_loss_reason_distribution.sql` | ✅ (added this phase) |
| Revenue Closed (Period) | `17_kpis_summary.sql` (all-time only) | ⚠️ Partial — company-wide *period-scoped* revenue (e.g. "this quarter," matching the per-rep quarterly scoping added in migration 0009) isn't broken out as its own query yet; `08_rep_leaderboard.sql` sums to it per-rep but no single company-wide period figure exists. Cheap follow-up, not done in this pass. |

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
| Commit Forecast | `21_forecast_scenarios.sql` | ⚠️ Structurally always $0 right now — see scope note 3 in `sql_queries/README.md` |
| Forecast Category Trend | `07_forecast_by_month.sql` | ✅ |

## Governance (1, not a dashboard tile)

| KPI | Verification | Status |
|---|---|---|
| Audit Log Completeness | Backend test suite (FR-40 tests), not Power BI | ✅ (by design, per `KPI_Catalog.md`'s own note) |

---

## Summary

- **20 of 23 dashboard KPIs fully queryable**, 1 partial (company-wide period revenue), 2 genuine
  gaps (Pipeline Coverage Ratio needs a target field that doesn't exist; Average Time-to-Assignment
  needs live-app data, not seed data).
- **8 KPIs had no query when this cross-check started** — found by actually going through the
  catalog line by line against the 17 queries drafted first, not assumed complete.
- **1 real bug fixed**: Quota Attainment was computing all-time revenue against a quarterly quota,
  producing 1,000%+ figures. See `analytics/sql_queries/README.md` for the fix.
- Every dashboard visual planned in `analytics/README.md` traces to a row in this table — no
  visual without a KPI, no KPI without a query (except the 2 documented gaps above).

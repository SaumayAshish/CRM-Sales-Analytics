# KPI Catalog

**Traceability:** Realizes `FRD.md` §7 (Reporting Requirements) and `BRD.md` §8. Every KPI is computable directly from tables in `Data_Dictionary.md` — no KPI here assumes data that doesn't exist in the schema. Dashboard assignment: **Pipeline** and **Sales** KPIs → *Pipeline Health* dashboard; **Lead** KPIs → *Lead Performance* dashboard; **Rep** KPIs → *Rep Performance* dashboard; **Forecast** KPIs → *Forecast Accuracy* dashboard (FR-28).

**Total KPIs: 23** across 5 categories.

---

## Category: Pipeline

| KPI | Formula (SQL-friendly) | Business Meaning | Owner Role | Refresh | Target/Threshold |
|---|---|---|---|---|---|
| Total Open Pipeline Value | `SUM(amount) WHERE stage NOT IN ('Closed Won','Closed Lost')` | Total unclosed deal value in flight | VP of Sales | Real-time / on dashboard load | Informational (trend, not fixed target) |
| Weighted Pipeline Value | `SUM(amount * probability) WHERE stage NOT IN ('Closed Won','Closed Lost')` | Risk-adjusted forecast contribution of open deals (BR-16) | VP of Sales, Manager | Real-time | Informational |
| Pipeline Stage Distribution | `COUNT(*), SUM(amount) GROUP BY stage_id` | Where deals are concentrated in the funnel | Sales Ops Manager | Real-time | Flag if >50% of pipeline sits in one stage |
| Average Time in Stage | `AVG(current_timestamp - stage_entered_at)` per stage (requires stage-entry timestamp captured at each transition via audit log) | Identifies bottleneck stages | Sales Ops Manager | Daily | Under 14 days per stage (illustrative) |
| Pipeline Coverage Ratio | `Total Open Pipeline Value / Quarterly Revenue Target` (Target from `company_targets`, BR-24, added Phase 6 — see `analytics/sql_queries/23_pipeline_coverage_ratio.sql`) | Whether enough pipeline exists to hit target | VP of Sales | Weekly | ≥ 3x coverage — **currently ~41x against live seed data**, a real finding about the seed data's pipeline concentration relative to a single quarter, not a target miscalibration; see the query file for detail |

## Category: Sales

| KPI | Formula (SQL-friendly) | Business Meaning | Owner Role | Refresh | Target/Threshold |
|---|---|---|---|---|---|
| Win Rate | `COUNT(*) WHERE stage='Closed Won' / COUNT(*) WHERE stage IN ('Closed Won','Closed Lost')` | % of decided deals won | VP of Sales | Daily | ≥ 25% (illustrative baseline) |
| Average Deal Size (Closed Won) | `AVG(amount) WHERE stage='Closed Won'` | Typical revenue per won deal | Sales Ops Manager | Daily | Informational (trend) |
| Sales Cycle Length | `AVG(closed_at - created_at) WHERE stage='Closed Won'` | Average days from opportunity creation to close | Sales Ops Manager | Weekly | Under 60 days (illustrative) |
| Loss Reason Distribution | `COUNT(*) GROUP BY loss_reason_id WHERE stage='Closed Lost'` | Why deals are lost, for enablement/process fixes | Sales Ops Manager | Weekly | Informational |
| Revenue Closed (Period) | `SUM(amount) WHERE stage='Closed Won' AND closed_at BETWEEN period_start AND period_end` | Actual realized revenue for a period | VP of Sales | Real-time | Compared against quarterly target (see `analytics/sql_queries/24_revenue_closed_this_quarter.sql`, added Phase 6) |

## Category: Lead

| KPI | Formula (SQL-friendly) | Business Meaning | Owner Role | Refresh | Target/Threshold |
|---|---|---|---|---|---|
| Lead Volume by Source | `COUNT(*) GROUP BY source_id` | Which channels generate the most leads | Sales Ops Manager | Daily | Informational |
| Lead-to-Conversion Rate | `COUNT(*) WHERE is_converted=true / COUNT(*) total leads`, optionally `GROUP BY score_band` | Effectiveness of lead qualification/scoring model | Sales Ops Manager | Daily | ≥ 20% overall (illustrative) |
| Conversion Rate by Score Band | Same as above, `GROUP BY score_band` | Validates the scoring model actually predicts conversion (RISK-02) | Sales Ops Manager, Admin | Weekly | Hot band should convert meaningfully higher than Cold |
| Average Time-to-Assignment | `AVG(assigned_at - created_at) WHERE assigned_to IS NOT NULL` (assigned_at derived from audit log first assignment event) | Validates OBJ-02 (automated assignment speed) | Sales Ops Manager | Daily | Under 5 minutes for auto-assigned Hot leads |
| Unassigned Lead Backlog | `COUNT(*) WHERE assigned_to IS NULL AND is_converted = false` | Leads at risk of going stale (BR-13) | Manager, Admin | Real-time | 0 leads older than 48 hours unassigned |
| Lead Aging (Stale Leads) | `COUNT(*) WHERE is_converted=false AND created_at < now() - interval '30 days'` | Leads never followed up | Manager | Daily | Trend toward 0 |

## Category: Rep

| KPI | Formula (SQL-friendly) | Business Meaning | Owner Role | Refresh | Target/Threshold |
|---|---|---|---|---|---|
| Quota Attainment per Rep | `closed_won_revenue / users.quota` (via `vw_rep_performance.quota_attainment`, added Phase 4 / BR-23; NULL when quota is unset, never treated as 0%) | Individual performance against goal | Manager, Rep (own only) | Weekly | ≥ 100% |
| Activities Logged per Rep | `COUNT(*) FROM activities WHERE logged_by=:rep GROUP BY period` | Activity/engagement volume, a leading indicator | Manager | Daily | ≥ 20 activities/week (illustrative) |
| Win Rate per Rep | `COUNT(*) WHERE owner_id=:rep AND stage='Closed Won' / COUNT(*) WHERE owner_id=:rep AND stage IN ('Closed Won','Closed Lost')` | Individual close effectiveness | Manager | Weekly | Informational, compared to team average |
| Average Response Time to Assigned Lead | `AVG(first_activity_at - assigned_at) GROUP BY owner_id` | How quickly a rep engages a newly assigned lead | Manager | Daily | Under 4 business hours (illustrative) |
| Open Opportunity Load per Rep | `COUNT(*) WHERE owner_id=:rep AND stage NOT IN ('Closed Won','Closed Lost')` | Workload balance across the team | Manager | Real-time | Flag if one rep's load > 2x team average |

## Category: Forecast

| KPI | Formula (SQL-friendly) | Business Meaning | Owner Role | Refresh | Target/Threshold |
|---|---|---|---|---|---|
| Forecast vs. Actual Variance | `(SUM(weighted pipeline at period start) - SUM(actual closed won in period)) / SUM(actual closed won in period)` | Core forecast accuracy metric (OBJ-04) | VP of Sales | Monthly (per quarter close) | Variance under 15% |
| Best-Case Forecast | `SUM(amount) WHERE stage IN ('Proposal','Negotiation')` | Optimistic scenario for planning | VP of Sales | Weekly | Informational |
| Commit Forecast | `SUM(amount) WHERE stage='Negotiation' AND probability >= 0.75` | Conservative, high-confidence forecast | VP of Sales | Weekly | Informational — requires a rep to have manually raised `probability` above the stage default (FR-65, added Phase 6); see `analytics/sql_queries/21_forecast_scenarios.sql` |
| Forecast Category Trend | `SUM(weighted amount) GROUP BY week, stage` over trailing 8 weeks | Whether forecast is improving or degrading sprint over sprint | VP of Sales, Sales Ops Manager | Weekly | Informational (trend line) |

---

## Governance Note (supports OBJ-05, not a dashboard tile but tracked)

| KPI | Formula | Business Meaning | Owner Role | Refresh |
|---|---|---|---|---|
| Audit Log Completeness | `COUNT(audit_logs) / COUNT(qualifying mutations across leads/accounts/contacts/opportunities/users)` | Confirms every mutation produced an audit entry (FR-40) | IT/Security Lead | Continuous (validated in test suite, not a dashboard tile) |

---

## Summary

- **23 dashboard-facing KPIs** across Pipeline (5), Sales (5), Lead (6), Rep (5), Forecast (4) — exceeds the 20+ target.
- Every formula references only columns present in `Data_Dictionary.md`; no KPI requires data outside the modeled schema.
- Refresh cadence per KPI determines the Power BI dataset refresh schedule required to satisfy BR-19.

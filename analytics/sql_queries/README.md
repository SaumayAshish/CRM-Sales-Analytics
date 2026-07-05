# SQL Analytics Layer

22 reusable SQL queries backing the 4 Power BI dashboards, each tested against the live seeded
database (not just written and assumed correct). Most are thin wrappers around a permanent
Postgres view (created in Alembic migrations 0004, 0007, 0008, 0009), so Power BI's Navigator can
pick them up directly as tables; the rest are one-off queries not worth promoting to a view.
Queries 18–22 were added after cross-checking every dashboard visual against `docs/KPI_Catalog.md`
(see that section below) surfaced 8 KPIs with no query yet.

**Data volume:** ~11,100 business records across 21 tables. Every query here runs in under 10ms
(checked via `EXPLAIN ANALYZE`) — no indexing beyond what already exists was needed. Materialized
views were considered and rejected at this volume (see `analytics/README.md` for the trade-off).

| # | File | Dashboard | KPI Catalog entry | Backing object |
|---|---|---|---|---|
| 01 | `01_pipeline_summary.sql` | Pipeline Health, Exec Summary | Total/Weighted Open Pipeline Value, Pipeline Stage Distribution | `vw_pipeline_summary` |
| 02 | `02_win_rate_trend.sql` | Executive Summary | Win Rate (trend) | `vw_win_rate_trend` |
| 03 | `03_top_5_accounts.sql` | Executive Summary | (supports pipeline concentration) | `vw_account_pipeline_value` |
| 04 | `04_sales_funnel_conversion.sql` | Executive Summary | Lead-to-Conversion Rate | `vw_sales_funnel` |
| 05 | `05_stage_aging.sql` | Pipeline Health | Average Time in Stage | `vw_stage_aging` |
| 06 | `06_win_probability_distribution.sql` | Pipeline Health | Weighted Pipeline Value (breakdown) | `vw_win_probability_buckets` |
| 07 | `07_forecast_by_month.sql` | Pipeline Health | Forecast vs. Actual Variance | `vw_forecast` |
| 08 | `08_rep_leaderboard.sql` | Rep Performance | Win Rate per Rep, Activities Logged per Rep | `vw_rep_performance` |
| 09 | `09_quota_attainment.sql` | Rep Performance | Quota Attainment per Rep | `vw_rep_performance` |
| 10 | `10_activities_per_rep.sql` | Rep Performance | Activities Logged per Rep (by type) | direct query |
| 11 | `11_sales_cycle_length.sql` | Rep Performance | Sales Cycle Length | `vw_sales_cycle_length` |
| 12 | `12_lead_funnel_by_score_band.sql` | Lead Funnel | Conversion Rate by Score Band | `vw_lead_funnel` |
| 13 | `13_lead_source_roi.sql` | Lead Funnel | Lead Volume by Source (+ ROI) | `vw_lead_source_roi` |
| 14 | `14_lead_score_distribution.sql` | Lead Funnel | Conversion Rate by Score Band (histogram) | `vw_lead_score_distribution` |
| 15 | `15_response_time_by_rep.sql` | Lead Funnel | Average Time-to-Assignment (proxy) | `vw_response_time_by_rep` |
| 16 | `16_lead_aging.sql` | Lead Funnel | Lead Aging (Stale Leads) | `vw_lead_aging` |
| 17 | `17_kpis_summary.sql` | Executive Summary (tiles) | Aggregate of 5 headline KPIs | direct query, same views as `GET /analytics/kpis` |
| 18 | `18_average_deal_size.sql` | Executive Summary, Pipeline Health | Average Deal Size (Closed Won) | direct query |
| 19 | `19_loss_reason_distribution.sql` | Pipeline Health, Executive Summary | Loss Reason Distribution | direct query |
| 20 | `20_unassigned_lead_backlog.sql` | Lead Funnel | Unassigned Lead Backlog | direct query |
| 21 | `21_forecast_scenarios.sql` | Pipeline Health | Best-Case Forecast, Commit Forecast | direct query |
| 22 | `22_forecast_variance.sql` | Pipeline Health | Forecast vs. Actual Variance | `vw_forecast` |

## Two scope notes worth reading before using these in the dashboard build

1. **`vw_stage_aging` measures time since the last recorded stage change**, not a full historical
   reconstruction of every transition. `audit_logs` only captures field values on `UPDATE`, not the
   value at `CREATE` — so a true "time entered each stage, ever" view isn't reconstructable without
   adding a `stage_entered_at` column (a candidate follow-up, not silently assumed to already exist).
2. **`vw_response_time_by_rep` measures lead-creation-to-first-activity**, not strictly
   assignment-to-first-activity. Bulk-seeded leads never write an audit trail (the seed script
   bypasses the API layer entirely, same reasoning as Phase 2/3's other bulk-insert design
   choices), so a strict "time since assignment" query returns zero rows for seed data. The proxy
   is a close approximation for Hot leads specifically, since FR-52 auto-assigns them in the same
   transaction as scoring.
3. **`21_forecast_scenarios.sql`'s Commit Forecast is structurally always $0/NULL right now.**
   `probability` is currently always set to exactly the opportunity's stage `default_probability`
   (no per-deal override exists anywhere in the app yet), and Negotiation's stage default is 0.700
   — below the KPI's 0.75 threshold — so "Negotiation AND probability >= 0.75" can never match.
   Not patched around here; needs either a per-deal probability override feature or a BA decision
   to raise Negotiation's default probability.
4. **Pipeline Coverage Ratio (`Total Open Pipeline Value / Quarterly Revenue Target`) has no query
   at all** — there's no company-wide quarterly revenue target anywhere in the schema (only
   per-rep `quota`), and inventing one to fill this KPI in would be exactly the kind of fabricated
   number this project's rules explicitly forbid. Flagged as an open item in
   `docs/PHASE_REPORTS/phase_5.md`, not silently dropped.

## A real bug this layer caught

The first version of `quota_attainment` divided a per-quarter quota by **all-time** closed-won
revenue (the seeded data spans ~12 months), producing attainment figures over 1,000% for several
reps — a vanity-metric red flag, not a usable KPI. Caught by reading the actual query output
during this phase, not assumed correct from the SQL syntax. Fixed in migration 0009 by adding
`closed_won_revenue_current_quarter` and scoping the attainment calculation to it; `Settings.tsx`
(frontend) and `08_rep_leaderboard.sql`/`09_quota_attainment.sql` were all updated to match.

## Running these yourself

```bash
docker compose up -d db
cat analytics/sql_queries/01_pipeline_summary.sql | docker exec -i crm-sales-analytics-db-1 psql -U crm_user -d crm_sales_analytics
```

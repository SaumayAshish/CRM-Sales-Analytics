# Power BI Desktop Build Instructions

Step-by-step guide to build the 4 dashboards. Power BI Desktop has no scriptable authoring API, so
this has to be done by hand — everything here has been reduced to exact clicks, field names, and
DAX so there's no guesswork.

## Phase 6 update — action needed on the existing `.pbix`

The `crm_sales_analytics.pbix` and screenshots already in this repo were captured **before** two
Phase 6 fixes. The underlying database has since been re-seeded, so the existing file is now
stale in two ways:

1. **Commit Forecast will no longer show "--"/blank.** `21_forecast_scenarios.sql` used to return
   NULL for Commit Forecast because no opportunity's `probability` ever exceeded 0.75 (FR-65 didn't
   exist yet). It's now a real feature (editable per-deal in the Kanban UI), and the seed script
   gives ~30% of open Negotiation deals an elevated probability to simulate real usage — Commit
   Forecast now computes to a genuine ~$6.5M. **Action:** open the `.pbix`, **Home → Refresh**, and
   re-capture the Pipeline Health screenshot.
2. **A new query, `23_pipeline_coverage_ratio.sql` (backed by `vw_pipeline_coverage`), has no
   visual yet.** **Action:** add it as a new data source (same "Advanced options → SQL statement"
   pattern as the other non-view queries in §1 step 7) and add a Card visual showing
   `coverage_ratio` to the Pipeline Health page, labeled "Pipeline Coverage Ratio." Also add
   `24_revenue_closed_this_quarter.sql`'s `revenue_closed_this_quarter` as a Card on the Executive
   Summary page. Re-capture both screenshots afterward.

Everything else in this document (visual layout for the other queries, RLS setup) is unaffected.

**Prerequisite:** Power BI Desktop installed, and the database running (`docker compose up -d db`
from the repo root, then confirm `docker exec crm-sales-analytics-db-1 psql -U crm_user -d
crm_sales_analytics -c "SELECT 1"` returns a row). Power BI's PostgreSQL connector requires the
Npgsql driver — Power BI Desktop will prompt you to download it on first connection attempt if it's
missing; let it install.

---

## 1. Connect to Postgres (once, shared by all 4 dashboards)

1. Power BI Desktop → **Get Data** → **More...** → search "PostgreSQL database" → **Connect**.
2. **Server:** `localhost:5433` **Database:** `crm_sales_analytics`
3. **Data Connectivity mode:** **Import** (per `analytics/README.md` §1 — not DirectQuery).
4. Credentials: **Database** tab → username `crm_user`, password `crm_password`.
5. In the Navigator window, check the boxes for these 13 views (they'll appear under the `public`
   schema, alongside all the app's tables — don't check the tables themselves):
   - `vw_pipeline_summary`, `vw_win_rate_trend`, `vw_account_pipeline_value`, `vw_sales_funnel`,
     `vw_stage_aging`, `vw_win_probability_buckets`, `vw_forecast`, `vw_rep_performance`,
     `vw_sales_cycle_length`, `vw_lead_funnel`, `vw_lead_source_roi`,
     `vw_lead_score_distribution`, `vw_lead_aging`
6. Click **Transform Data** (not Load yet) to open Power Query Editor.
7. For the 5 queries that aren't views (`10_activities_per_rep`, `17_kpis_summary`,
   `18_average_deal_size`, `19_loss_reason_distribution`, `20_unassigned_lead_backlog`,
   `21_forecast_scenarios`, `22_forecast_variance`), add each as its own query: **Home** →
   **New Source** → **PostgreSQL database** → same server/database → in the connection dialog,
   expand **Advanced options** → paste the query's SQL directly into **SQL statement** → OK.
   Name each query after its file (e.g. `17_kpis_summary`).
8. **Close & Apply.**

---

## 2. Dashboard A — Executive Summary

**New Page**, rename to "Executive Summary."

| Visual | Type | Fields | Query |
|---|---|---|---|
| Total Pipeline Value (weighted + unweighted) | Card x2, or a single KPI visual | `total_open_pipeline_value`, `weighted_pipeline_value` | `17_kpis_summary` |
| Revenue Closed This Quarter | Card | `revenue_closed_this_quarter` | `24_revenue_closed_this_quarter` |
| Win Rate Trend (6 months) | Line chart | X: `month`, Y: `win_rate` | `vw_win_rate_trend` |
| Top 5 Accounts by Opportunity Value | Bar chart (horizontal) | Axis: `account_name`, Value: `total_value`, sorted descending, top 5 filter | `vw_account_pipeline_value` |
| Sales Funnel Conversion | Funnel visual | Stages: Total Leads → Converted Leads → Total Opportunities → Won Opportunities (build as 4 manual measures from `vw_sales_funnel`'s single row — funnel visuals want one column of stage labels + one of values, so unpivot the 4 columns into 2 via Power Query's "Unpivot columns" on `04_sales_funnel_conversion`) | `vw_sales_funnel` |
| Average Deal Size | Card | `avg_deal_size` | `18_average_deal_size` |

**Tooltip annotations** (Format visual → Tooltips, or a text box under each visual): for every
visual, add a one-line note stating the KPI Catalog name and source query, e.g. *"KPI: Total Open
Pipeline Value. Source: vw_pipeline_summary. Formula: SUM(amount) WHERE stage NOT IN (Closed
Won, Closed Lost)."*

---

## 3. Dashboard B — Pipeline Health

**New Page**, rename to "Pipeline Health."

| Visual | Type | Fields | Query |
|---|---|---|---|
| Pipeline by Stage | Funnel chart | Stage: `stage_name`, Value: `total_value`, sorted by `sort_order` | `vw_pipeline_summary` |
| Average Deal Size per Stage | Column chart | Axis: `stage_name`, Value: measure `total_value / opportunity_count` | `vw_pipeline_summary` |
| Stage Aging (stuck opportunities) | Bar chart | Axis: `stage_name`, Value: `avg_days_since_last_change` — conditional formatting: red if > 30 days | `vw_stage_aging` |
| Forecast by Close Month | Line/column combo | X: `forecast_month`, Columns: `weighted_open_pipeline`, Line: `actual_closed_won` | `vw_forecast` |
| Win Probability Distribution | Pie or donut | Legend: `probability_bucket`, Value: `total_value` | `vw_win_probability_buckets` |
| Loss Reason Distribution | Bar chart | Axis: `loss_reason`, Value: `deal_count` | `19_loss_reason_distribution` |
| Best-Case / Commit Forecast | 2 cards side by side | `best_case_forecast`, `commit_forecast` — both should now show real non-zero figures (FR-65's per-deal probability override closed this gap in Phase 6) | `21_forecast_scenarios` |
| Pipeline Coverage Ratio | Card | `coverage_ratio` — expect a large number (~40x) against live seed data; this is a genuine finding about the seed data's pipeline concentration, not a build error (see `KPI_CROSS_CHECK.md`) | `23_pipeline_coverage_ratio` |
| Forecast vs. Actual Variance | Line chart | X: `forecast_month`, Y: `variance_ratio`; add a constant reference line at 0.15 (the KPI Catalog's 15% target threshold) via Analytics pane → Constant Line | `22_forecast_variance` |

---

## 4. Dashboard C — Rep Performance

**New Page**, rename to "Rep Performance."

| Visual | Type | Fields | Query |
|---|---|---|---|
| Rep Leaderboard | Table | `first_name`, `last_name`, `closed_won_revenue`, `won_count`, `win_rate` (measure: `won_count / (won_count + lost_count)`), `activity_count` — sort by `closed_won_revenue` descending | `08_rep_leaderboard` / `vw_rep_performance` |
| Quota Attainment % | Bar chart | Axis: rep name, Value: `quota_attainment`; conditional formatting green ≥100%, red <70% | `vw_rep_performance` (filter `quota IS NOT NULL`) |
| Activities per Rep (by type) | Stacked column chart | Axis: rep name, Legend: `activity_type`, Value: `activity_count` | `10_activities_per_rep` |
| Conversion Rate per Rep | Column chart | Axis: rep name, Value: measure `won_count / (won_count + lost_count)` | `vw_rep_performance` |
| Average Sales Cycle Length per Rep | Bar chart | Axis: rep name, Value: `avg_sales_cycle_days` | `vw_sales_cycle_length` |

**RLS note:** this page is the one where "View As Role: Rep" matters most — a Rep viewing this
page (in Desktop's simulation) should see only their own row across every visual. See §5.

---

## 5. Dashboard D — Lead Funnel

**New Page**, rename to "Lead Funnel."

| Visual | Type | Fields | Query |
|---|---|---|---|
| Lead Source ROI | Table or bar chart | `source_name`, `lead_count`, `conversion_rate`, `attributed_closed_won_revenue` | `13_lead_source_roi` |
| MQL → SQL → Opportunity Conversion | Funnel | Score-band-based proxy: Cold → Warm → Hot → Converted, using `vw_lead_funnel`'s per-band lead_count/converted_count | `vw_lead_funnel` |
| Lead Scoring Distribution | Column chart | Axis: `score_bucket`, Legend: `score_band`, Value: `lead_count` | `14_lead_score_distribution` |
| Average Response Time by Rep | Bar chart | Axis: rep name, Value: `avg_response_hours` — **label this "creation to first activity," not "assignment to first activity"** per the documented proxy scope note | `15_response_time_by_rep` |
| Lead Aging Report | Column chart | Axis: `age_bucket`, Value: `lead_count`, ordered 0-7 / 7-14 / 14-30 / 30+ | `16_lead_aging` |
| Unassigned Lead Backlog | 2 cards | `unassigned_lead_count`, `unassigned_over_48h` | `20_unassigned_lead_backlog` |

---

## 6. Row-Level Security (Desktop-simulated — see `analytics/README.md` §4)

**Important correction:** an earlier draft of this doc specified `[user_id] = USERNAME()`. That's
wrong and can never match — `USERNAME()` returns a *login identity* (your Windows username in
Desktop, or the signed-in user's email/UPN when a report is published to Power BI Service), never
a UUID. Migration 0010 added `email` to `vw_rep_performance` specifically so the filter can compare
against something `USERNAME()` could plausibly equal.

**Modeling** tab → **Manage Roles** → **Create**:

1. **Role: Rep** — on the `vw_rep_performance` table, add a filter DAX expression:
   `[email] = USERNAME()`. This is the standard, actually-functional RLS pattern *when the report
   is published to Power BI Service* and reps sign in with an org account matching their seeded
   email (e.g. `rep1@northwindsales.com`) — `USERNAME()` in Service returns that signed-in user's
   UPN/email. In Desktop alone, `USERNAME()` returns your local Windows username, which won't match
   any seeded email either — see the "View As" step below for how to actually test the filter
   without a Service deployment.
2. **Role: Manager** — no filter (Managers see their full team per BR-11; team-level filtering
   would require a `team_id` column exposed on the rep-performance view, a reasonable Phase 6
   enhancement, not built this phase).
3. **Role: Viewer / Admin** — no filter.

**Modeling** → **View As** → check "Rep" → **Other user** → type a real seeded rep's email (e.g.
`rep1@northwindsales.com`) directly into the "Other user" box (View As lets you substitute a
literal value for what `USERNAME()` would return, so you don't need an actual Service deployment
to confirm the filter logic works) → confirm only that rep's row appears across every visual on
the Rep Performance page → revert before saving. Take a screenshot of this filtered view for the
README as evidence the RLS filter logic works, clearly captioned "Desktop simulation via View As,
not Service-enforced multi-user security."

---

## 7. Save and export

1. **File → Save As** → `analytics/powerbi_dashboards/crm_sales_analytics.pbix`.
2. For each of the 4 pages: **File → Export → Export to PDF** (gives you print-quality pages), or
   simpler, use **Snipping Tool**/`Win+Shift+S` to capture just the report canvas at a good
   resolution, save as PNG to `analytics/screenshots/` named `executive_summary.png`,
   `pipeline_health.png`, `rep_performance.png`, `lead_funnel.png`.
3. Copy those same 4 PNGs (or resized copies) into `frontend/public/reports/` so the React
   Reports page (`/reports`) can display them — see that page's code for the expected filenames.

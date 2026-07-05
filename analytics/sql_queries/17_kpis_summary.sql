-- Dashboard: Executive Summary (top-line KPI tiles)
-- KPI_Catalog.md: aggregate of several headline KPIs in one row, mirrors GET /analytics/kpis
-- Business question: What are the 5 numbers a VP of Sales checks first thing?
-- Source: composed directly from vw_pipeline_summary, vw_lead_funnel, vw_rep_performance
-- (same views the API's /analytics/kpis endpoint queries -- see app/api/v1/routers/analytics.py)

SELECT
    (SELECT SUM(total_value) FROM vw_pipeline_summary) AS total_open_pipeline_value,
    (SELECT SUM(weighted_value) FROM vw_pipeline_summary) AS weighted_pipeline_value,
    (SELECT ROUND(SUM(converted_count)::numeric / NULLIF(SUM(lead_count), 0), 4) FROM vw_lead_funnel) AS lead_to_conversion_rate,
    (SELECT ROUND(SUM(won_count)::numeric / NULLIF(SUM(won_count) + SUM(lost_count), 0), 4) FROM vw_rep_performance) AS win_rate,
    (SELECT SUM(closed_won_revenue) FROM vw_rep_performance) AS revenue_closed_won;

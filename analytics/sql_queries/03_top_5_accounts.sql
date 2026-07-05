-- Dashboard: Executive Summary (Top 5 accounts by opportunity value)
-- KPI_Catalog.md: supports Total Open Pipeline Value by showing concentration risk
-- Business question: Which customers represent the most revenue at stake right now?
-- Source: vw_account_pipeline_value (migration 0008)

SELECT account_name, opportunity_count, total_value, weighted_value, closed_won_value
FROM vw_account_pipeline_value
ORDER BY total_value DESC
LIMIT 5;

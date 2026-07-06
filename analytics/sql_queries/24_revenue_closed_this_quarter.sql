-- Dashboard: Executive Summary
-- KPI_Catalog.md: Revenue Closed (Period)
-- Business question: How much revenue has actually closed this quarter, company-wide?
-- Source: direct query (company-wide equivalent of the per-rep
-- closed_won_revenue_current_quarter added to vw_rep_performance in migration 0009)

SELECT SUM(o.amount) AS revenue_closed_this_quarter
FROM opportunities o
JOIN pipeline_stages ps ON ps.id = o.stage_id
WHERE o.deleted_at IS NULL AND ps.name = 'Closed Won' AND o.closed_at >= date_trunc('quarter', now());

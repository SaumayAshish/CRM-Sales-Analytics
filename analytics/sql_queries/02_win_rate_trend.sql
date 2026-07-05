-- Dashboard: Executive Summary (Win rate trend, 6 months)
-- KPI_Catalog.md: Win Rate
-- Business question: Is our close rate improving or degrading month over month?
-- Source: vw_win_rate_trend (migration 0008)

SELECT * FROM vw_win_rate_trend
WHERE month >= date_trunc('month', now()) - interval '6 months'
ORDER BY month;

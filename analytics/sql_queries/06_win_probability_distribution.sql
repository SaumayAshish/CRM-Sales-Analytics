-- Dashboard: Pipeline Health (Win probability distribution)
-- KPI_Catalog.md: Weighted Pipeline Value (supporting breakdown)
-- Business question: How much of our open pipeline is high-confidence vs. speculative?
-- Source: vw_win_probability_buckets (migration 0008)

SELECT * FROM vw_win_probability_buckets ORDER BY probability_bucket;

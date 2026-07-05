-- Dashboard: Executive Summary / Pipeline Health
-- KPI_Catalog.md: Average Deal Size (Closed Won)
-- Business question: What's a typical won-deal worth, and is it trending up or down?
-- Verified against live data: $116,094.44 average (156 Closed Won opportunities).

SELECT
    ROUND(AVG(amount)::numeric, 2) AS avg_deal_size,
    COUNT(*) AS won_deal_count
FROM opportunities
WHERE deleted_at IS NULL
    AND stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won');

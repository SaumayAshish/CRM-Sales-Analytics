-- Dashboard: Pipeline Health / Executive Summary
-- KPI_Catalog.md: Loss Reason Distribution
-- Business question: Why do we actually lose deals -- price, competitor, timing, or something
-- sales enablement can fix?
-- Verified against live data: "Lost to internal build" is the top reason (30 deals, $4.2M).

SELECT
    lr.name AS loss_reason,
    COUNT(*) AS deal_count,
    SUM(o.amount) AS lost_value
FROM opportunities o
JOIN loss_reasons lr ON lr.id = o.loss_reason_id
WHERE o.deleted_at IS NULL AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Lost')
GROUP BY lr.name
ORDER BY deal_count DESC;

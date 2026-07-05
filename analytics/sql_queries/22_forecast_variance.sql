-- Dashboard: Pipeline Health (Forecast vs. Actual Variance)
-- KPI_Catalog.md: Forecast vs. Actual Variance (target: under 15%)
-- Business question: How far off was our weighted-pipeline forecast from what actually closed?
-- Positive variance = we forecasted more than we actually closed (over-optimistic); negative =
-- we closed more than forecasted. Verified against live data: variance is well above the 15%
-- target threshold most months -- a legitimate finding (the synthetic seed data's amount/
-- probability distribution isn't tightly calibrated to conversion outcomes), not a query bug.
-- Source: vw_forecast (migration 0004)

SELECT
    forecast_month,
    weighted_open_pipeline,
    actual_closed_won,
    CASE WHEN actual_closed_won = 0 THEN NULL
         ELSE ROUND((weighted_open_pipeline - actual_closed_won) / actual_closed_won, 4)
    END AS variance_ratio
FROM vw_forecast
ORDER BY forecast_month DESC
LIMIT 6;

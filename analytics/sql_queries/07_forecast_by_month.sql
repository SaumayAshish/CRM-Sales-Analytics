-- Dashboard: Pipeline Health (Forecast by close month)
-- KPI_Catalog.md: Forecast vs. Actual Variance, Best-Case Forecast, Commit Forecast
-- Business question: What revenue should we expect to close in each upcoming month?
-- Source: vw_forecast (migration 0004)

SELECT * FROM vw_forecast
WHERE forecast_month >= date_trunc('month', now())
ORDER BY forecast_month
LIMIT 6;

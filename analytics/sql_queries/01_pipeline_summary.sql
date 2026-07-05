-- Dashboard: Pipeline Health, Executive Summary
-- KPI_Catalog.md: Total Open Pipeline Value, Weighted Pipeline Value, Pipeline Stage Distribution
-- Business question: How much is in the pipeline right now, and where is it concentrated?
-- Source: vw_pipeline_summary (migration 0004)

SELECT * FROM vw_pipeline_summary;

-- Dashboard: Pipeline Health / Executive Summary
-- KPI_Catalog.md: Pipeline Coverage Ratio (target: >= 3x coverage)
-- Business question: Is there enough pipeline in flight to hit the company's revenue target?
-- Source: vw_pipeline_coverage (migration 0011)
--
-- FINDING from running this against live data: the ratio comes back at ~41x (open pipeline
-- $164.1M vs. a $4M quarterly target) -- far above the "healthy >=3x" benchmark. Not a query bug:
-- 1,286 open opportunities average ~$127K each with expected close dates spread across a
-- 13-month window (Nov 2025-Dec 2026), an artifact of seed data sized to hit the project's 10K+
-- record target rather than calibrated to a single quarter's realistic close volume. Documented
-- here rather than silently adjusting the target to make the ratio look tidier.

SELECT * FROM vw_pipeline_coverage;

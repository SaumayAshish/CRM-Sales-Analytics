-- Dashboard: Pipeline Health (Best-Case / Commit forecast scenarios)
-- KPI_Catalog.md: Best-Case Forecast, Commit Forecast
-- Business question: What's the optimistic scenario, and what's the high-confidence-only figure?
--
-- KNOWN DATA-MODEL LIMITATION, found by running this query and getting NULL for commit_forecast:
-- `probability` is currently always set to exactly the opportunity's stage default_probability
-- (no per-deal override happens anywhere in the app yet), so "Negotiation AND probability >= 0.75"
-- can never match while Negotiation's stage default is 0.700. Commit Forecast will read as $0/NULL
-- until either (a) a rep can manually override an opportunity's probability above its stage
-- default, or (b) Negotiation's stage default is raised to 0.75+ (a BA/pipeline-configuration
-- decision, not something to silently hack around here).

SELECT
    (SELECT SUM(o.amount)
     FROM opportunities o JOIN pipeline_stages ps ON ps.id = o.stage_id
     WHERE o.deleted_at IS NULL AND o.closed_at IS NULL AND ps.name IN ('Proposal', 'Negotiation')
    ) AS best_case_forecast,
    (SELECT SUM(o.amount)
     FROM opportunities o JOIN pipeline_stages ps ON ps.id = o.stage_id
     WHERE o.deleted_at IS NULL AND o.closed_at IS NULL AND ps.name = 'Negotiation' AND o.probability >= 0.75
    ) AS commit_forecast;

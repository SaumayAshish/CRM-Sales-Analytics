-- Dashboard: Lead Funnel (Lead scoring distribution)
-- KPI_Catalog.md: Conversion Rate by Score Band (supporting histogram)
-- Business question: What does our overall lead quality mix look like right now?
-- Source: vw_lead_score_distribution (migration 0008)

SELECT * FROM vw_lead_score_distribution ORDER BY score_bucket;

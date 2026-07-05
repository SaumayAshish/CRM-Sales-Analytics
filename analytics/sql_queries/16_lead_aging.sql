-- Dashboard: Lead Funnel (Lead aging report)
-- KPI_Catalog.md: Unassigned Lead Backlog, Lead Aging (Stale Leads)
-- Business question: How many leads are we sitting on for too long without converting?
-- Source: vw_lead_aging (migration 0008)

SELECT * FROM vw_lead_aging ORDER BY age_bucket;

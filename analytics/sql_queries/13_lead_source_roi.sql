-- Dashboard: Lead Funnel (Lead source ROI -- which channels convert best)
-- KPI_Catalog.md: Lead Volume by Source (extended with attributed revenue)
-- Business question: Which lead sources are actually worth the marketing/outreach spend?
-- Source: vw_lead_source_roi (migration 0008)

SELECT * FROM vw_lead_source_roi ORDER BY attributed_closed_won_revenue DESC;

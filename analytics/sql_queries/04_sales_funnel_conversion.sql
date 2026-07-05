-- Dashboard: Executive Summary (Sales funnel conversion: Lead -> Converted -> Opportunity -> Won)
-- KPI_Catalog.md: Lead-to-Conversion Rate
-- Business question: Where do we lose the most volume in the lead-to-revenue journey?
-- Source: vw_sales_funnel (migration 0008)
-- Note: total_opportunities includes both lead-converted deals AND direct/expansion deals on
-- existing accounts (most B2B pipelines aren't 100% lead-sourced) -- this view answers "how much
-- of our funnel volume traces back to a lead" via converted_leads, not "opportunities == converted leads".

SELECT
    total_leads,
    converted_leads,
    ROUND(converted_leads::numeric / NULLIF(total_leads, 0), 4) AS lead_to_converted_rate,
    total_opportunities,
    won_opportunities,
    ROUND(won_opportunities::numeric / NULLIF(total_opportunities, 0), 4) AS opportunity_to_won_rate
FROM vw_sales_funnel;

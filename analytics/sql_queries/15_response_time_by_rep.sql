-- Dashboard: Lead Funnel (Average response time by rep)
-- KPI_Catalog.md: Average Time-to-Assignment (proxy variant, see view definition note)
-- Business question: How quickly does each rep engage a new lead after it lands?
-- Source: vw_response_time_by_rep (migration 0008)
-- Scope note: this measures lead-creation-to-first-activity, not a strict assignment-to-first-
-- activity interval -- see the view's SQL comment in migration 0008 for why (audit_logs doesn't
-- capture bulk-seeded assignment events; this proxy is accurate for auto-assigned Hot leads,
-- where assignment happens in the same transaction as creation).

SELECT * FROM vw_response_time_by_rep ORDER BY avg_response_hours ASC;

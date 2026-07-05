-- Dashboard: Lead Funnel
-- KPI_Catalog.md: Unassigned Lead Backlog
-- Business question: How many leads are sitting in the unassigned queue, and how many have
-- been there dangerously long (BR-13's 48-hour threshold)?
-- Verified against live data: 2,844 unassigned leads (mostly Cold, by design -- see BR-13 and
-- the lead-heavy funnel shape documented in docs/PHASE_REPORTS/phase_2.md).

SELECT
    COUNT(*) AS unassigned_lead_count,
    COUNT(*) FILTER (WHERE created_at < now() - interval '48 hours') AS unassigned_over_48h
FROM leads
WHERE deleted_at IS NULL AND assigned_to IS NULL AND is_converted = false;

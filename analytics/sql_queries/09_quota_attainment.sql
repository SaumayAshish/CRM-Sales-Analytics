-- Dashboard: Rep Performance (Quota attainment %)
-- KPI_Catalog.md: Quota Attainment per Rep
-- Business question: Who is on track (or behind) against their revenue target this quarter?
-- Source: vw_rep_performance (migration 0009) -- quota_attainment is NULL (not 0%) when no
-- quota is set, per BR-23's "not applicable" semantics, and is scoped to the CURRENT QUARTER's
-- closed-won revenue, not all-time (an earlier version divided all-time revenue by a quarterly
-- quota, producing 1,000%+ "attainment" -- caught during Phase 5 verification, not shipped).

SELECT first_name, last_name, quota, closed_won_revenue_current_quarter, quota_attainment
FROM vw_rep_performance
WHERE quota IS NOT NULL
ORDER BY quota_attainment DESC NULLS LAST;

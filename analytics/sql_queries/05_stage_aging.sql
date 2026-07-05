-- Dashboard: Pipeline Health (Stage aging analysis / stuck opportunities)
-- KPI_Catalog.md: Average Time in Stage
-- Business question: Which stages have deals sitting the longest without movement?
-- Source: vw_stage_aging (migration 0008)
-- IMPORTANT scope note: this measures time since each open opportunity's *last recorded stage
-- change* (or since creation if it has never changed stage) -- not a full historical
-- reconstruction of every stage transition, since audit_logs only captures field values on
-- UPDATE, not the initial value at CREATE (a stage_entered_at column would be needed for the
-- latter; flagged as a candidate follow-up in docs/PHASE_REPORTS/phase_5.md, not silently assumed).

SELECT * FROM vw_stage_aging;

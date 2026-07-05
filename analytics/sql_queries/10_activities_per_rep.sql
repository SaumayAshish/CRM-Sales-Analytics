-- Dashboard: Rep Performance (Activities per rep, by type)
-- KPI_Catalog.md: Activities Logged per Rep
-- Business question: Is activity volume (calls/emails/meetings) healthy per rep, and what's the mix?
-- Source: activities + activity_types + users (no dedicated view -- a direct query, since the
-- type-level breakdown is a one-off pivot not reused elsewhere)

SELECT
    u.first_name, u.last_name, at.name AS activity_type, COUNT(*) AS activity_count
FROM activities a
JOIN users u ON u.id = a.logged_by
JOIN activity_types at ON at.id = a.type_id
WHERE a.deleted_at IS NULL
GROUP BY u.first_name, u.last_name, at.name
ORDER BY u.last_name, activity_count DESC;

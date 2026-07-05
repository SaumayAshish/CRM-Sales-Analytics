-- Dashboard: Rep Performance (Leaderboard: deals closed, revenue, activities)
-- KPI_Catalog.md: Win Rate per Rep, Activities Logged per Rep, Open Opportunity Load per Rep
-- Business question: Who are the top and bottom performers this period, by revenue and activity?
-- Source: vw_rep_performance (migration 0004/0007/0009)
-- Note: closed_won_revenue is all-time (right for a leaderboard's "total revenue closed" figure);
-- quota_attainment is deliberately scoped to the current quarter (migration 0009) -- the two
-- numbers intentionally cover different time windows, don't expect them to be arithmetically
-- consistent with each other.

SELECT
    first_name, last_name, quota, closed_won_revenue, quota_attainment,
    won_count, lost_count,
    ROUND(won_count::numeric / NULLIF(won_count + lost_count, 0), 4) AS win_rate,
    activity_count, open_opportunity_count
FROM vw_rep_performance
ORDER BY closed_won_revenue DESC;

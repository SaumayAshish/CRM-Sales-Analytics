"""Add email to vw_rep_performance for Power BI Row-Level Security.

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-06

Traces to: analytics/powerbi_dashboards/BUILD_INSTRUCTIONS.md SS6 (RLS).
The originally-documented RLS filter `[user_id] = USERNAME()` can never
match: USERNAME() returns a login identity (Windows username in
Desktop, or the signed-in user's email/UPN in Power BI Service), never
a UUID. Caught by a correct technical review of the build instructions,
not assumed to work because the DAX was syntactically valid. Exposing
`email` lets the RLS filter be `[email] = USERNAME()` instead, which is
the standard, actually-functional pattern for a report published to
Power BI Service where reps sign in with matching org email addresses.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_rep_performance;")
    op.execute(
        """
        CREATE VIEW vw_rep_performance AS
        SELECT
            u.id AS user_id,
            u.first_name,
            u.last_name,
            u.email,
            u.quota,
            COALESCE(opp_stats.open_opportunity_count, 0) AS open_opportunity_count,
            COALESCE(opp_stats.won_count, 0) AS won_count,
            COALESCE(opp_stats.lost_count, 0) AS lost_count,
            COALESCE(opp_stats.closed_won_revenue, 0) AS closed_won_revenue,
            COALESCE(opp_stats.closed_won_revenue_current_quarter, 0) AS closed_won_revenue_current_quarter,
            COALESCE(act_stats.activity_count, 0) AS activity_count,
            CASE
                WHEN u.quota IS NULL OR u.quota = 0 THEN NULL
                ELSE ROUND(COALESCE(opp_stats.closed_won_revenue_current_quarter, 0) / u.quota, 4)
            END AS quota_attainment
        FROM users u
        LEFT JOIN (
            SELECT
                o.owner_id,
                COUNT(*) FILTER (WHERE o.deleted_at IS NULL AND o.closed_at IS NULL) AS open_opportunity_count,
                COUNT(*) FILTER (
                    WHERE o.deleted_at IS NULL AND o.closed_at IS NOT NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
                ) AS won_count,
                COUNT(*) FILTER (
                    WHERE o.deleted_at IS NULL AND o.closed_at IS NOT NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Lost')
                ) AS lost_count,
                SUM(o.amount) FILTER (
                    WHERE o.deleted_at IS NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
                ) AS closed_won_revenue,
                SUM(o.amount) FILTER (
                    WHERE o.deleted_at IS NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
                    AND o.closed_at >= date_trunc('quarter', now())
                ) AS closed_won_revenue_current_quarter
            FROM opportunities o
            GROUP BY o.owner_id
        ) opp_stats ON opp_stats.owner_id = u.id
        LEFT JOIN (
            SELECT a.logged_by, COUNT(*) AS activity_count
            FROM activities a
            WHERE a.deleted_at IS NULL AND a.logged_by IS NOT NULL
            GROUP BY a.logged_by
        ) act_stats ON act_stats.logged_by = u.id
        WHERE u.deleted_at IS NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_rep_performance;")
    op.execute(
        """
        CREATE VIEW vw_rep_performance AS
        SELECT
            u.id AS user_id,
            u.first_name,
            u.last_name,
            u.quota,
            COALESCE(opp_stats.open_opportunity_count, 0) AS open_opportunity_count,
            COALESCE(opp_stats.won_count, 0) AS won_count,
            COALESCE(opp_stats.lost_count, 0) AS lost_count,
            COALESCE(opp_stats.closed_won_revenue, 0) AS closed_won_revenue,
            COALESCE(opp_stats.closed_won_revenue_current_quarter, 0) AS closed_won_revenue_current_quarter,
            COALESCE(act_stats.activity_count, 0) AS activity_count,
            CASE
                WHEN u.quota IS NULL OR u.quota = 0 THEN NULL
                ELSE ROUND(COALESCE(opp_stats.closed_won_revenue_current_quarter, 0) / u.quota, 4)
            END AS quota_attainment
        FROM users u
        LEFT JOIN (
            SELECT
                o.owner_id,
                COUNT(*) FILTER (WHERE o.deleted_at IS NULL AND o.closed_at IS NULL) AS open_opportunity_count,
                COUNT(*) FILTER (
                    WHERE o.deleted_at IS NULL AND o.closed_at IS NOT NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
                ) AS won_count,
                COUNT(*) FILTER (
                    WHERE o.deleted_at IS NULL AND o.closed_at IS NOT NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Lost')
                ) AS lost_count,
                SUM(o.amount) FILTER (
                    WHERE o.deleted_at IS NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
                ) AS closed_won_revenue,
                SUM(o.amount) FILTER (
                    WHERE o.deleted_at IS NULL
                    AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
                    AND o.closed_at >= date_trunc('quarter', now())
                ) AS closed_won_revenue_current_quarter
            FROM opportunities o
            GROUP BY o.owner_id
        ) opp_stats ON opp_stats.owner_id = u.id
        LEFT JOIN (
            SELECT a.logged_by, COUNT(*) AS activity_count
            FROM activities a
            WHERE a.deleted_at IS NULL AND a.logged_by IS NOT NULL
            GROUP BY a.logged_by
        ) act_stats ON act_stats.logged_by = u.id
        WHERE u.deleted_at IS NULL;
        """
    )

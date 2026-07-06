"""Add team_id to vw_rep_performance and scope Manager's rep-performance view to their own team.

Revision ID: 0012
Revises: 0011
Create Date: 2026-07-06

Traces to: BR-11 ("Managers may view/edit all records within their
team," not system-wide). Found via live UAT execution (UAT-30): the
/analytics/rep-performance endpoint's own docstring claimed "Manager/
Admin see all reps" as if that were correct, but a Manager could see
every other region's rep data -- quota attainment, revenue, activity
counts -- across the whole company. A real business-sensitive data
exposure, not a cosmetic gap. This migration exposes team_id so the
endpoint (fixed in the same commit) can filter Manager results to
their own team_id, matching Admin-sees-everything/Rep-sees-own-row/
Manager-sees-own-team consistently with every other endpoint's RBAC.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
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
            u.team_id,
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

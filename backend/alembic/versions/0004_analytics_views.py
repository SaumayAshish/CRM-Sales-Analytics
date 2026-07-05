"""Analytics SQL views backing the Power BI / analytics endpoints.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-05

Traces to: FR-64, KPI_Catalog.md. Quota-based KPIs (e.g. "Quota Attainment
per Rep") are intentionally omitted -- no quota column/table exists in the
schema and fabricating one here would invent data not backed by any BR/FR;
noted in docs/PHASE_REPORTS/phase_3.md as a KPI Catalog gap for a future
phase to close explicitly, rather than silently faked.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIEW vw_pipeline_summary AS
        SELECT
            ps.id AS stage_id,
            ps.name AS stage_name,
            ps.sort_order,
            COUNT(o.id) AS opportunity_count,
            COALESCE(SUM(o.amount), 0) AS total_value,
            COALESCE(SUM(o.amount * o.probability), 0) AS weighted_value
        FROM pipeline_stages ps
        LEFT JOIN opportunities o ON o.stage_id = ps.id AND o.deleted_at IS NULL
        GROUP BY ps.id, ps.name, ps.sort_order
        ORDER BY ps.sort_order;
        """
    )

    # Aggregated in two independent subqueries (not a direct multi-table
    # JOIN) to avoid a fan-out: joining opportunities and activities to
    # users at the same grain would multiply SUM(amount) by the activity
    # count for that user, since each opportunity row would be repeated
    # once per matching activity row.
    op.execute(
        """
        CREATE VIEW vw_rep_performance AS
        SELECT
            u.id AS user_id,
            u.first_name,
            u.last_name,
            COALESCE(opp_stats.open_opportunity_count, 0) AS open_opportunity_count,
            COALESCE(opp_stats.won_count, 0) AS won_count,
            COALESCE(opp_stats.lost_count, 0) AS lost_count,
            COALESCE(opp_stats.closed_won_revenue, 0) AS closed_won_revenue,
            COALESCE(act_stats.activity_count, 0) AS activity_count
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
                ) AS closed_won_revenue
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

    op.execute(
        """
        CREATE VIEW vw_lead_funnel AS
        SELECT
            score_band,
            COUNT(*) AS lead_count,
            SUM(is_converted::int) AS converted_count,
            CASE WHEN COUNT(*) = 0 THEN 0
                 ELSE ROUND(SUM(is_converted::int)::numeric / COUNT(*), 4)
            END AS conversion_rate
        FROM leads
        WHERE deleted_at IS NULL
        GROUP BY score_band;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_forecast AS
        SELECT
            date_trunc('month', expected_close_date) AS forecast_month,
            COALESCE(SUM(amount * probability) FILTER (WHERE closed_at IS NULL), 0) AS weighted_open_pipeline,
            COALESCE(SUM(amount) FILTER (
                WHERE closed_at IS NOT NULL
                AND stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
            ), 0) AS actual_closed_won
        FROM opportunities
        WHERE deleted_at IS NULL
        GROUP BY date_trunc('month', expected_close_date)
        ORDER BY forecast_month;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_forecast;")
    op.execute("DROP VIEW IF EXISTS vw_lead_funnel;")
    op.execute("DROP VIEW IF EXISTS vw_rep_performance;")
    op.execute("DROP VIEW IF EXISTS vw_pipeline_summary;")

"""Phase 5: additional analytics views for the 4 Power BI dashboards.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-05

Traces to: FR-64, KPI_Catalog.md, docs/PHASE_REPORTS/phase_5.md. Extends
the 4 views from migrations 0004/0007 (vw_pipeline_summary,
vw_rep_performance, vw_lead_funnel, vw_forecast) with 9 more, covering
the Executive Summary, Rep Performance, and Lead Funnel dashboards'
remaining visuals.

vw_stage_aging measures time since a deal's *last recorded stage
change* (or since creation if it has never changed stage), not a full
historical reconstruction -- audit_logs only captures state on UPDATE,
not the initial value at CREATE, so a true "time entered each stage
historically" view isn't reconstructable from existing data without
adding a stage-entry timestamp column (a candidate for a future ADR,
noted in docs/PHASE_REPORTS/phase_5.md, not silently assumed away).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIEW vw_win_rate_trend AS
        SELECT
            date_trunc('month', closed_at) AS month,
            COUNT(*) FILTER (WHERE stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')) AS won_count,
            COUNT(*) FILTER (WHERE stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Lost')) AS lost_count,
            CASE WHEN COUNT(*) = 0 THEN 0
                 ELSE ROUND(
                     COUNT(*) FILTER (WHERE stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won'))::numeric
                     / COUNT(*), 4)
            END AS win_rate
        FROM opportunities
        WHERE deleted_at IS NULL AND closed_at IS NOT NULL
        GROUP BY date_trunc('month', closed_at)
        ORDER BY month;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_account_pipeline_value AS
        SELECT
            a.id AS account_id,
            a.name AS account_name,
            COUNT(o.id) AS opportunity_count,
            COALESCE(SUM(o.amount), 0) AS total_value,
            COALESCE(SUM(o.amount * o.probability), 0) AS weighted_value,
            COALESCE(SUM(o.amount) FILTER (
                WHERE o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
            ), 0) AS closed_won_value
        FROM accounts a
        LEFT JOIN opportunities o ON o.account_id = a.id AND o.deleted_at IS NULL
        WHERE a.deleted_at IS NULL
        GROUP BY a.id, a.name;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_sales_funnel AS
        SELECT
            (SELECT COUNT(*) FROM leads WHERE deleted_at IS NULL) AS total_leads,
            (SELECT COUNT(*) FROM leads WHERE deleted_at IS NULL AND is_converted) AS converted_leads,
            (SELECT COUNT(*) FROM opportunities WHERE deleted_at IS NULL) AS total_opportunities,
            (SELECT COUNT(*) FROM opportunities
                WHERE deleted_at IS NULL AND stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
            ) AS won_opportunities;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_stage_aging AS
        WITH latest_transition AS (
            SELECT entity_id AS opportunity_id, MAX(created_at) AS last_transition_at
            FROM audit_logs
            WHERE entity_type = 'opportunities' AND action = 'UPDATE' AND after_state ? 'stage_id'
            GROUP BY entity_id
        )
        SELECT
            ps.name AS stage_name,
            COUNT(*) AS opportunity_count,
            ROUND(AVG(
                EXTRACT(EPOCH FROM (now() - COALESCE(lt.last_transition_at, o.created_at))) / 86400
            )::numeric, 1) AS avg_days_since_last_change
        FROM opportunities o
        JOIN pipeline_stages ps ON ps.id = o.stage_id
        LEFT JOIN latest_transition lt ON lt.opportunity_id = o.id
        WHERE o.deleted_at IS NULL AND o.closed_at IS NULL
        GROUP BY ps.name
        ORDER BY avg_days_since_last_change DESC;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_win_probability_buckets AS
        SELECT
            CASE
                WHEN probability < 0.25 THEN '0-25%'
                WHEN probability < 0.50 THEN '25-50%'
                WHEN probability < 0.75 THEN '50-75%'
                ELSE '75-100%'
            END AS probability_bucket,
            COUNT(*) AS opportunity_count,
            COALESCE(SUM(amount), 0) AS total_value
        FROM opportunities
        WHERE deleted_at IS NULL AND closed_at IS NULL
        GROUP BY 1
        ORDER BY 1;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_lead_source_roi AS
        SELECT
            ls.name AS source_name,
            COUNT(l.id) AS lead_count,
            SUM(l.is_converted::int) AS converted_count,
            CASE WHEN COUNT(l.id) = 0 THEN 0
                 ELSE ROUND(SUM(l.is_converted::int)::numeric / COUNT(l.id), 4)
            END AS conversion_rate,
            COALESCE(SUM(o.amount) FILTER (
                WHERE o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
            ), 0) AS attributed_closed_won_revenue
        FROM lead_sources ls
        LEFT JOIN leads l ON l.source_id = ls.id AND l.deleted_at IS NULL
        LEFT JOIN accounts a ON a.converted_from_lead_id = l.id AND a.deleted_at IS NULL
        LEFT JOIN opportunities o ON o.account_id = a.id AND o.deleted_at IS NULL
        GROUP BY ls.name;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_lead_score_distribution AS
        SELECT
            CASE
                WHEN score < 0 THEN 'Below 0'
                WHEN score < 20 THEN '0-19'
                WHEN score < 40 THEN '20-39'
                WHEN score < 60 THEN '40-59'
                WHEN score < 80 THEN '60-79'
                ELSE '80+'
            END AS score_bucket,
            score_band,
            COUNT(*) AS lead_count
        FROM leads
        WHERE deleted_at IS NULL
        GROUP BY 1, score_band
        ORDER BY 1;
        """
    )

    # Proxy metric: time from lead creation to first logged activity, not a
    # strict "time since assignment" reconstruction. audit_logs only records
    # assignment events written through the API (FR-40); bulk-seeded leads
    # never go through that path (same reasoning as the seed script's other
    # audit-skipping bulk inserts), so a strict assignment-timestamp query
    # returns zero rows for seed data. Creation-to-first-activity is a very
    # close approximation for Hot leads specifically, since FR-52 auto-
    # assigns them in the same transaction as scoring/creation.
    op.execute(
        """
        CREATE VIEW vw_response_time_by_rep AS
        WITH first_activity AS (
            SELECT lead_id, logged_by, MIN(created_at) AS first_activity_at
            FROM activities
            WHERE lead_id IS NOT NULL AND logged_by IS NOT NULL AND deleted_at IS NULL
            GROUP BY lead_id, logged_by
        )
        SELECT
            u.id AS user_id,
            u.first_name,
            u.last_name,
            COUNT(fa.lead_id) AS leads_with_response,
            ROUND(AVG(
                EXTRACT(EPOCH FROM (fa.first_activity_at - l.created_at)) / 3600
            )::numeric, 1) AS avg_response_hours
        FROM first_activity fa
        JOIN leads l ON l.id = fa.lead_id AND l.deleted_at IS NULL
        JOIN users u ON u.id = fa.logged_by
        WHERE fa.first_activity_at > l.created_at
        GROUP BY u.id, u.first_name, u.last_name;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_lead_aging AS
        SELECT
            CASE
                WHEN now() - created_at < interval '7 days' THEN '0-7 days'
                WHEN now() - created_at < interval '14 days' THEN '7-14 days'
                WHEN now() - created_at < interval '30 days' THEN '14-30 days'
                ELSE '30+ days'
            END AS age_bucket,
            COUNT(*) AS lead_count
        FROM leads
        WHERE deleted_at IS NULL AND is_converted = false
        GROUP BY 1
        ORDER BY 1;
        """
    )

    op.execute(
        """
        CREATE VIEW vw_sales_cycle_length AS
        SELECT
            u.id AS user_id,
            u.first_name,
            u.last_name,
            COUNT(o.id) AS won_deal_count,
            ROUND(AVG(EXTRACT(EPOCH FROM (o.closed_at - o.created_at)) / 86400)::numeric, 1) AS avg_sales_cycle_days
        FROM opportunities o
        JOIN users u ON u.id = o.owner_id
        WHERE o.deleted_at IS NULL
            AND o.stage_id = (SELECT id FROM pipeline_stages WHERE name = 'Closed Won')
        GROUP BY u.id, u.first_name, u.last_name;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_sales_cycle_length;")
    op.execute("DROP VIEW IF EXISTS vw_lead_aging;")
    op.execute("DROP VIEW IF EXISTS vw_response_time_by_rep;")
    op.execute("DROP VIEW IF EXISTS vw_lead_score_distribution;")
    op.execute("DROP VIEW IF EXISTS vw_lead_source_roi;")
    op.execute("DROP VIEW IF EXISTS vw_win_probability_buckets;")
    op.execute("DROP VIEW IF EXISTS vw_stage_aging;")
    op.execute("DROP VIEW IF EXISTS vw_sales_funnel;")
    op.execute("DROP VIEW IF EXISTS vw_account_pipeline_value;")
    op.execute("DROP VIEW IF EXISTS vw_win_rate_trend;")

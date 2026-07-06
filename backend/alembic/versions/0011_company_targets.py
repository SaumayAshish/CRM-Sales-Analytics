"""Add company_targets table (BR-24) and a Pipeline Coverage Ratio view.

Revision ID: 0011
Revises: 0010
Create Date: 2026-07-07

Traces to: KPI_CROSS_CHECK.md's Pipeline Coverage Ratio gap -- the KPI
formula (Total Open Pipeline Value / Quarterly Revenue Target) had no
target field anywhere in the schema (only per-rep users.quota existed),
so the KPI was undocumented as a genuine gap rather than faked with an
invented number. This migration adds a real company_targets table
(Admin-editable via a new endpoint) and vw_pipeline_coverage, computing
the ratio against the current quarter's row.
"""
import uuid
from datetime import date
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("quarter_start", sa.Date, nullable=False, unique=True),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    conn = op.get_bind()
    today = date.today()
    quarter_month = ((today.month - 1) // 3) * 3 + 1
    quarter_start = date(today.year, quarter_month, 1)
    conn.execute(
        sa.text(
            "INSERT INTO company_targets (id, quarter_start, target_amount, created_at, updated_at) "
            "VALUES (gen_random_uuid(), :qs, :amt, now(), now())"
        ),
        {"qs": quarter_start, "amt": 4_000_000.00},
    )

    op.execute(
        """
        CREATE VIEW vw_pipeline_coverage AS
        SELECT
            ct.quarter_start,
            ct.target_amount,
            (SELECT SUM(o.amount)
             FROM opportunities o
             JOIN pipeline_stages ps ON ps.id = o.stage_id
             WHERE o.deleted_at IS NULL AND ps.name NOT IN ('Closed Won', 'Closed Lost')
            ) AS total_open_pipeline_value,
            ROUND(
                (SELECT SUM(o.amount)
                 FROM opportunities o
                 JOIN pipeline_stages ps ON ps.id = o.stage_id
                 WHERE o.deleted_at IS NULL AND ps.name NOT IN ('Closed Won', 'Closed Lost')
                ) / NULLIF(ct.target_amount, 0),
                4
            ) AS coverage_ratio
        FROM company_targets ct
        WHERE ct.quarter_start = date_trunc('quarter', now())::date;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_pipeline_coverage;")
    op.drop_table("company_targets")

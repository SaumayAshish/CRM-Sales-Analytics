"""Add users.quota for Quota Attainment KPI.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-05

Traces to: BR-23 (Phase 4 kickoff decision -- closes the KPI Catalog gap
flagged in docs/PHASE_REPORTS/phase_3.md). A null quota means the KPI is
not applicable for that user (e.g. Admin/Viewer), not zero attainment.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("quota", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "quota")

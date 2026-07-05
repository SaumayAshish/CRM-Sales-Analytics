"""Widen scoring_criteria.operator to fit longer operator names.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-05

Traces to: FR-50. "greater_than_or_equal" (22 chars) and
"less_than_or_equal" (19 chars) exceed the original VARCHAR(20), caught
by the Phase 3 scoring-engine unit tests exercising all four rule-type
families (test_scoring_engine.py), not assumed from a code review.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("scoring_criteria", "operator", type_=sa.String(30))


def downgrade() -> None:
    op.alter_column("scoring_criteria", "operator", type_=sa.String(20))

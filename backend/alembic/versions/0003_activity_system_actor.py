"""Allow activities.logged_by to be null for system-generated entries.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-05

Traces to: FR-54 (automatic activity logging on stage-change/conversion
uses a null logged_by, distinct from user-logged activities, mirroring
audit_logs.actor_id's existing nullable pattern for system actions).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("activities", "logged_by", nullable=True)


def downgrade() -> None:
    op.alter_column("activities", "logged_by", nullable=False)

"""Phase 3: pipeline stage transitions, audit hardening, workflow engine, notifications.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-05

Traces to: BR-21, BR-22, FR-46, FR-55, FR-56, FR-58..FR-63,
docs/Data_Dictionary.md "Addendum: Phase 3 Schema Additions".
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pipeline_stages",
        sa.Column("allowed_next_stage_ids", postgresql.JSONB(), nullable=False, server_default="[]"),
    )

    op.add_column("audit_logs", sa.Column("ip_address", sa.String(45), nullable=True))
    op.add_column("audit_logs", sa.Column("user_agent", sa.String(500), nullable=True))

    # FR-56: DB-level immutability, belt-and-suspenders on top of the app-layer
    # enforcement (no UPDATE/DELETE route ever exists for this table).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_mutation() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only: % is not permitted', TG_OP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_prevent_audit_log_mutation
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
        """
    )

    op.create_table(
        "workflow_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("trigger_event", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("conditions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("actions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_rules_trigger_event", "workflow_rules", ["trigger_event"])

    op.create_table(
        "workflow_execution_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflow_rules.id"), nullable=False),
        sa.Column("triggering_event", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("matched", sa.Boolean(), nullable=False),
        sa.Column("actions_taken", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_execution_log_rule_id", "workflow_execution_log", ["workflow_rule_id"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("link_entity_type", sa.String(50), nullable=True),
        sa.Column("link_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("workflow_execution_log")
    op.drop_table("workflow_rules")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_log_mutation ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_mutation;")
    op.drop_column("audit_logs", "user_agent")
    op.drop_column("audit_logs", "ip_address")
    op.drop_column("pipeline_stages", "allowed_next_stage_ids")

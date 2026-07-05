"""
Workflow automation models: scoring_rules, scoring_criteria, assignment_rules,
workflow_rules, workflow_execution_log.

Traces to: Data_Dictionary.md SS14, SS15, SS16 and Phase 3 addendum; BR-02,
BR-03, BR-18; FR-33, FR-34, FR-35, FR-37, FR-58..FR-61. The scoring/
assignment rule *evaluation engines* and the workflow event dispatcher are
implemented in app/services/ (Phase 3), not in these persistence models.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class ScoringRule(Base, UUIDPKMixin):
    __tablename__ = "scoring_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hot_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    warm_threshold: Mapped[int] = mapped_column(Integer, nullable=False)


class ScoringCriteria(Base, UUIDPKMixin):
    __tablename__ = "scoring_criteria"

    scoring_rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("scoring_rules.id"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    operator: Mapped[str] = mapped_column(String(30), nullable=False)
    comparison_value: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)


class AssignmentRule(Base, UUIDPKMixin):
    __tablename__ = "assignment_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WorkflowRule(Base, UUIDPKMixin, TimestampMixin):
    """Hybrid relational + JSONB storage, per Phase 3 decision (mirrors
    scoring_rules/scoring_criteria's precedent and ADR-002's JSONB-where-
    genuinely-flexible principle)."""

    __tablename__ = "workflow_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_event: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    conditions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    actions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)


class WorkflowExecutionLog(Base, UUIDPKMixin):
    """Records rule *evaluation* attempts (including non-matches), distinct
    from audit_logs which records entity state changes. Traces to FR-61."""

    __tablename__ = "workflow_execution_log"

    workflow_rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("workflow_rules.id"), nullable=False, index=True
    )
    triggering_event: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    matched: Mapped[bool] = mapped_column(Boolean, nullable=False)
    actions_taken: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

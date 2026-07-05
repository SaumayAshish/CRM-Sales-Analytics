"""
Workflow automation models: scoring_rules, scoring_criteria, assignment_rules.

Traces to: Data_Dictionary.md SS14, SS15, SS16; BR-02, BR-03, BR-18; FR-33,
FR-34, FR-35, FR-37. CRUD-level persistence only in Phase 2 — the rule
*evaluation engine* is Phase 3 scope (CLAUDE.md Backend Advanced phase).
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPKMixin


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
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    comparison_value: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)


class AssignmentRule(Base, UUIDPKMixin):
    __tablename__ = "assignment_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    strategy: Mapped[str] = mapped_column(String(30), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

"""
Lead model.

Traces to: Data_Dictionary.md SS5; BR-01, BR-02, BR-03, BR-04; FR-01, FR-02,
FR-03, FR-04, FR-07, FR-20; soft-delete addendum.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Lead(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "leads"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("lead_sources.id"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_band: Mapped[str] = mapped_column(String(10), default="Cold", nullable=False)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    scoring_rule_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("scoring_rules.id"), nullable=True
    )
    is_converted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

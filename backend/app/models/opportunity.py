"""
Opportunity model.

Traces to: Data_Dictionary.md SS10; BR-05, BR-06, BR-07, BR-16, BR-17;
FR-09, FR-12, FR-13, FR-15; soft-delete addendum.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Opportunity(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "opportunities"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    probability: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    expected_close_date: Mapped[date] = mapped_column(Date, nullable=False)
    loss_reason_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("loss_reasons.id"), nullable=True
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

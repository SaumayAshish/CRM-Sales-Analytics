"""
Activity model.

Traces to: Data_Dictionary.md SS12; BR-09; FR-23, FR-24, FR-26, FR-27;
soft-delete addendum. The "at least one related entity" rule (BR-09) is
enforced via a CHECK constraint added in the Alembic migration, since
SQLAlchemy's column-level API can't express a multi-column CHECK cleanly
in the ORM model itself. logged_by is nullable (migration 0003) to allow
system-generated timeline entries on stage-change/conversion (FR-54).
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Activity(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "activities"

    type_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("activity_types.id"), nullable=False, index=True
    )
    logged_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True, index=True
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True, index=True
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("contacts.id"), nullable=True, index=True
    )
    opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

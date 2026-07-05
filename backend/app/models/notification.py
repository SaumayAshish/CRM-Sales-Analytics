"""
Notification model.

Traces to: Data_Dictionary.md Phase 3 addendum; BR-22, FR-62, FR-63. Exists
solely to back the workflow engine's send_notification action (Module 6
infrastructure per Phase 3 scoping decision, not a standalone 8th module).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPKMixin


class Notification(Base, UUIDPKMixin):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    link_entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    link_entity_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

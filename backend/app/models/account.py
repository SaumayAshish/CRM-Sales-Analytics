"""
Account and Contact models.

Traces to: Data_Dictionary.md SS6, SS7; BR-08, BR-20; FR-17, FR-18, FR-19,
FR-20; soft-delete addendum. Contacts.is_primary uniqueness (FR-18) is
enforced via a partial unique index created in the Alembic migration
(SQLAlchemy Column-level `unique=True` cannot express a partial/WHERE
constraint), not in this model definition.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Account(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "accounts"

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    converted_from_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True
    )
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class Contact(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contacts"

    account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

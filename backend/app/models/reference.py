"""
Reference/lookup tables: roles, teams, lead_sources, pipeline_stages,
loss_reasons, activity_types.

Traces to: Data_Dictionary.md SS1, SS2, SS4, SS8, SS9, SS11; BR-01, BR-06, BR-07, BR-09.
"""

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPKMixin


class Role(Base, UUIDPKMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Team(Base, UUIDPKMixin):
    __tablename__ = "teams"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)


class LeadSource(Base, UUIDPKMixin):
    __tablename__ = "lead_sources"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)


class PipelineStage(Base, UUIDPKMixin):
    __tablename__ = "pipeline_stages"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(unique=True, nullable=False)
    default_probability: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)


class LossReason(Base, UUIDPKMixin):
    __tablename__ = "loss_reasons"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class ActivityType(Base, UUIDPKMixin):
    __tablename__ = "activity_types"

    name: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

"""
Company target schemas.

Traces to: BR-24, FR-66.
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CompanyTargetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    quarter_start: date
    target_amount: float
    created_at: datetime
    updated_at: datetime


class CompanyTargetUpdate(BaseModel):
    target_amount: float

"""
Opportunity schemas.

Traces to: FR-09, FR-12, FR-13, FR-14, FR-15.
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class OpportunityCreate(BaseModel):
    name: str
    account_id: uuid.UUID
    owner_id: uuid.UUID
    stage_id: uuid.UUID
    amount: float
    probability: float
    expected_close_date: date


class OpportunityUpdate(BaseModel):
    name: str | None = None
    owner_id: uuid.UUID | None = None
    amount: float | None = None
    probability: float | None = None
    expected_close_date: date | None = None


class OpportunityStageChangeRequest(BaseModel):
    stage_id: uuid.UUID
    loss_reason_id: uuid.UUID | None = None
    override_reason: str | None = None  # required only for Admin reopen of a closed deal (FR-14)


class OpportunityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    account_id: uuid.UUID
    owner_id: uuid.UUID
    stage_id: uuid.UUID
    amount: float
    probability: float
    expected_close_date: date
    loss_reason_id: uuid.UUID | None
    closed_at: datetime | None
    weighted_value: float
    created_at: datetime

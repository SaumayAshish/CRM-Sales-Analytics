"""
Lead schemas.

Traces to: FR-01 (required fields), FR-02/FR-03 (score/band are read-only,
system-computed), FR-06 (conversion), FR-20 (custom_fields).
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    company: str
    email: EmailStr
    phone: str | None = None
    source_id: uuid.UUID
    custom_fields: dict | None = None


class LeadUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    source_id: uuid.UUID | None = None
    custom_fields: dict | None = None


class LeadAssignRequest(BaseModel):
    assigned_to: uuid.UUID


class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str
    last_name: str
    company: str
    email: EmailStr
    phone: str | None
    source_id: uuid.UUID
    score: int
    score_band: str
    assigned_to: uuid.UUID | None
    is_converted: bool
    custom_fields: dict | None
    created_at: datetime


class LeadConvertResponse(BaseModel):
    account_id: uuid.UUID
    contact_id: uuid.UUID
    opportunity_id: uuid.UUID

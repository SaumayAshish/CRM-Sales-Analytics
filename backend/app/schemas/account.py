"""
Account and Contact schemas.

Traces to: FR-17, FR-18, FR-19, FR-20.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class AccountCreate(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    owner_id: uuid.UUID
    custom_fields: dict | None = None
    override_duplicate_warning: bool = False
    override_reason: str | None = None


class AccountUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    owner_id: uuid.UUID | None = None
    custom_fields: dict | None = None


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    domain: str | None
    industry: str | None
    owner_id: uuid.UUID
    converted_from_lead_id: uuid.UUID | None
    custom_fields: dict | None
    created_at: datetime


class ContactCreate(BaseModel):
    account_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    is_primary: bool = False


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    is_primary: bool | None = None


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    is_primary: bool
    created_at: datetime

"""
User schemas.

Traces to: FR-01 (n/a), FR-38, FR-42; Data_Dictionary.md SS3; BR-23 (quota).
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role_id: uuid.UUID
    team_id: uuid.UUID | None = None
    quota: float | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    role_id: uuid.UUID | None = None
    team_id: uuid.UUID | None = None
    is_active: bool | None = None
    quota: float | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    role_id: uuid.UUID
    team_id: uuid.UUID | None
    is_active: bool
    quota: float | None
    created_at: datetime

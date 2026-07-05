"""
Activity schemas.

Traces to: FR-23, FR-24, FR-26.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class ActivityCreate(BaseModel):
    type_id: uuid.UUID
    lead_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    opportunity_id: uuid.UUID | None = None
    notes: str | None = None
    due_at: datetime | None = None

    @model_validator(mode="after")
    def at_least_one_related_entity(self) -> "ActivityCreate":
        if not any([self.lead_id, self.account_id, self.contact_id, self.opportunity_id]):
            raise ValueError(
                "An activity must relate to at least one of lead_id, account_id, "
                "contact_id, or opportunity_id (BR-09)."
            )
        return self


class ActivityUpdate(BaseModel):
    notes: str | None = None
    is_complete: bool | None = None
    due_at: datetime | None = None


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type_id: uuid.UUID
    logged_by: uuid.UUID | None
    lead_id: uuid.UUID | None
    account_id: uuid.UUID | None
    contact_id: uuid.UUID | None
    opportunity_id: uuid.UUID | None
    notes: str | None
    is_complete: bool
    due_at: datetime | None
    created_at: datetime

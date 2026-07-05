"""
Notification schemas.

Traces to: BR-22, FR-62, FR-63.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    message: str
    link_entity_type: str | None
    link_entity_id: uuid.UUID | None
    is_read: bool
    created_at: datetime

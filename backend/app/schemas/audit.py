"""
Audit log query response schema.

Traces to: FR-44, FR-57.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID
    before_state: dict | None
    after_state: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

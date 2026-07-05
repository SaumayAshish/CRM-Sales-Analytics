"""
Pipeline stage configuration schemas.

Traces to: FR-46 (Admin-configurable transitions).
"""
import uuid

from pydantic import BaseModel, ConfigDict


class PipelineStageCreate(BaseModel):
    name: str
    sort_order: int
    default_probability: float
    allowed_next_stage_ids: list[uuid.UUID] = []


class PipelineStageUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    default_probability: float | None = None
    allowed_next_stage_ids: list[uuid.UUID] | None = None


class PipelineStageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    sort_order: int
    default_probability: float
    allowed_next_stage_ids: list[uuid.UUID]

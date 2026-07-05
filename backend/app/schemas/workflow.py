"""
Workflow rule schemas.

Traces to: FR-58, FR-59, FR-60, FR-61.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowCondition(BaseModel):
    field: str
    operator: str
    value: str


class WorkflowAction(BaseModel):
    type: str
    params: dict = {}


class WorkflowRuleCreate(BaseModel):
    name: str
    trigger_event: str
    is_active: bool = True
    conditions: list[WorkflowCondition] = []
    actions: list[WorkflowAction] = []


class WorkflowRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    trigger_event: str
    is_active: bool
    conditions: list[dict]
    actions: list[dict]
    created_at: datetime


class WorkflowExecutionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workflow_rule_id: uuid.UUID
    triggering_event: str
    entity_type: str
    entity_id: uuid.UUID
    matched: bool
    actions_taken: list[dict] | None
    created_at: datetime

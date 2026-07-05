"""
Lead scoring rule/criteria schemas.

Traces to: FR-33, FR-34, FR-49, FR-50, FR-51.
"""
import uuid

from pydantic import BaseModel, ConfigDict


class ScoringCriterionCreate(BaseModel):
    field_name: str
    operator: str
    comparison_value: str
    weight: int


class ScoringCriterionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    field_name: str
    operator: str
    comparison_value: str
    weight: int


class ScoringRuleCreate(BaseModel):
    name: str
    hot_threshold: int
    warm_threshold: int
    is_active: bool = True
    criteria: list[ScoringCriterionCreate] = []


class ScoringRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    is_active: bool
    hot_threshold: int
    warm_threshold: int


class ScoreBreakdownResponse(BaseModel):
    lead_id: uuid.UUID
    score: int
    score_band: str
    scoring_rule_id: uuid.UUID | None
    matched_criteria: list[dict]

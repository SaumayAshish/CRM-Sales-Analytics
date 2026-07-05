"""
Pipeline stage transition engine.

Traces to: BR-21, BR-06, FR-46, FR-47. Transitions are data-driven
(pipeline_stages.allowed_next_stage_ids), not a hardcoded state machine, so
Admin can reconfigure the funnel without a code change.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reference import PipelineStage

CLOSED_STAGE_NAMES = {"Closed Won", "Closed Lost"}


def validate_transition(
    db: Session, *, current_stage: PipelineStage, target_stage: PipelineStage,
    is_privileged_actor: bool, override_reason: str | None,
) -> None:
    """FR-47: reject a transition outside the current stage's allowed set
    unless a Manager/Admin supplies an override reason."""
    allowed_ids = {str(sid) for sid in (current_stage.allowed_next_stage_ids or [])}
    if str(target_stage.id) in allowed_ids:
        return

    if not is_privileged_actor:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"'{current_stage.name}' cannot transition directly to '{target_stage.name}'; "
            "this requires a Manager/Admin override with a reason.",
        )
    if not override_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="override_reason is required for a non-standard stage transition (BR-21).",
        )


def is_closed_stage(stage: PipelineStage) -> bool:
    return stage.name in CLOSED_STAGE_NAMES

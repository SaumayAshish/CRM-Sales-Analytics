"""
Pipeline stage configuration endpoints (Admin).

Traces to: FR-46 (Admin-configurable stage transitions), BR-21.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.reference import PipelineStage
from app.schemas.pipeline import PipelineStageCreate, PipelineStageRead, PipelineStageUpdate
from app.services.audit import write_audit_log

router = APIRouter()


@router.get("/stages", response_model=list[PipelineStageRead])
def list_stages(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[PipelineStage]:
    return db.query(PipelineStage).order_by(PipelineStage.sort_order.asc()).all()


@router.post("/stages", response_model=PipelineStageRead, status_code=status.HTTP_201_CREATED)
def create_stage(
    payload: PipelineStageCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> PipelineStage:
    stage = PipelineStage(
        name=payload.name, sort_order=payload.sort_order, default_probability=payload.default_probability,
        allowed_next_stage_ids=[str(sid) for sid in payload.allowed_next_stage_ids],
    )
    db.add(stage)
    db.flush()
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="pipeline_stages", entity_id=stage.id)
    db.commit()
    db.refresh(stage)
    return stage


@router.patch("/stages/{stage_id}", response_model=PipelineStageRead)
def update_stage(
    stage_id: uuid.UUID,
    payload: PipelineStageUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> PipelineStage:
    """FR-46: changing allowed_next_stage_ids takes effect immediately, no deploy."""
    stage = db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()
    if stage is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline stage not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "allowed_next_stage_ids" in update_data and update_data["allowed_next_stage_ids"] is not None:
        update_data["allowed_next_stage_ids"] = [str(sid) for sid in update_data["allowed_next_stage_ids"]]
    for field, value in update_data.items():
        setattr(stage, field, value)

    write_audit_log(db, actor_id=current_user.id, action="UPDATE", entity_type="pipeline_stages", entity_id=stage.id)
    db.commit()
    db.refresh(stage)
    return stage

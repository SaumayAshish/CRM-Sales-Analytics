"""
Read-only reference/lookup endpoints, used to populate dropdowns and to
back FR-01 (standardized lead source), FR-09 (fixed stage enum), FR-12
(loss reason list), FR-24 (activity types).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.models.reference import ActivityType, LeadSource, LossReason, PipelineStage, Role, Team
from app.schemas.lookups import (
    ActivityTypeRead,
    LeadSourceRead,
    LossReasonRead,
    PipelineStageRead,
    RoleRead,
    TeamRead,
)

router = APIRouter()


@router.get("/roles", response_model=list[RoleRead])
def list_roles(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)) -> list[Role]:
    return db.query(Role).all()


@router.get("/teams", response_model=list[TeamRead])
def list_teams(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)) -> list[Team]:
    return db.query(Team).all()


@router.get("/lead-sources", response_model=list[LeadSourceRead])
def list_lead_sources(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[LeadSource]:
    return db.query(LeadSource).all()


@router.get("/pipeline-stages", response_model=list[PipelineStageRead])
def list_pipeline_stages(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[PipelineStage]:
    return db.query(PipelineStage).order_by(PipelineStage.sort_order.asc()).all()


@router.get("/loss-reasons", response_model=list[LossReasonRead])
def list_loss_reasons(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[LossReason]:
    return db.query(LossReason).all()


@router.get("/activity-types", response_model=list[ActivityTypeRead])
def list_activity_types(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[ActivityType]:
    return db.query(ActivityType).all()

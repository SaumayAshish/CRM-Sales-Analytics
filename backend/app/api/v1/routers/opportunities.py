"""
Opportunity endpoints, including guarded stage transitions.

Traces to: FR-09 (valid stage enum), FR-12 (loss reason required on Closed
Lost), FR-13 (exactly one account/owner), FR-14 (Admin-only reopen of
Closed deals, reason required), FR-15 (weighted value), FR-16 (filtering).
"""
import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, ROLE_REP, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.opportunity import Opportunity
from app.models.reference import PipelineStage
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityRead,
    OpportunityStageChangeRequest,
    OpportunityUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter()

CLOSED_STAGE_NAMES = {"Closed Won", "Closed Lost"}


def _to_read(o: Opportunity) -> dict:
    return {**o.__dict__, "weighted_value": float(o.amount) * float(o.probability)}


def _get_stage_or_404(db: Session, stage_id: uuid.UUID) -> PipelineStage:
    stage = db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()
    if stage is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid stage_id")
    return stage


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> dict:
    """FR-13: account_id/owner_id required by the schema itself (not Optional)."""
    _get_stage_or_404(db, payload.stage_id)

    opportunity = Opportunity(**payload.model_dump())
    db.add(opportunity)
    db.flush()
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="opportunities", entity_id=opportunity.id)
    db.commit()
    db.refresh(opportunity)
    return _to_read(opportunity)


@router.get("", response_model=list[OpportunityRead])
def list_opportunities(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    stage_id: uuid.UUID | None = Query(None),
    owner_id: uuid.UUID | None = Query(None),
    close_date_from: date | None = Query(None),
    close_date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """FR-16: filter by stage/owner/close_date, server-side."""
    query = db.query(Opportunity).filter(Opportunity.deleted_at.is_(None))
    if current_user.role == ROLE_REP:
        query = query.filter(Opportunity.owner_id == current_user.id)
    if stage_id:
        query = query.filter(Opportunity.stage_id == stage_id)
    if owner_id:
        query = query.filter(Opportunity.owner_id == owner_id)
    if close_date_from:
        query = query.filter(Opportunity.expected_close_date >= close_date_from)
    if close_date_to:
        query = query.filter(Opportunity.expected_close_date <= close_date_to)

    opportunities = query.offset((page - 1) * page_size).limit(page_size).all()
    return [_to_read(o) for o in opportunities]


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(
    opportunity_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> dict:
    opportunity = (
        db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)).first()
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    if current_user.role == ROLE_REP and opportunity.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your opportunity")
    return _to_read(opportunity)


@router.patch("/{opportunity_id}", response_model=OpportunityRead)
def update_opportunity(
    opportunity_id: uuid.UUID,
    payload: OpportunityUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> dict:
    opportunity = (
        db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)).first()
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    if current_user.role == ROLE_REP and opportunity.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your opportunity")
    if opportunity.closed_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Opportunity is closed; use Admin reopen via stage endpoint")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(opportunity, field, value)

    write_audit_log(db, actor_id=current_user.id, action="UPDATE", entity_type="opportunities", entity_id=opportunity.id)
    db.commit()
    db.refresh(opportunity)
    return _to_read(opportunity)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    opportunity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> None:
    opportunity = (
        db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)).first()
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    opportunity.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, actor_id=current_user.id, action="DELETE", entity_type="opportunities", entity_id=opportunity.id)
    db.commit()
    return None


@router.post("/{opportunity_id}/advance-stage", response_model=OpportunityRead)
def advance_stage(
    opportunity_id: uuid.UUID,
    payload: OpportunityStageChangeRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> dict:
    """FR-09/FR-12/FR-14/FR-17(BR-17): the core guarded stage-transition endpoint."""
    opportunity = (
        db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)).first()
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")

    new_stage = _get_stage_or_404(db, payload.stage_id)

    # BR-17 / FR-14: closed opportunities are locked except for an Admin override with a reason.
    if opportunity.closed_at is not None:
        if current_user.role != ROLE_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Admin may reopen a closed opportunity")
        if not payload.override_reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="override_reason is required to reopen a closed opportunity (BR-17)",
            )

    # FR-12 / BR-07: loss reason required before finalizing Closed Lost.
    if new_stage.name == "Closed Lost" and payload.loss_reason_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="loss_reason_id is required when moving an opportunity to Closed Lost",
        )

    before_state = {"stage_id": str(opportunity.stage_id), "closed_at": str(opportunity.closed_at)}

    opportunity.stage_id = new_stage.id
    opportunity.probability = new_stage.default_probability
    if new_stage.name in CLOSED_STAGE_NAMES:
        opportunity.closed_at = datetime.now(timezone.utc)
        if new_stage.name == "Closed Lost":
            opportunity.loss_reason_id = payload.loss_reason_id
    else:
        opportunity.closed_at = None
        opportunity.loss_reason_id = None

    write_audit_log(
        db, actor_id=current_user.id, action="UPDATE", entity_type="opportunities", entity_id=opportunity.id,
        before_state=before_state,
        after_state={"stage_id": str(opportunity.stage_id), "override_reason": payload.override_reason},
    )
    db.commit()
    db.refresh(opportunity)
    return _to_read(opportunity)

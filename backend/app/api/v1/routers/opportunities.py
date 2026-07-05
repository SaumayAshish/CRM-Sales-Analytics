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
from app.models.audit import AuditLog
from app.models.opportunity import Opportunity
from app.models.reference import PipelineStage
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityRead,
    OpportunityStageChangeRequest,
    OpportunityUpdate,
)
from app.services.activity_log import log_system_activity
from app.services.audit import write_audit_log
from app.services.stage_engine import CLOSED_STAGE_NAMES, validate_transition
from app.services.workflow_engine import dispatch_event

router = APIRouter()


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

    current_stage = _get_stage_or_404(db, opportunity.stage_id)
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
    elif new_stage.id != current_stage.id:
        # FR-46/FR-47: transition must be in the current stage's allowed-next set,
        # unless a Manager/Admin supplies an override reason (BR-21).
        validate_transition(
            db, current_stage=current_stage, target_stage=new_stage,
            is_privileged_actor=current_user.role in (ROLE_ADMIN, ROLE_MANAGER),
            override_reason=payload.override_reason,
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
    log_system_activity(
        db, opportunity_id=opportunity.id, account_id=opportunity.account_id,
        notes=f"Stage changed from '{current_stage.name}' to '{new_stage.name}'.",
    )

    # FR-59: stage_changed always fires; opportunity_won/opportunity_lost are
    # the more specific terminal events a workflow rule may target instead.
    event_context = {
        "stage_name": new_stage.name, "owner_id": opportunity.owner_id, "amount": float(opportunity.amount),
    }
    dispatch_event(db, event="stage_changed", entity_type="opportunities", entity_id=opportunity.id, context=event_context)
    if new_stage.name == "Closed Won":
        dispatch_event(db, event="opportunity_won", entity_type="opportunities", entity_id=opportunity.id, context=event_context)
    elif new_stage.name == "Closed Lost":
        dispatch_event(db, event="opportunity_lost", entity_type="opportunities", entity_id=opportunity.id, context=event_context)

    db.commit()
    db.refresh(opportunity)
    return _to_read(opportunity)


@router.get("/{opportunity_id}/stage-history")
def get_stage_history(
    opportunity_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> list[dict]:
    """FR-48: derived from audit_logs, no separate history table."""
    opportunity = (
        db.query(Opportunity).filter(Opportunity.id == opportunity_id, Opportunity.deleted_at.is_(None)).first()
    )
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    if current_user.role == ROLE_REP and opportunity.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your opportunity")

    entries = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == "opportunities", AuditLog.entity_id == opportunity_id,
            AuditLog.action == "UPDATE",
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )
    return [
        {
            "id": e.id, "actor_id": e.actor_id, "before_state": e.before_state,
            "after_state": e.after_state, "created_at": e.created_at,
        }
        for e in entries
    ]

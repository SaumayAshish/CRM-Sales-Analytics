"""
Activity endpoints.

Traces to: FR-23 (orphan-prevention enforced in ActivityCreate validator),
FR-24 (type-specific data via notes/due_at), FR-26 (task completion/overdue),
FR-27 (Reps log only against records they own).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, ROLE_REP, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.account import Account
from app.models.activity import Activity
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.schemas.activity import ActivityCreate, ActivityRead, ActivityUpdate
from app.services.audit import write_audit_log
from app.services.lead_workflow import rescore_and_maybe_assign
from app.services.workflow_engine import dispatch_event

router = APIRouter()


def _assert_owns_related_record(db: Session, current_user: CurrentUser, payload: ActivityCreate) -> None:
    """FR-27: a Rep may log activities only against records they own."""
    if current_user.role != ROLE_REP:
        return

    if payload.lead_id:
        lead = db.query(Lead).filter(Lead.id == payload.lead_id).first()
        if lead is None or lead.assigned_to != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lead")
    if payload.account_id:
        account = db.query(Account).filter(Account.id == payload.account_id).first()
        if account is None or account.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your account")
    if payload.opportunity_id:
        opp = db.query(Opportunity).filter(Opportunity.id == payload.opportunity_id).first()
        if opp is None or opp.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your opportunity")


@router.post("", response_model=ActivityRead, status_code=status.HTTP_201_CREATED)
def create_activity(
    payload: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Activity:
    _assert_owns_related_record(db, current_user, payload)

    activity = Activity(**payload.model_dump(), logged_by=current_user.id)
    db.add(activity)
    db.flush()
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="activities", entity_id=activity.id)
    dispatch_event(
        db, event="activity_logged", entity_type="activities", entity_id=activity.id,
        context={"lead_id": str(activity.lead_id) if activity.lead_id else None},
    )

    if activity.lead_id is not None:
        # FR-49: new-activity-logged is a scoring trigger (e.g. recency/behavior criteria).
        lead = db.query(Lead).filter(Lead.id == activity.lead_id).first()
        if lead is not None:
            rescore_and_maybe_assign(db, lead)

    db.commit()
    db.refresh(activity)
    return activity


@router.get("", response_model=list[ActivityRead])
def list_activities(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    lead_id: uuid.UUID | None = Query(None),
    account_id: uuid.UUID | None = Query(None),
    opportunity_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[Activity]:
    """FR-25: chronological timeline, newest first, paginated."""
    query = db.query(Activity).filter(Activity.deleted_at.is_(None))
    if current_user.role == ROLE_REP:
        query = query.filter(Activity.logged_by == current_user.id)
    if lead_id:
        query = query.filter(Activity.lead_id == lead_id)
    if account_id:
        query = query.filter(Activity.account_id == account_id)
    if opportunity_id:
        query = query.filter(Activity.opportunity_id == opportunity_id)

    return (
        query.order_by(Activity.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/{activity_id}", response_model=ActivityRead)
def get_activity(
    activity_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> Activity:
    activity = db.query(Activity).filter(Activity.id == activity_id, Activity.deleted_at.is_(None)).first()
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return activity


@router.patch("/{activity_id}", response_model=ActivityRead)
def update_activity(
    activity_id: uuid.UUID,
    payload: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Activity:
    """FR-26: supports toggling is_complete for tasks."""
    activity = db.query(Activity).filter(Activity.id == activity_id, Activity.deleted_at.is_(None)).first()
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    if current_user.role == ROLE_REP and activity.logged_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your activity")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)

    write_audit_log(db, actor_id=current_user.id, action="UPDATE", entity_type="activities", entity_id=activity.id)
    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(
    activity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> None:
    activity = db.query(Activity).filter(Activity.id == activity_id, Activity.deleted_at.is_(None)).first()
    if activity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    activity.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, actor_id=current_user.id, action="DELETE", entity_type="activities", entity_id=activity.id)
    db.commit()
    return None

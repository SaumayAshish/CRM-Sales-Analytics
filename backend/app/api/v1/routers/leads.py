"""
Lead endpoints, including conversion and assignment.

Traces to: FR-01 (create), FR-05 (manual reassignment restricted to
Admin/Manager), FR-06 (atomic conversion), FR-07 (block re-conversion),
FR-08 (unassigned queue), FR-49 (scoring runs on create/update), FR-52
(Hot leads auto-assign via the least-loaded engine).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, ROLE_REP, CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.models.account import Account, Contact
from app.models.activity import Activity
from app.models.lead import Lead
from app.models.opportunity import Opportunity
from app.models.reference import PipelineStage
from app.schemas.activity import ActivityRead
from app.schemas.lead import LeadAssignRequest, LeadConvertResponse, LeadCreate, LeadRead, LeadUpdate
from app.services.activity_log import log_system_activity
from app.services.audit import write_audit_log
from app.services.lead_workflow import rescore_and_maybe_assign
from app.services.workflow_engine import dispatch_event

router = APIRouter()


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(
    payload: LeadCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Lead:
    """FR-01: required fields enforced by LeadCreate. FR-49: scoring engine
    runs immediately, and FR-52 auto-assigns if the lead lands Hot."""
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.flush()
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="leads", entity_id=lead.id)
    dispatch_event(
        db, event="lead_created", entity_type="leads", entity_id=lead.id,
        context={"source_id": str(lead.source_id), "owner_id": lead.assigned_to},
    )
    rescore_and_maybe_assign(db, lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("", response_model=list[LeadRead])
def list_leads(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
    status_unassigned: bool = Query(False, description="BR-13: unassigned lead queue"),
    source_id: uuid.UUID | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[Lead]:
    """FR-08: unassigned queue restricted to Manager/Admin; Reps see only their own leads."""
    query = db.query(Lead).filter(Lead.deleted_at.is_(None))

    if status_unassigned:
        if current_user.role not in (ROLE_ADMIN, ROLE_MANAGER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unassigned queue is Manager/Admin only")
        query = query.filter(Lead.assigned_to.is_(None), Lead.is_converted.is_(False))
    elif current_user.role == ROLE_REP:
        query = query.filter(Lead.assigned_to == current_user.id)

    if source_id:
        query = query.filter(Lead.source_id == source_id)
    if assigned_to:
        query = query.filter(Lead.assigned_to == assigned_to)

    return query.order_by(Lead.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(
    lead_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if current_user.role == ROLE_REP and lead.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lead")
    return lead


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if current_user.role == ROLE_REP and lead.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lead")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    write_audit_log(db, actor_id=current_user.id, action="UPDATE", entity_type="leads", entity_id=lead.id)
    rescore_and_maybe_assign(db, lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(
    lead_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> None:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    lead.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, actor_id=current_user.id, action="DELETE", entity_type="leads", entity_id=lead.id)
    db.commit()
    return None


@router.post("/{lead_id}/assign", response_model=LeadRead)
def assign_lead(
    lead_id: uuid.UUID,
    payload: LeadAssignRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> Lead:
    """FR-05: manual reassignment restricted to Admin/Manager; Rep gets 403 (BR-10)."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

    before_state = {"assigned_to": str(lead.assigned_to) if lead.assigned_to else None}
    lead.assigned_to = payload.assigned_to
    write_audit_log(
        db, actor_id=current_user.id, action="UPDATE", entity_type="leads", entity_id=lead.id,
        before_state=before_state, after_state={"assigned_to": str(payload.assigned_to)},
    )
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/{lead_id}/convert", response_model=LeadConvertResponse, status_code=status.HTTP_201_CREATED)
def convert_lead(
    lead_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER, ROLE_REP])),
) -> LeadConvertResponse:
    """FR-06/FR-07: atomic Account+Contact+Opportunity creation, blocked if already converted (BR-04)."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if lead.is_converted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lead already converted")

    owner_id = lead.assigned_to or current_user.id

    account = Account(name=lead.company, owner_id=owner_id, converted_from_lead_id=lead.id)
    db.add(account)
    db.flush()

    contact = Contact(
        account_id=account.id, first_name=lead.first_name, last_name=lead.last_name,
        email=lead.email, phone=lead.phone, is_primary=True,
    )
    db.add(contact)

    # First pipeline stage (lowest sort_order) as the starting stage for a freshly converted lead.
    first_stage = db.query(PipelineStage).order_by(PipelineStage.sort_order.asc()).first()
    if first_stage is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No pipeline stages configured")

    opportunity = Opportunity(
        name=f"{lead.company} - New Opportunity", account_id=account.id, owner_id=owner_id,
        stage_id=first_stage.id, amount=0, probability=first_stage.default_probability,
        expected_close_date=datetime.now(timezone.utc).date(),
    )
    db.add(opportunity)
    db.flush()

    lead.is_converted = True

    write_audit_log(db, actor_id=current_user.id, action="UPDATE", entity_type="leads", entity_id=lead.id,
                     after_state={"is_converted": True})
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="accounts", entity_id=account.id)
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="contacts", entity_id=contact.id)
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="opportunities", entity_id=opportunity.id)
    log_system_activity(
        db, lead_id=lead.id, account_id=account.id, opportunity_id=opportunity.id,
        notes=f"Lead converted to Account '{account.name}' and Opportunity '{opportunity.name}'.",
    )

    db.commit()
    return LeadConvertResponse(account_id=account.id, contact_id=contact.id, opportunity_id=opportunity.id)


@router.get("/{lead_id}/timeline", response_model=list[ActivityRead])
def get_lead_timeline(
    lead_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user),
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
) -> list[Activity]:
    """FR-53: chronological activity feed for a single lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at.is_(None)).first()
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    if current_user.role == ROLE_REP and lead.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your lead")

    return (
        db.query(Activity)
        .filter(Activity.lead_id == lead_id, Activity.deleted_at.is_(None))
        .order_by(Activity.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

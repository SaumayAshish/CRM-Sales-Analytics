"""
Workflow rule management endpoints (Admin).

Traces to: FR-58 (toggleable rules), FR-61 (execution log visibility).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, CurrentUser, require_role
from app.db.session import get_db
from app.models.workflow import WorkflowExecutionLog, WorkflowRule
from app.schemas.workflow import WorkflowExecutionLogRead, WorkflowRuleCreate, WorkflowRuleRead
from app.services.audit import write_audit_log

router = APIRouter()


@router.get("", response_model=list[WorkflowRuleRead])
def list_workflows(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_role([ROLE_ADMIN]))
) -> list[WorkflowRule]:
    return db.query(WorkflowRule).all()


@router.post("", response_model=WorkflowRuleRead, status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: WorkflowRuleCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> WorkflowRule:
    rule = WorkflowRule(
        name=payload.name, trigger_event=payload.trigger_event, is_active=payload.is_active,
        conditions=[c.model_dump() for c in payload.conditions],
        actions=[a.model_dump() for a in payload.actions],
    )
    db.add(rule)
    db.flush()
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="workflow_rules", entity_id=rule.id)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/{workflow_id}/toggle", response_model=WorkflowRuleRead)
def toggle_workflow(
    workflow_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> WorkflowRule:
    """FR-37/FR-58: disable/enable without deleting the rule's configuration."""
    rule = db.query(WorkflowRule).filter(WorkflowRule.id == workflow_id).first()
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow rule not found")

    rule.is_active = not rule.is_active
    write_audit_log(
        db, actor_id=current_user.id, action="UPDATE", entity_type="workflow_rules", entity_id=rule.id,
        after_state={"is_active": rule.is_active},
    )
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/{workflow_id}/execution-log", response_model=list[WorkflowExecutionLogRead])
def get_execution_log(
    workflow_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> list[WorkflowExecutionLog]:
    """FR-61: chronological record of evaluation attempts, including non-matches."""
    return (
        db.query(WorkflowExecutionLog)
        .filter(WorkflowExecutionLog.workflow_rule_id == workflow_id)
        .order_by(WorkflowExecutionLog.created_at.desc())
        .all()
    )

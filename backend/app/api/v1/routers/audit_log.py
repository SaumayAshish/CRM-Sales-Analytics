"""
Audit log query endpoints.

Traces to: FR-44, FR-57, BR-15 (no update/delete route is ever defined here).
Manager scoping interpretation: a Manager sees audit entries whose actor is
a member of their own team (i.e. their team's activity), not system-wide.
"""
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, CurrentUser, require_role
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead

router = APIRouter()


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
    entity_type: str | None = Query(None),
    actor_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> list[AuditLog]:
    query = db.query(AuditLog)

    if current_user.role == ROLE_MANAGER:
        team_user_ids = [
            u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()
        ]
        query = query.filter(AuditLog.actor_id.in_(team_user_ids))

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if date_from:
        query = query.filter(AuditLog.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(AuditLog.created_at <= datetime.combine(date_to, datetime.max.time()))

    return (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLogRead])
def get_entity_audit_history(
    entity_type: str, entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> list[AuditLog]:
    query = db.query(AuditLog).filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)

    if current_user.role == ROLE_MANAGER:
        team_user_ids = [
            u.id for u in db.query(User.id).filter(User.team_id == current_user.team_id).all()
        ]
        query = query.filter(AuditLog.actor_id.in_(team_user_ids))

    return query.order_by(AuditLog.created_at.asc()).all()

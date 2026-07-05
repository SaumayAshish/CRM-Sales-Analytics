"""
User management endpoints.

Traces to: FR-42 (Admin creates/deactivates/changes role), BR-10/11/12
(RBAC scope). GET /users/me satisfies FR-45 (profile info for UI gating).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import ROLE_ADMIN, ROLE_MANAGER, CurrentUser, get_current_user, require_role
from app.core.security import hash_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.audit import write_audit_log

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> User:
    """FR-42: only Admin may create user accounts."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_id=payload.role_id,
        team_id=payload.team_id,
    )
    db.add(user)
    db.flush()
    write_audit_log(db, actor_id=current_user.id, action="CREATE", entity_type="users", entity_id=user.id)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN, ROLE_MANAGER])),
) -> list[User]:
    """FR-42 / RACI: Admin sees all users; Manager sees their own team."""
    query = db.query(User).filter(User.deleted_at.is_(None))
    if current_user.role == ROLE_MANAGER:
        query = query.filter(User.team_id == current_user.team_id)
    return query.all()


@router.get("/me", response_model=UserRead)
def read_current_user(
    db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)
) -> User:
    """FR-45: authenticated user's own profile, for frontend UI gating."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> User:
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    before_state = {"is_active": user.is_active, "role_id": str(user.role_id)}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    write_audit_log(
        db, actor_id=current_user.id, action="UPDATE", entity_type="users", entity_id=user.id,
        before_state=before_state, after_state={"is_active": user.is_active, "role_id": str(user.role_id)},
    )
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role([ROLE_ADMIN])),
) -> None:
    """FR-42: soft delete (deactivate). Deactivated users cannot authenticate (get_current_user)."""
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    user.deleted_at = datetime.now(timezone.utc)
    write_audit_log(db, actor_id=current_user.id, action="DELETE", entity_type="users", entity_id=user.id)
    db.commit()
    return None

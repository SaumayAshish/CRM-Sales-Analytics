"""
Shared FastAPI dependencies: DB session, current user resolution, RBAC
enforcement.

Traces to: FR-38 (JWT auth), FR-39 (server-side RBAC enforcement on every
protected endpoint, not just UI hiding), Architecture.md SS5.2 (4-role model).
"""
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import JWTError, TOKEN_TYPE_ACCESS, decode_token
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Fixed 4-role model (Architecture.md SS5.2) -- never extended without a new ADR.
ROLE_ADMIN = "Admin"
ROLE_MANAGER = "Manager"
ROLE_REP = "Rep"
ROLE_VIEWER = "Viewer"


class CurrentUser:
    def __init__(self, id: uuid.UUID, role: str, team_id: uuid.UUID | None):
        self.id = id
        self.role = role
        self.team_id = team_id


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> CurrentUser:
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token")

    user_id = uuid.UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    return CurrentUser(id=user.id, role=payload["role"], team_id=user.team_id)


def require_role(allowed_roles: list[str]) -> Callable[[CurrentUser], CurrentUser]:
    """FR-39: server-side role enforcement. Denies with 403, never leaking
    whether the underlying record exists."""

    def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions")
        return current_user

    return dependency

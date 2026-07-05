"""
Auth endpoints: login, refresh, logout.

Traces to: FR-38 (JWT issuance with role claim), FR-43 (refresh-time
revocation check per ADR-003), NFR-03 (bcrypt verification).
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.core.security import (
    JWTError,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.session import get_db
from app.models.auth import RevokedToken
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, LoginRequest, RefreshRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """FR-38: authenticate and issue an access + refresh token pair."""
    user = db.query(User).filter(User.email == credentials.email, User.deleted_at.is_(None)).first()
    if user is None or not user.is_active or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    role_name = user.role.name if user.role else "Rep"
    return TokenResponse(
        access_token=create_access_token(user.id, role_name),
        refresh_token=create_refresh_token(user.id, role_name),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessTokenResponse:
    """FR-43: refresh-time revocation check against revoked_tokens (ADR-003)."""
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    if claims.get("type") != TOKEN_TYPE_REFRESH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    revoked = db.query(RevokedToken).filter(RevokedToken.token_jti == claims["jti"]).first()
    if revoked is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    user = db.query(User).filter(User.id == uuid.UUID(claims["sub"]), User.deleted_at.is_(None)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

    role_name = user.role.name if user.role else "Rep"
    return AccessTokenResponse(access_token=create_access_token(user.id, role_name))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> None:
    """FR-43: revoke a refresh token so it cannot be used to mint new access tokens."""
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        return None  # Already unusable; logout is idempotent.

    exists = db.query(RevokedToken).filter(RevokedToken.token_jti == claims["jti"]).first()
    if exists is None:
        db.add(
            RevokedToken(
                user_id=uuid.UUID(claims["sub"]),
                token_jti=claims["jti"],
                revoked_at=datetime.now(timezone.utc),
                expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
            )
        )
        db.commit()
    return None

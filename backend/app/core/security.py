"""
Password hashing and JWT issuance/validation.

Traces to: NFR-03 (bcrypt hashing, no plaintext), ADR-003 (JWT access +
refresh tokens, revocation via Postgres table checked at refresh time),
FR-38 (login issues a role-bearing JWT), FR-43 (refresh-time revocation).
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def _create_token(subject: UUID, role: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": f"{subject}-{now.timestamp()}",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: UUID, role: str) -> str:
    return _create_token(
        subject, role, TOKEN_TYPE_ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: UUID, role: str) -> str:
    return _create_token(
        subject, role, TOKEN_TYPE_REFRESH,
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Raises jose.JWTError on invalid/expired tokens; caller maps to 401."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


__all__ = [
    "hash_password", "verify_password", "create_access_token",
    "create_refresh_token", "decode_token", "JWTError",
    "TOKEN_TYPE_ACCESS", "TOKEN_TYPE_REFRESH",
]

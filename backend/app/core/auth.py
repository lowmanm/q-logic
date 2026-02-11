"""JWT authentication and role-based access control."""

import enum
from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

logger = structlog.get_logger("auth")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


# ── Roles ─────────────────────────────────────────────────────

class Role(str, enum.Enum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    AGENT = "agent"


# ── Token models ──────────────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str  # user ID
    email: str
    role: Role
    exp: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    """Injected into route handlers via Depends(get_current_user)."""
    id: UUID
    email: str
    role: Role


# ── Password hashing ─────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT creation / verification ───────────────────────────────

def create_access_token(user_id: UUID, email: str, role: Role) -> TokenResponse:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role.value,
        "exp": expires,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRY_MINUTES * 60,
    )


def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return TokenPayload(**payload)
    except JWTError as e:
        logger.warning("token_decode_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependencies ──────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> CurrentUser:
    """Extract and validate the JWT from the Authorization header."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    return CurrentUser(id=UUID(payload.sub), email=payload.email, role=payload.role)


def require_role(*allowed_roles: Role):
    """Dependency factory: restrict an endpoint to specific roles."""

    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in allowed_roles:
            logger.warning(
                "access_denied",
                user_id=str(user.id),
                required=sorted(r.value for r in allowed_roles),
                actual=user.role.value,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return user

    return _check

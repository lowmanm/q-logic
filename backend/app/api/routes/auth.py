"""Routes for user registration and login."""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    CurrentUser,
    Role,
    TokenResponse,
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserRead

logger = structlog.get_logger("routes.auth")
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_role(Role.ADMIN)),
):
    """Register a new user. Admin-only."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered.")

    new_user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info("user_registered", email=body.email, role=body.role.value)
    return UserRead(
        id=str(new_user.id),
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        is_active=new_user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive a JWT."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.hashed_password):
        logger.warning("login_failed", email=body.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled.")

    token = create_access_token(user.id, user.email, user.role)
    logger.info("login_success", email=body.email, role=user.role.value)
    return token


@router.get("/me", response_model=UserRead)
async def get_me(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile."""
    user = await db.get(User, current.id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserRead(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/seed-admin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def seed_admin(db: AsyncSession = Depends(get_db)):
    """One-time bootstrap: create an admin user if none exists.

    This endpoint is only available when no admin users exist in the database.
    """
    result = await db.execute(select(User).where(User.role == Role.ADMIN))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Admin user already exists.")

    admin = User(
        email="admin@qlogic.local",
        name="System Admin",
        hashed_password=hash_password("admin"),
        role=Role.ADMIN,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    logger.info("admin_seeded", email=admin.email)
    return UserRead(
        id=str(admin.id),
        email=admin.email,
        name=admin.name,
        role=admin.role,
        is_active=admin.is_active,
    )

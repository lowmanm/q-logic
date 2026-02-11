"""Pydantic schemas for auth endpoints."""

from pydantic import BaseModel, EmailStr

from app.core.auth import Role


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    role: Role = Role.AGENT


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    is_active: bool

    model_config = {"from_attributes": True}

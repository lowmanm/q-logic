"""Tests for the authentication system."""

import uuid

import pytest
import pytest_asyncio

from app.core.auth import (
    Role,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── Password hashing ─────────────────────────────────────────

def test_hash_and_verify():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_produces_different_hashes():
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2  # bcrypt salts


# ── JWT tokens ────────────────────────────────────────────────

def test_create_and_decode_token():
    uid = uuid.uuid4()
    token = create_access_token(uid, "test@test.com", Role.ADMIN)
    assert token.access_token
    assert token.token_type == "bearer"
    assert token.expires_in > 0

    payload = decode_token(token.access_token)
    assert payload.sub == str(uid)
    assert payload.email == "test@test.com"
    assert payload.role == Role.ADMIN


def test_decode_invalid_token():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        decode_token("not.a.valid.token")
    assert exc_info.value.status_code == 401


# ── Auth routes ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_seed_admin(client):
    """POST /api/auth/seed-admin creates the first admin."""
    resp = await client.post("/api/auth/seed-admin")
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "admin"
    assert data["email"] == "admin@qlogic.local"


@pytest.mark.asyncio
async def test_seed_admin_idempotent(client):
    """Second call should return 409."""
    await client.post("/api/auth/seed-admin")
    resp = await client.post("/api/auth/seed-admin")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    """Login with seeded admin credentials."""
    await client.post("/api/auth/seed-admin")
    resp = await client.post(
        "/api/auth/login",
        json={"email": "admin@qlogic.local", "password": "admin"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_bad_password(client):
    await client.post("/api/auth/seed-admin")
    resp = await client.post(
        "/api/auth/login",
        json={"email": "admin@qlogic.local", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client):
    """GET /api/auth/me returns the user's profile."""
    await client.post("/api/auth/seed-admin")
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "admin@qlogic.local", "password": "admin"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "admin@qlogic.local"

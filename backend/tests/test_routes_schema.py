"""Tests for schema routes — verifies auth protection and basic functionality."""

import io
import pytest


def _csv_bytes(headers: list[str], rows: list[list[str]]) -> bytes:
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row))
    return "\n".join(lines).encode("utf-8")


@pytest.mark.asyncio
async def test_infer_requires_auth(client):
    """POST /api/schema/infer should return 401 without a token."""
    csv = _csv_bytes(["id", "name"], [["1", "Alice"]])
    resp = await client.post(
        "/api/schema/infer",
        files={"file": ("test.csv", io.BytesIO(csv), "text/csv")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_infer_with_auth(auth_client):
    """POST /api/schema/infer succeeds with a valid token."""
    csv = _csv_bytes(["id", "name"], [["1", "Alice"], ["2", "Bob"]])
    resp = await auth_client.post(
        "/api/schema/infer",
        files={"file": ("test.csv", io.BytesIO(csv), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "test.csv"
    assert data["row_count"] == 2
    assert len(data["columns"]) == 2


@pytest.mark.asyncio
async def test_infer_rejects_non_csv(auth_client):
    """Non-CSV files should be rejected."""
    resp = await auth_client.post(
        "/api/schema/infer",
        files={"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_provision_requires_admin_or_supervisor(client, agent_token):
    """Agents should not be able to provision tables."""
    resp = await client.post(
        "/api/schema/provision",
        json={
            "project_name": "test_project",
            "columns": [
                {
                    "original_name": "id",
                    "display_name": "ID",
                    "data_type": "INTEGER",
                    "is_unique_id": True,
                }
            ],
        },
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 403

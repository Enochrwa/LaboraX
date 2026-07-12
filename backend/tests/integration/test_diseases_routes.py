"""Integration tests for `GET /api/v1/diseases` — Sprint 6's lightweight
disease-template listing endpoint (see `app/api/v1/routes/diseases.py`)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.models.disease import Disease
from tests.conftest import fixture_credential

pytestmark = pytest.mark.anyio


async def _register_and_login(client: AsyncClient, *, role: str, email: str) -> str:
    password = fixture_credential()
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password, "role": role},
    )
    assert response.status_code == 201
    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    return str(login_response.json()["access_token"])


async def test_list_diseases_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/diseases")
    assert response.status_code == 401


async def test_list_diseases_returns_seeded_templates_name_sorted(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client, role="student", email="student@laborax.dev")
    response = await client.get("/api/v1/diseases", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    names = [d["name"] for d in response.json()]
    assert names == sorted(names)
    assert "Malaria" in names


async def test_list_diseases_filters_by_category(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client, role="lecturer", email="lecturer@laborax.dev")
    response = await client.get(
        "/api/v1/diseases",
        headers={"Authorization": f"Bearer {token}"},
        params={"category": "hematology"},
    )
    assert response.status_code == 200
    assert all(d["category"] == "hematology" for d in response.json())

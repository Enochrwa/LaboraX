"""Integration tests for the register/login/refresh/me auth flow."""

import pytest
from httpx import AsyncClient

from tests.conftest import fixture_credential

pytestmark = pytest.mark.anyio


async def _register(
    client: AsyncClient,
    password: str,
    email: str = "student@laborax.dev",
    role: str = "student",
) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Ada Lovelace",
            "password": password,
            "role": role,
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_register_creates_a_user(client: AsyncClient) -> None:
    body = await _register(client, fixture_credential())
    assert body["email"] == "student@laborax.dev"
    assert body["role"] == "student"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body


async def test_register_rejects_duplicate_email(client: AsyncClient) -> None:
    await _register(client, fixture_credential())
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "student@laborax.dev",
            "full_name": "Another Student",
            "password": fixture_credential(),
            "role": "student",
        },
    )
    assert response.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "shortpw@laborax.dev",
            "full_name": "Short Password",
            "password": "short",
            "role": "student",
        },
    )
    assert response.status_code == 422


async def test_login_returns_token_pair(client: AsyncClient) -> None:
    password = fixture_credential()
    await _register(client, password)
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "student@laborax.dev", "password": password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    await _register(client, fixture_credential())
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "student@laborax.dev", "password": "a-different-value"},
    )
    assert response.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@laborax.dev", "password": fixture_credential()},
    )
    assert response.status_code == 401


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client: AsyncClient) -> None:
    password = fixture_credential()
    await _register(client, password)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "student@laborax.dev", "password": password},
    )
    access_token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "student@laborax.dev"


async def test_me_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


async def test_refresh_issues_a_new_token_pair(client: AsyncClient) -> None:
    password = fixture_credential()
    await _register(client, password)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "student@laborax.dev", "password": password},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


async def test_refresh_rejects_an_access_token(client: AsyncClient) -> None:
    password = fixture_credential()
    await _register(client, password)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "student@laborax.dev", "password": password},
    )
    access_token = login_response.json()["access_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401

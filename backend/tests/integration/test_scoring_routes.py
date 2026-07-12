"""Integration tests for `GET /api/v1/scoring/me` — Sprint 5's personal
progress endpoint. Exercises the full submit-interpretation -> mastery-update
-> read-scoring-summary loop end to end against the real test DB."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.models.disease import Disease
from app.db.models.test_catalog import TestCatalog
from tests.conftest import fixture_credential

pytestmark = pytest.mark.anyio


async def _register_and_login(
    client: AsyncClient, *, role: str = "student", email: str = "student@laborax.dev"
) -> str:
    password = fixture_credential()
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Ada Lovelace", "password": password, "role": role},
    )
    assert response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    return str(login_response.json()["access_token"])


async def _generate_case(client: AsyncClient, headers: dict[str, str], disease_name: str) -> str:
    response = await client.get(
        "/api/v1/cases/next",
        headers=headers,
        params={"disease_name": disease_name},
    )
    assert response.status_code == 200
    return str(response.json()["id"])


async def test_scoring_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/scoring/me")
    assert response.status_code == 401


async def test_scoring_me_rejects_non_students(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client, role="lecturer", email="lecturer@laborax.dev")
    response = await client.get("/api/v1/scoring/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


async def test_scoring_me_returns_empty_summary_for_new_student(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    response = await client.get("/api/v1/scoring/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["topics"] == []
    assert body["overall_mastery"] == 0.0
    assert body["total_attempts"] == 0
    assert body["recent_attempts"] == []


async def test_scoring_me_reflects_mastery_after_submitting_an_interpretation(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    free_text = (
        "The hemoglobin is decreased, consistent with a hemolytic anemia. "
        "Platelets are low, showing thrombocytopenia. "
        "The blood film shows ring-form trophozoites. "
        "White cell count is roughly normal. "
        "Reticulocyte count is elevated due to compensatory marrow response."
    )
    submit_response = await client.post(
        "/api/v1/interpretations",
        headers=headers,
        json={"case_id": case_id, "free_text": free_text},
    )
    assert submit_response.status_code == 201

    response = await client.get("/api/v1/scoring/me", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["total_attempts"] == 1
    assert len(body["recent_attempts"]) == 1
    assert body["recent_attempts"][0]["case_id"] == case_id

    topics_by_name = {t["topic"]: t for t in body["topics"]}
    assert "red_cell_indices" in topics_by_name
    assert "parasitology" in topics_by_name
    assert topics_by_name["red_cell_indices"]["attempts_count"] == 1
    assert topics_by_name["red_cell_indices"]["mastery_score"] > 0

    assert body["overall_mastery"] > 0


async def test_scoring_me_is_scoped_to_the_requesting_student(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    owner_token = await _register_and_login(client, email="owner@laborax.dev")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    case_id = await _generate_case(client, owner_headers, "Malaria")
    await client.post(
        "/api/v1/interpretations",
        headers=owner_headers,
        json={"case_id": case_id, "free_text": "Hemoglobin is decreased."},
    )

    other_token = await _register_and_login(client, email="other@laborax.dev")
    response = await client.get(
        "/api/v1/scoring/me", headers={"Authorization": f"Bearer {other_token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["topics"] == []
    assert body["total_attempts"] == 0


async def test_repeated_submissions_increase_attempts_count_for_touched_topics(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    for _ in range(2):
        response = await client.post(
            "/api/v1/interpretations",
            headers=headers,
            json={"case_id": case_id, "free_text": "Hemoglobin is decreased."},
        )
        assert response.status_code == 201

    response = await client.get("/api/v1/scoring/me", headers=headers)
    body = response.json()
    topics_by_name = {t["topic"]: t for t in body["topics"]}
    assert topics_by_name["red_cell_indices"]["attempts_count"] == 2
    assert body["total_attempts"] == 2

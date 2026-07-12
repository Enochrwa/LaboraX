"""Integration tests for the interpretation submission (`/interpretations/*`)
routes — Sprint 4's core deliverable."""

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


async def test_submit_interpretation_requires_authentication(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    response = await client.post(
        "/api/v1/interpretations",
        json={"case_id": "00000000-0000-0000-0000-000000000000", "free_text": "Anything"},
    )
    assert response.status_code == 401


async def test_submit_interpretation_rejects_non_students(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client, role="lecturer", email="lecturer@laborax.dev")
    response = await client.post(
        "/api/v1/interpretations",
        headers={"Authorization": f"Bearer {token}"},
        json={"case_id": "00000000-0000-0000-0000-000000000000", "free_text": "Anything"},
    )
    assert response.status_code == 403


async def test_submit_interpretation_returns_404_for_unknown_case(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    response = await client.post(
        "/api/v1/interpretations",
        headers={"Authorization": f"Bearer {token}"},
        json={"case_id": "00000000-0000-0000-0000-000000000000", "free_text": "Anything"},
    )
    assert response.status_code == 404


async def test_student_cannot_submit_interpretation_for_another_students_case(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    owner_token = await _register_and_login(client, email="owner@laborax.dev")
    case_id = await _generate_case(client, {"Authorization": f"Bearer {owner_token}"}, "Malaria")

    other_token = await _register_and_login(client, email="other@laborax.dev")
    response = await client.post(
        "/api/v1/interpretations",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"case_id": case_id, "free_text": "Anything"},
    )
    assert response.status_code == 403


async def test_submit_interpretation_rejects_blank_text(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    response = await client.post(
        "/api/v1/interpretations",
        headers=headers,
        json={"case_id": case_id, "free_text": ""},
    )
    assert response.status_code == 422


async def test_submit_strong_interpretation_scores_highly_and_persists(
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
    response = await client.post(
        "/api/v1/interpretations",
        headers=headers,
        json={"case_id": case_id, "free_text": free_text},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["score"] >= 60.0
    assert body["case_id"] == case_id
    assert len(body["confirmed_findings"]) == 5
    assert body["incorrect_findings"] == []
    assert body["tutor_feedback"]

    history = await client.get(f"/api/v1/interpretations/{case_id}", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["id"] == body["id"]


async def test_submit_contradictory_interpretation_is_penalized(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    response = await client.post(
        "/api/v1/interpretations",
        headers=headers,
        json={
            "case_id": case_id,
            "free_text": "Hemoglobin is normal. Platelets are increased.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["incorrect_findings"]) == 1
    assert body["score"] < 50.0


async def test_resubmitting_creates_a_new_history_entry(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    first = await client.post(
        "/api/v1/interpretations",
        headers=headers,
        json={"case_id": case_id, "free_text": "Hemoglobin is decreased."},
    )
    second = await client.post(
        "/api/v1/interpretations",
        headers=headers,
        json={"case_id": case_id, "free_text": "Hemoglobin is decreased and platelets are low."},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]

    history = await client.get(f"/api/v1/interpretations/{case_id}", headers=headers)
    assert len(history.json()) == 2
    # Newest first.
    assert history.json()[0]["id"] == second.json()["id"]


async def test_interpretations_history_visible_to_lecturer_but_not_other_students(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    owner_token = await _register_and_login(client, email="owner2@laborax.dev")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    case_id = await _generate_case(client, owner_headers, "Malaria")
    await client.post(
        "/api/v1/interpretations",
        headers=owner_headers,
        json={"case_id": case_id, "free_text": "Hemoglobin is decreased."},
    )

    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer3@laborax.dev"
    )
    lecturer_response = await client.get(
        f"/api/v1/interpretations/{case_id}",
        headers={"Authorization": f"Bearer {lecturer_token}"},
    )
    assert lecturer_response.status_code == 200

    other_student_token = await _register_and_login(client, email="other2@laborax.dev")
    other_response = await client.get(
        f"/api/v1/interpretations/{case_id}",
        headers={"Authorization": f"Bearer {other_student_token}"},
    )
    assert other_response.status_code == 403


async def test_interpretations_history_returns_404_for_unknown_case(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/interpretations/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404

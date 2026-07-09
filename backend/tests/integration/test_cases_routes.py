"""Integration tests for the case retrieval/generation routes."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.models.disease import Disease
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


async def test_next_case_requires_authentication(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    response = await client.get("/api/v1/cases/next")
    assert response.status_code == 401


async def test_next_case_rejects_non_students(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client, role="lecturer", email="lecturer@laborax.dev")
    response = await client.get("/api/v1/cases/next", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


async def test_next_case_returns_a_generated_case(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    response = await client.get("/api/v1/cases/next", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["patient_pseudo_id"].startswith("PT-")
    assert body["difficulty"] == "novice"
    assert body["disease"]["category"] == "hematology"
    assert "presenting_symptoms" in body["doctor_request"]
    # The raw answer key must never be exposed to the student.
    assert "lab_pattern_template" not in body["disease"]
    assert "symptom_template" not in body["disease"]


async def test_next_case_is_deterministic_given_a_seed(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.get(
        "/api/v1/cases/next",
        headers=headers,
        params={"disease_name": "Malaria", "difficulty": "novice", "seed": 555},
    )
    second = await client.get(
        "/api/v1/cases/next",
        headers=headers,
        params={"disease_name": "Malaria", "difficulty": "novice", "seed": 555},
    )

    assert first.status_code == second.status_code == 200
    first_body, second_body = first.json(), second.json()
    assert first_body["patient_pseudo_id"] == second_body["patient_pseudo_id"]
    assert first_body["age"] == second_body["age"]
    assert first_body["doctor_request"] == second_body["doctor_request"]
    # Distinct persisted rows even though the generated content is identical.
    assert first_body["id"] != second_body["id"]


async def test_next_case_honors_category_filter(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/cases/next",
        headers={"Authorization": f"Bearer {token}"},
        params={"category": "hematology"},
    )
    assert response.status_code == 200
    assert response.json()["disease"]["category"] == "hematology"


async def test_next_case_returns_404_for_unknown_category(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/cases/next",
        headers={"Authorization": f"Bearer {token}"},
        params={"category": "histopathology"},
    )
    assert response.status_code == 404


async def test_next_case_returns_422_for_unknown_difficulty(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/cases/next",
        headers={"Authorization": f"Bearer {token}"},
        params={"difficulty": "impossible"},
    )
    assert response.status_code == 422


async def test_next_case_returns_422_for_unknown_disease_name(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/cases/next",
        headers={"Authorization": f"Bearer {token}"},
        params={"disease_name": "Scurvy"},
    )
    assert response.status_code == 422


async def test_get_case_by_id_returns_the_persisted_case(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.get("/api/v1/cases/next", headers=headers)
    case_id = created.json()["id"]

    response = await client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == case_id


async def test_get_case_by_id_is_visible_to_lecturers(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    student_token = await _register_and_login(client)
    created = await client.get(
        "/api/v1/cases/next", headers={"Authorization": f"Bearer {student_token}"}
    )
    case_id = created.json()["id"]

    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer2@laborax.dev"
    )
    response = await client.get(
        f"/api/v1/cases/{case_id}", headers={"Authorization": f"Bearer {lecturer_token}"}
    )
    assert response.status_code == 200


async def test_get_case_returns_404_for_unknown_id(
    client: AsyncClient, seeded_diseases: list[Disease]
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404

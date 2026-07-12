"""Integration tests for `POST /api/v1/lecturer/cases/assign`,
`GET /api/v1/lecturer/assignments`, and
`GET /api/v1/lecturer/analytics/{group_id}` — Sprint 6.

Also covers the corresponding `interpretations.py` ownership-check change
(a `LECTURER`-generated/assigned case is attemptable by any student, but a
student can only ever see their own submissions for it)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.db.models.disease import Disease
from app.db.models.test_catalog import TestCatalog
from tests.conftest import fixture_credential

pytestmark = pytest.mark.anyio


async def _register_and_login(
    client: AsyncClient, *, role: str = "student", email: str = "user@laborax.dev"
) -> str:
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


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_assign_case_requires_lecturer_role(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    student_token = await _register_and_login(client, email="student@laborax.dev")
    response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(student_token),
        json={"disease_name": "Malaria", "assigned_to_group": "BLS-Y3-A"},
    )
    assert response.status_code == 403


async def test_assign_case_rejects_both_case_id_and_disease_name(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer1@laborax.dev"
    )
    response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={
            "case_id": "00000000-0000-0000-0000-000000000000",
            "disease_name": "Malaria",
            "assigned_to_group": "BLS-Y3-A",
        },
    )
    assert response.status_code == 422


async def test_assign_case_rejects_neither_case_id_nor_disease_name(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer1@laborax.dev"
    )
    response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={"assigned_to_group": "BLS-Y3-A"},
    )
    assert response.status_code == 422


async def test_assign_case_generates_a_lecturer_owned_case(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer2@laborax.dev"
    )
    response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={
            "disease_name": "Malaria",
            "difficulty": "novice",
            "seed": 42,
            "assigned_to_group": "BLS-Y3-A",
            "due_at": "2026-08-01T00:00:00Z",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["assigned_to_group"] == "BLS-Y3-A"
    assert body["case"]["generated_by"] == "lecturer"
    assert body["case"]["disease"]["name"] == "Malaria"
    assert body["case"]["seed"] == 42


async def test_assign_case_by_existing_case_id_must_be_lecturer_owned(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    student_token = await _register_and_login(client, email="student2@laborax.dev")
    case_response = await client.get(
        "/api/v1/cases/next",
        headers=_auth(student_token),
        params={"disease_name": "Malaria"},
    )
    student_case_id = case_response.json()["id"]

    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer3@laborax.dev"
    )
    response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={"case_id": student_case_id, "assigned_to_group": "BLS-Y3-A"},
    )
    assert response.status_code == 422


async def test_assign_case_returns_422_for_unknown_disease_name(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer7@laborax.dev"
    )
    response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={"disease_name": "Not A Real Disease", "assigned_to_group": "BLS-Y3-A"},
    )
    assert response.status_code == 422


async def test_assign_case_returns_404_for_unknown_case_id(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer8@laborax.dev"
    )
    response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={
            "case_id": "11111111-1111-1111-1111-111111111111",
            "assigned_to_group": "BLS-Y3-A",
        },
    )
    assert response.status_code == 404


async def test_any_student_can_submit_an_interpretation_for_an_assigned_case(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer4@laborax.dev"
    )
    assign_response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={
            "disease_name": "Malaria",
            "seed": 7,
            "assigned_to_group": "BLS-Y3-B",
        },
    )
    case_id = assign_response.json()["case"]["id"]

    alice_token = await _register_and_login(client, email="alice@laborax.dev")
    bob_token = await _register_and_login(client, email="bob@laborax.dev")

    for token in (alice_token, bob_token):
        submit_response = await client.post(
            "/api/v1/interpretations",
            headers=_auth(token),
            json={"case_id": case_id, "free_text": "Hemoglobin is decreased."},
        )
        assert submit_response.status_code == 201

    # Each student only ever sees their own submissions for the shared case.
    alice_view = await client.get(f"/api/v1/interpretations/{case_id}", headers=_auth(alice_token))
    assert alice_view.status_code == 200
    assert len(alice_view.json()) == 1

    # The lecturer sees every submission.
    lecturer_view = await client.get(
        f"/api/v1/interpretations/{case_id}", headers=_auth(lecturer_token)
    )
    assert lecturer_view.status_code == 200
    assert len(lecturer_view.json()) == 2


async def test_list_my_assignments_is_scoped_to_the_requesting_lecturer(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_a = await _register_and_login(client, role="lecturer", email="lecturera@laborax.dev")
    lecturer_b = await _register_and_login(client, role="lecturer", email="lecturerb@laborax.dev")

    await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_a),
        json={"disease_name": "Malaria", "assigned_to_group": "GROUP-A"},
    )

    response = await client.get("/api/v1/lecturer/assignments", headers=_auth(lecturer_b))
    assert response.status_code == 200
    assert response.json() == []

    response = await client.get("/api/v1/lecturer/assignments", headers=_auth(lecturer_a))
    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_analytics_returns_404_for_unknown_group(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer5@laborax.dev"
    )
    response = await client.get(
        "/api/v1/lecturer/analytics/no-such-group", headers=_auth(lecturer_token)
    )
    assert response.status_code == 404


async def test_analytics_is_scoped_to_the_requesting_lecturers_own_assignments(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_a = await _register_and_login(client, role="lecturer", email="lecturerc@laborax.dev")
    lecturer_b = await _register_and_login(client, role="lecturer", email="lecturerd@laborax.dev")

    await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_a),
        json={"disease_name": "Malaria", "assigned_to_group": "SHARED-LABEL"},
    )

    response = await client.get(
        "/api/v1/lecturer/analytics/SHARED-LABEL", headers=_auth(lecturer_b)
    )
    assert response.status_code == 404


async def test_analytics_aggregates_cohort_performance(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer6@laborax.dev"
    )
    assign_response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=_auth(lecturer_token),
        json={"disease_name": "Malaria", "seed": 99, "assigned_to_group": "BLS-Y3-C"},
    )
    case_id = assign_response.json()["case"]["id"]

    alice_token = await _register_and_login(client, email="alice2@laborax.dev")
    bob_token = await _register_and_login(client, email="bob2@laborax.dev")

    await client.post(
        "/api/v1/interpretations",
        headers=_auth(alice_token),
        json={"case_id": case_id, "free_text": "Hemoglobin is decreased."},
    )
    await client.post(
        "/api/v1/interpretations",
        headers=_auth(bob_token),
        json={"case_id": case_id, "free_text": "Everything looks completely normal."},
    )

    response = await client.get(
        "/api/v1/lecturer/analytics/BLS-Y3-C", headers=_auth(lecturer_token)
    )
    assert response.status_code == 200
    body = response.json()

    assert body["group_id"] == "BLS-Y3-C"
    assert body["assignment_count"] == 1
    assert body["case_count"] == 1
    assert body["distinct_students"] == 2
    assert body["total_attempts"] == 2
    assert len(body["cases"]) == 1
    assert body["cases"][0]["disease_name"] == "Malaria"
    assert body["cases"][0]["attempts_count"] == 2
    assert body["cases"][0]["distinct_students"] == 2
    assert len(body["assignments"]) == 1
    # Bob's submission missed findings entirely -> should surface as commonly missed.
    assert len(body["commonly_missed_findings"]) > 0
    assert len(body["topics"]) > 0


async def test_analytics_requires_lecturer_role(
    client: AsyncClient, seeded_diseases: list[Disease], seeded_test_catalog: list[TestCatalog]
) -> None:
    student_token = await _register_and_login(client, email="student3@laborax.dev")
    response = await client.get("/api/v1/lecturer/analytics/anything", headers=_auth(student_token))
    assert response.status_code == 403

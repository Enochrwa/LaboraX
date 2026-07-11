"""Integration tests for the test-ordering (`/tests/*`) and result
retrieval (`/results/*`) routes — Sprint 3's core deliverable."""

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


async def test_get_test_catalog_requires_authentication(
    client: AsyncClient, seeded_test_catalog: list[TestCatalog]
) -> None:
    response = await client.get("/api/v1/tests/catalog")
    assert response.status_code == 401


async def test_get_test_catalog_lists_every_seeded_test(
    client: AsyncClient, seeded_test_catalog: list[TestCatalog]
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/tests/catalog", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    codes = {entry["code"] for entry in body}
    assert codes == {"CBC", "PBF", "RETIC", "FERRITIN", "CRP", "LFT", "URINALYSIS"}
    # Relevance rules are an internal answer-key-adjacent detail.
    assert "relevance_rules" not in body[0]


async def test_order_tests_requires_authentication(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    response = await client.post(
        "/api/v1/tests/order",
        json={"case_id": "00000000-0000-0000-0000-000000000000", "test_codes": ["CBC"]},
    )
    assert response.status_code == 401


async def test_order_tests_rejects_non_students(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client, role="lecturer", email="lecturer@laborax.dev")
    response = await client.post(
        "/api/v1/tests/order",
        headers={"Authorization": f"Bearer {token}"},
        json={"case_id": "00000000-0000-0000-0000-000000000000", "test_codes": ["CBC"]},
    )
    assert response.status_code == 403


async def test_order_tests_returns_422_for_unknown_test_code(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    response = await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["NOT_A_REAL_TEST"]},
    )
    assert response.status_code == 422


async def test_order_tests_returns_404_for_unknown_case(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    response = await client.post(
        "/api/v1/tests/order",
        headers={"Authorization": f"Bearer {token}"},
        json={"case_id": "00000000-0000-0000-0000-000000000000", "test_codes": ["CBC"]},
    )
    assert response.status_code == 404


async def test_student_cannot_order_tests_for_another_students_case(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    owner_token = await _register_and_login(client, email="owner@laborax.dev")
    case_id = await _generate_case(client, {"Authorization": f"Bearer {owner_token}"}, "Malaria")

    other_token = await _register_and_login(client, email="other@laborax.dev")
    response = await client.post(
        "/api/v1/tests/order",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"case_id": case_id, "test_codes": ["CBC"]},
    )
    assert response.status_code == 403


async def test_ordering_core_cbc_is_always_appropriate_and_free(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    response = await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["CBC"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_penalty"] == 0.0
    order = body["orders"][0]
    assert order["test"]["code"] == "CBC"
    assert order["is_appropriate"] is True
    assert order["penalty_applied"] == 0.0


async def test_ordering_reticulocyte_for_malaria_is_appropriate(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    response = await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["RETIC"]},
    )

    assert response.status_code == 200
    order = response.json()["orders"][0]
    assert order["is_appropriate"] is True
    assert order["penalty_applied"] == 0.0


async def test_ordering_liver_function_test_for_malaria_incurs_penalty(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    response = await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["LFT"]},
    )

    assert response.status_code == 200
    body = response.json()
    order = body["orders"][0]
    assert order["is_appropriate"] is False
    assert order["penalty_applied"] == 2.0
    assert body["total_penalty"] == 2.0


async def test_ordering_the_same_test_twice_is_idempotent(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    first = await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["CBC"]},
    )
    second = await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["CBC"]},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["orders"][0]["id"] == second.json()["orders"][0]["id"]

    results = await client.get(f"/api/v1/results/{case_id}", headers=headers)
    assert len(results.json()["results"]) == 1


async def test_ordering_multiple_tests_in_one_batch(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    response = await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["CBC", "PBF", "LFT"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["orders"]) == 3
    assert body["total_penalty"] == 2.0  # only LFT is inappropriate


async def test_results_reflect_only_ordered_tests(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    case_id = await _generate_case(client, headers, "Malaria")

    # Before ordering anything, results should be empty.
    empty = await client.get(f"/api/v1/results/{case_id}", headers=headers)
    assert empty.status_code == 200
    assert empty.json()["results"] == []

    await client.post(
        "/api/v1/tests/order",
        headers=headers,
        json={"case_id": case_id, "test_codes": ["CBC", "PBF"]},
    )

    response = await client.get(f"/api/v1/results/{case_id}", headers=headers)
    assert response.status_code == 200
    body = response.json()
    codes = {result["test"]["code"] for result in body["results"]}
    assert codes == {"CBC", "PBF"}

    cbc_result = next(r for r in body["results"] if r["test"]["code"] == "CBC")
    assert "hemoglobin_g_dl" in cbc_result["result_payload"]["values"]

    pbf_result = next(r for r in body["results"] if r["test"]["code"] == "PBF")
    assert pbf_result["result_payload"]["flag"] == "abnormal"
    assert len(pbf_result["result_payload"]["findings"]) > 0


async def test_results_are_visible_to_lecturers_but_not_other_students(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    owner_token = await _register_and_login(client, email="owner2@laborax.dev")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    case_id = await _generate_case(client, owner_headers, "Malaria")
    await client.post(
        "/api/v1/tests/order",
        headers=owner_headers,
        json={"case_id": case_id, "test_codes": ["CBC"]},
    )

    lecturer_token = await _register_and_login(
        client, role="lecturer", email="lecturer3@laborax.dev"
    )
    lecturer_response = await client.get(
        f"/api/v1/results/{case_id}", headers={"Authorization": f"Bearer {lecturer_token}"}
    )
    assert lecturer_response.status_code == 200

    other_student_token = await _register_and_login(client, email="other2@laborax.dev")
    other_response = await client.get(
        f"/api/v1/results/{case_id}",
        headers={"Authorization": f"Bearer {other_student_token}"},
    )
    assert other_response.status_code == 403


async def test_results_returns_404_for_unknown_case(
    client: AsyncClient,
    seeded_diseases: list[Disease],
    seeded_test_catalog: list[TestCatalog],
) -> None:
    token = await _register_and_login(client)
    response = await client.get(
        "/api/v1/results/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404

"""Sprint 6 "load smoke test" — a fast, dependency-light sanity check against
a *running* LaboraX instance (`docs/SPRINT_PLAN.md` Sprint 6: "Full
regression pass: ... load smoke test").

This is deliberately not a full load-testing harness (no Locust/k6): the
free-tier infra this project targets (`docs/HLD.md`) can't meaningfully
absorb sustained load testing anyway, and pytest's ~150 functional tests
already cover correctness. What this script checks instead is the thing
functional tests can't: that the whole request path — auth, case
generation, interpretation scoring, mastery tracking, and the new Sprint 6
lecturer-assignment/analytics endpoints — holds up under a small burst of
*concurrent* traffic without errors or runaway latency, against a real
running server (not the in-process ASGI transport `tests/conftest.py`
uses).

Usage:
    python scripts/load_smoke_test.py [--base-url http://localhost:8000] [--concurrency 10]

Exits non-zero if any request fails or the server is unreachable.
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
import uuid
from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class SmokeResult:
    label: str
    durations_s: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        if not self.durations_s:
            return f"{self.label}: no successful requests"
        p50 = statistics.median(self.durations_s)
        p95 = sorted(self.durations_s)[max(0, int(len(self.durations_s) * 0.95) - 1)]
        return (
            f"{self.label}: {len(self.durations_s)} ok, {len(self.errors)} failed, "
            f"p50={p50 * 1000:.0f}ms p95={p95 * 1000:.0f}ms"
        )


async def _timed(result: SmokeResult, coro: Coroutine[Any, Any, httpx.Response]) -> None:
    start = time.monotonic()
    try:
        response = await coro
        response.raise_for_status()
    except Exception as exc:
        result.errors.append(str(exc))
    else:
        result.durations_s.append(time.monotonic() - start)


async def _student_journey(client: httpx.AsyncClient, result: SmokeResult, index: int) -> None:
    email = f"smoke-student-{uuid.uuid4().hex[:10]}-{index}@laborax.dev"
    password = "SmokeTest!2026"

    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Smoke Student",
            "password": password,
            "role": "student",
        },
    )
    if register.status_code != 201:
        result.errors.append(f"register failed: {register.status_code} {register.text}")
        return

    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if login.status_code != 200:
        result.errors.append(f"login failed: {login.status_code} {login.text}")
        return
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    start = time.monotonic()
    case_response = await client.get(
        "/api/v1/cases/next", headers=headers, params={"disease_name": "Malaria"}
    )
    if case_response.status_code != 200:
        result.errors.append(f"case generation failed: {case_response.status_code}")
        return
    result.durations_s.append(time.monotonic() - start)
    case_id = case_response.json()["id"]

    start = time.monotonic()
    interpretation_response = await client.post(
        "/api/v1/interpretations",
        headers=headers,
        json={
            "case_id": case_id,
            "free_text": "Hemoglobin is decreased, consistent with anemia.",
        },
    )
    if interpretation_response.status_code != 201:
        result.errors.append(f"interpretation failed: {interpretation_response.status_code}")
        return
    result.durations_s.append(time.monotonic() - start)

    start = time.monotonic()
    scoring_response = await client.get("/api/v1/scoring/me", headers=headers)
    if scoring_response.status_code != 200:
        result.errors.append(f"scoring failed: {scoring_response.status_code}")
        return
    result.durations_s.append(time.monotonic() - start)


async def _lecturer_journey(client: httpx.AsyncClient, result: SmokeResult, index: int) -> None:
    email = f"smoke-lecturer-{uuid.uuid4().hex[:10]}-{index}@laborax.dev"
    password = "SmokeTest!2026"
    group = f"SMOKE-{uuid.uuid4().hex[:6]}"

    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Smoke Lecturer",
            "password": password,
            "role": "lecturer",
        },
    )
    if register.status_code != 201:
        result.errors.append(f"register failed: {register.status_code} {register.text}")
        return

    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if login.status_code != 200:
        result.errors.append(f"login failed: {login.status_code} {login.text}")
        return
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    start = time.monotonic()
    assign_response = await client.post(
        "/api/v1/lecturer/cases/assign",
        headers=headers,
        json={"disease_name": "Malaria", "assigned_to_group": group},
    )
    if assign_response.status_code != 201:
        result.errors.append(f"assign failed: {assign_response.status_code} {assign_response.text}")
        return
    result.durations_s.append(time.monotonic() - start)

    start = time.monotonic()
    analytics_response = await client.get(f"/api/v1/lecturer/analytics/{group}", headers=headers)
    if analytics_response.status_code != 200:
        result.errors.append(f"analytics failed: {analytics_response.status_code}")
        return
    result.durations_s.append(time.monotonic() - start)


async def run(base_url: str, concurrency: int) -> bool:
    health_result = SmokeResult(label="health check")
    student_result = SmokeResult(label="student journey (case -> interpretation -> scoring)")
    lecturer_result = SmokeResult(label="lecturer journey (assign -> analytics)")

    async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
        await _timed(health_result, client.get("/health"))
        if not health_result.ok:
            print(f"Server unreachable at {base_url}: {health_result.errors[0]}")
            return False

        await asyncio.gather(
            *(_student_journey(client, student_result, i) for i in range(concurrency)),
            *(
                _lecturer_journey(client, lecturer_result, i)
                for i in range(max(1, concurrency // 2))
            ),
        )

    for result in (health_result, student_result, lecturer_result):
        print(result.summary())

    return health_result.ok and student_result.ok and lecturer_result.ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    ok = asyncio.run(run(args.base_url, args.concurrency))
    if not ok:
        print("Load smoke test FAILED.")
        return 1
    print("Load smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

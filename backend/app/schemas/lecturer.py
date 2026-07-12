"""Pydantic request/response schemas for the Sprint 6 lecturer routes.

`POST /api/v1/lecturer/cases/assign` and
`GET /api/v1/lecturer/analytics/{group_id}` — see
`app/api/v1/routes/lecturer.py` for the full design rationale.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.db.models.case import DifficultyLevel
from app.schemas.case import CaseRead


class CaseAssignmentCreate(BaseModel):
    """Request body for `POST /api/v1/lecturer/cases/assign`.

    Either `case_id` (assign an already-generated, lecturer-owned case) or
    `disease_name` (generate a brand-new lecturer case on the fly, then
    assign it in the same call) must be supplied. Exactly one of the two
    keeps the request unambiguous rather than silently preferring one.
    """

    case_id: uuid.UUID | None = Field(
        default=None,
        description="Assign an existing lecturer-generated case. Mutually exclusive with disease_name.",
    )
    disease_name: str | None = Field(
        default=None, description="Generate a new case for this disease and assign it."
    )
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.NOVICE)
    seed: int | None = Field(
        default=None,
        description="Deterministic seed so every student in the group receives an identical case.",
    )
    assigned_to_group: str = Field(min_length=1, max_length=128)
    due_at: datetime | None = Field(default=None)

    @model_validator(mode="after")
    def _exactly_one_case_source(self) -> CaseAssignmentCreate:
        if (self.case_id is None) == (self.disease_name is None):
            raise ValueError("Provide exactly one of case_id or disease_name.")
        return self


class CaseAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lecturer_id: uuid.UUID
    assigned_to_group: str
    due_at: datetime | None
    created_at: datetime
    case: CaseRead


class CohortCaseBreakdown(BaseModel):
    case_id: uuid.UUID
    disease_name: str
    difficulty: DifficultyLevel
    due_at: datetime | None
    attempts_count: int
    distinct_students: int
    average_score: float


class CohortTopicBreakdown(BaseModel):
    topic: str
    average_mastery: float
    students_count: int


class CommonlyMissedFinding(BaseModel):
    finding: str
    miss_count: int


class CohortAnalytics(BaseModel):
    """Response body for `GET /api/v1/lecturer/analytics/{group_id}`."""

    group_id: str
    assignment_count: int
    case_count: int
    distinct_students: int
    total_attempts: int
    overall_average_score: float
    cases: list[CohortCaseBreakdown]
    topics: list[CohortTopicBreakdown]
    commonly_missed_findings: list[CommonlyMissedFinding]
    assignments: list[CaseAssignmentRead]

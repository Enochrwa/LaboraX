"""Pydantic request/response schemas for virtual patient cases."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.case import CaseGeneratedBy, DifficultyLevel, PatientSex
from app.schemas.disease import DiseaseSummary


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_pseudo_id: str
    age: int
    sex: PatientSex
    clinical_history: str
    doctor_request: dict[str, Any]
    difficulty: DifficultyLevel
    seed: int
    generated_by: CaseGeneratedBy
    created_at: datetime
    disease: DiseaseSummary


class NextCaseParams(BaseModel):
    """Query parameters accepted by `GET /api/v1/cases/next`."""

    category: str | None = Field(default=None, description="Filter by disease category.")
    disease_name: str | None = Field(
        default=None, description="Request a specific disease by name."
    )
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.NOVICE)
    seed: int | None = Field(
        default=None,
        description="Deterministic seed. Omit for a random case; lecturers supply this for exams.",
    )

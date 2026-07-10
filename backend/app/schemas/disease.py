"""Pydantic response schemas for disease templates."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.db.models.disease import DiseaseCategory


class DiseaseSummary(BaseModel):
    """Deliberately excludes `symptom_template`/`lab_pattern_template`.

    Students must not receive the raw answer key alongside the case — those
    fields are for internal use by `CaseGenerator` and, later, `AnswerEvaluator`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: DiseaseCategory

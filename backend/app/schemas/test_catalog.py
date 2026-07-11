"""Pydantic response schemas for the orderable test catalog.

Deliberately excludes `relevance_rules` — students must not see which
parameters a test measures or how appropriateness is computed, the same
principle `DiseaseSummary` already applies to disease templates.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.db.models.disease import DiseaseCategory


class TestCatalogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    category: DiseaseCategory
    cost_weight: float

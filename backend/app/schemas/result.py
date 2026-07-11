"""Pydantic response schemas for generated lab results."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.test_catalog import TestCatalogRead


class ResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test: TestCatalogRead
    result_payload: dict[str, Any]
    generated_at: datetime


class CaseResultsRead(BaseModel):
    """Response for `GET /api/v1/results/{case_id}`.

    Only reflects tests the student has actually ordered — results for
    un-ordered tests are never generated eagerly, per `docs/PRD.md` §5.2's
    cost-stewardship principle.
    """

    case_id: uuid.UUID
    total_penalty: float
    results: list[ResultRead]

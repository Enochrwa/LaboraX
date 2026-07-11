"""Pydantic request/response schemas for test ordering."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.test_catalog import TestCatalogRead


class TestOrderRequest(BaseModel):
    """Body for `POST /api/v1/tests/order`.

    Accepts one or more test codes so the frontend's test-selection
    checklist can submit a whole panel in a single call.
    """

    case_id: uuid.UUID
    test_codes: list[str] = Field(min_length=1)


class TestOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    test: TestCatalogRead
    is_appropriate: bool
    penalty_applied: float
    ordered_at: datetime


class TestOrderBatchRead(BaseModel):
    """Response for `POST /api/v1/tests/order` — every order in the batch
    (including tests that were already ordered previously, returned
    idempotently) plus the total simulated cost penalty accrued so far."""

    orders: list[TestOrderRead]
    total_penalty: float

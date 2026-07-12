"""Pydantic response schemas for `GET /api/v1/scoring/me` (Sprint 5)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TopicMasteryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic: str
    mastery_score: float
    attempts_count: int
    updated_at: datetime


class RecentAttemptSummary(BaseModel):
    """A lightweight per-attempt entry for the personal progress view.

    Deliberately a slimmer projection than `InterpretationResultRead`
    (`app/schemas/interpretation.py`) — the progress view wants a trend
    line, not the full finding-by-finding breakdown, which is still
    available via `GET /api/v1/interpretations/{case_id}`.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    score: float
    evaluated_at: datetime


class ScoringSummary(BaseModel):
    """Response body for `GET /api/v1/scoring/me`."""

    topics: list[TopicMasteryRead]
    overall_mastery: float
    total_attempts: int
    recent_attempts: list[RecentAttemptSummary]

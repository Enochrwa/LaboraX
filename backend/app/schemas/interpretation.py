"""Pydantic request/response schemas for interpretation evaluation."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterpretationRequest(BaseModel):
    """Body for `POST /api/v1/interpretations`."""

    case_id: uuid.UUID
    free_text: str = Field(min_length=1, max_length=5000)


class FindingMatch(BaseModel):
    """One expected finding and how well the student's text matched it.

    `topic` and `explanation` are Sprint 5 additions — the learning topic
    this finding belongs to (`student_topic_mastery`'s grouping) and the
    rule-based "why this matters" text from
    `app.services.tutor.explanations`.
    """

    expected_finding: str
    matched_statement: str | None = None
    similarity: float
    topic: str
    explanation: str


class IncorrectStatement(BaseModel):
    """A statement in the student's text that contradicts a known case finding."""

    statement: str
    reason: str
    topic: str


class InterpretationResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    submitted_text: str
    score: float
    confirmed_findings: list[FindingMatch]
    missing_findings: list[FindingMatch]
    incorrect_findings: list[IncorrectStatement]
    tutor_feedback: str
    evaluated_at: datetime

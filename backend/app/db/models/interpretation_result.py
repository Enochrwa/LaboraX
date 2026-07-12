"""InterpretationResult model — a student's evaluated free-text interpretation.

Produced by `AnswerEvaluator` (see `app/services/answer_evaluator`) when a
student submits their reading of a case's results via
`POST /api/v1/interpretations`. One row per `(case, student)` submission
history entry — re-submitting for the same case creates a new row rather
than overwriting the previous attempt, so `student_topic_mastery` (Sprint 5)
can be updated from a full attempt history rather than only the latest one.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.case import Case


class InterpretationResult(Base):
    __tablename__ = "interpretation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitted_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confirmed_findings: Mapped[list[Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    missing_findings: Mapped[list[Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    incorrect_findings: Mapped[list[Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    tutor_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case: Mapped[Case] = relationship(Case, lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"InterpretationResult(id={self.id!r}, case_id={self.case_id!r}, score={self.score!r})"
        )

"""StudentTopicMastery model — a student's running mastery signal per topic.

Sprint 5 (`docs/SPRINT_PLAN.md`): "student_topic_mastery table + update
logic". One row per `(student, topic)` — unlike `InterpretationResult`
(one row per submission), this table holds a single running value that
`MasteryTracker` (see `app/services/mastery/tracker.py`) blends into after
every evaluated interpretation, so `GET /api/v1/scoring/me` can answer
"how am I doing on X" in O(topics) rather than replaying full submission
history on every request.

`topic` values come from `app.services.tutor.explanations.TOPIC_BY_PARAMETER`
(plus `DEFAULT_TOPIC`) — a small, evolving vocabulary, so it's stored as a
plain indexed string rather than a native DB enum. A native enum would need
a migration every time Sprint 7+ (Clinical Chemistry) or beyond adds a new
topic; a string does not.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudentTopicMastery(Base):
    __tablename__ = "student_topic_mastery"
    __table_args__ = (
        UniqueConstraint("student_id", "topic", name="uq_student_topic_mastery_student_topic"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"StudentTopicMastery(student_id={self.student_id!r}, topic={self.topic!r}, "
            f"mastery_score={self.mastery_score!r})"
        )

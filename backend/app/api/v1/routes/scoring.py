"""Student progress/mastery routes — Sprint 5's `GET /api/v1/scoring/me`.

Read-only: this route never mutates `student_topic_mastery` itself — that
happens as a side effect of `POST /api/v1/interpretations` via
`MasteryTracker` (see `app/services/mastery/tracker.py`). This route only
projects the current state for the requesting student's own personal
progress view (`docs/LLD.md` §7 restricts this to `student` — a lecturer's
equivalent cohort view is Sprint 6's `GET /lecturer/analytics/{group_id}`).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DbSession, require_roles
from app.db.models.interpretation_result import InterpretationResult
from app.db.models.student_topic_mastery import StudentTopicMastery
from app.db.models.user import UserRole
from app.schemas.scoring import RecentAttemptSummary, ScoringSummary, TopicMasteryRead

router = APIRouter(prefix="/scoring", tags=["scoring"])

_RECENT_ATTEMPTS_LIMIT = 10


@router.get(
    "/me",
    response_model=ScoringSummary,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def get_my_scoring_summary(db: DbSession, current_user: CurrentUser) -> ScoringSummary:
    """The requesting student's own topic mastery + recent submission history."""
    topics_result = await db.execute(
        select(StudentTopicMastery)
        .where(StudentTopicMastery.student_id == current_user.id)
        .order_by(StudentTopicMastery.topic)
    )
    topics = list(topics_result.scalars().all())

    total_attempts_result = await db.execute(
        select(func.count())
        .select_from(InterpretationResult)
        .where(InterpretationResult.student_id == current_user.id)
    )
    total_attempts = int(total_attempts_result.scalar_one())

    recent_result = await db.execute(
        select(InterpretationResult)
        .where(InterpretationResult.student_id == current_user.id)
        .order_by(InterpretationResult.evaluated_at.desc())
        .limit(_RECENT_ATTEMPTS_LIMIT)
    )
    recent_attempts = list(recent_result.scalars().all())

    weighted_total = sum(t.mastery_score * t.attempts_count for t in topics)
    weight_sum = sum(t.attempts_count for t in topics)
    overall_mastery = round(weighted_total / weight_sum, 1) if weight_sum else 0.0

    return ScoringSummary(
        topics=[TopicMasteryRead.model_validate(t) for t in topics],
        overall_mastery=overall_mastery,
        total_attempts=total_attempts,
        recent_attempts=[RecentAttemptSummary.model_validate(a) for a in recent_attempts],
    )

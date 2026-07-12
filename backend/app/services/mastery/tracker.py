"""`MasteryTracker` — updates `student_topic_mastery` from an evaluated interpretation.

`docs/LLD.md` §2 step 5 sketches this as "`student_topic_mastery` updated
(async, via ARQ task if computation is non-trivial)". The computation here
is a handful of dict lookups plus one upsert-shaped query per touched
topic — not non-trivial — so, matching the same reasoning already applied
to `AnswerEvaluator` in Sprint 4 (spaCy/sentence-transformers -> local
TF-IDF), Sprint 5 runs it synchronously inside the request instead of
standing up the ARQ worker/Redis queue infra a full async pipeline would
need. `app/workers/` remains an empty scaffold; this can move onto it later
without changing `AnswerEvaluator`'s or this tracker's public interface.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.student_topic_mastery import StudentTopicMastery
from app.services.answer_evaluator.evaluator import TopicScore

# Exponential-moving-average blend factor: how much a single new submission
# moves the running mastery score. Deliberately not 1.0 (which would just
# overwrite the previous value with the latest attempt) so mastery reflects
# a trend across attempts rather than being reset by one lucky/unlucky
# submission — mirrors spaced-repetition-style weighting `docs/LLD.md` §4's
# `Recommender` interface already expects `student_topic_mastery` to feed.
_BLEND_ALPHA = 0.35


class MasteryTracker:
    """Stateless — safe to share a single instance across requests."""

    async def update_from_evaluation(
        self,
        db: AsyncSession,
        *,
        student_id: uuid.UUID,
        topic_scores: list[TopicScore],
    ) -> list[StudentTopicMastery]:
        """Blend each `TopicScore` from one evaluation into the running mastery row.

        Creates a new `StudentTopicMastery` row (starting at that
        submission's score) the first time a student touches a topic;
        otherwise blends via an exponential moving average. Rows the
        student hasn't touched in this submission are left untouched.
        """
        if not topic_scores:
            return []

        result = await db.execute(
            select(StudentTopicMastery).where(
                StudentTopicMastery.student_id == student_id,
                StudentTopicMastery.topic.in_([ts.topic for ts in topic_scores]),
            )
        )
        existing_by_topic = {row.topic: row for row in result.scalars().all()}

        updated: list[StudentTopicMastery] = []
        for topic_score in topic_scores:
            row = existing_by_topic.get(topic_score.topic)
            if row is None:
                row = StudentTopicMastery(
                    student_id=student_id,
                    topic=topic_score.topic,
                    mastery_score=topic_score.score,
                    attempts_count=1,
                )
                db.add(row)
            else:
                row.mastery_score = round(
                    (row.mastery_score * (1 - _BLEND_ALPHA)) + (topic_score.score * _BLEND_ALPHA),
                    1,
                )
                row.attempts_count += 1
            updated.append(row)

        await db.flush()
        for row in updated:
            await db.refresh(row)
        return updated

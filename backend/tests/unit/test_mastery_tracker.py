"""Unit tests for `MasteryTracker` — Sprint 5's `student_topic_mastery`
update logic.

Uses the real `db_session` fixture (real Postgres test DB, per
`tests/conftest.py`) rather than mocking SQLAlchemy, since the tracker's
entire job is to correctly upsert-shape a row per `(student, topic)`.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.student_topic_mastery import StudentTopicMastery
from app.db.models.user import User, UserRole
from app.services.answer_evaluator.evaluator import TopicScore
from app.services.mastery.tracker import MasteryTracker
from tests.conftest import fixture_credential

pytestmark = pytest.mark.anyio


async def _create_student(db: AsyncSession) -> User:
    user = User(
        email=f"{uuid.uuid4().hex}@laborax.dev",
        hashed_password=fixture_credential(),
        full_name="Test Student",
        role=UserRole.STUDENT,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
def tracker() -> MasteryTracker:
    return MasteryTracker()


class TestMasteryTracker:
    async def test_first_submission_creates_a_row_at_the_submission_score(
        self, db_session: AsyncSession, tracker: MasteryTracker
    ) -> None:
        student = await _create_student(db_session)

        rows = await tracker.update_from_evaluation(
            db_session,
            student_id=student.id,
            topic_scores=[TopicScore(topic="red_cell_indices", score=80.0, finding_count=2)],
        )

        assert len(rows) == 1
        assert rows[0].mastery_score == 80.0
        assert rows[0].attempts_count == 1

        persisted = (
            await db_session.execute(
                select(StudentTopicMastery).where(
                    StudentTopicMastery.student_id == student.id,
                    StudentTopicMastery.topic == "red_cell_indices",
                )
            )
        ).scalar_one()
        assert persisted.mastery_score == 80.0

    async def test_second_submission_blends_via_exponential_moving_average(
        self, db_session: AsyncSession, tracker: MasteryTracker
    ) -> None:
        student = await _create_student(db_session)

        await tracker.update_from_evaluation(
            db_session,
            student_id=student.id,
            topic_scores=[TopicScore(topic="parasitology", score=40.0, finding_count=1)],
        )
        rows = await tracker.update_from_evaluation(
            db_session,
            student_id=student.id,
            topic_scores=[TopicScore(topic="parasitology", score=100.0, finding_count=1)],
        )

        # alpha=0.35: 40 * 0.65 + 100 * 0.35 = 61.0
        assert rows[0].mastery_score == pytest.approx(61.0, abs=0.1)
        assert rows[0].attempts_count == 2

    async def test_topics_from_different_students_are_independent(
        self, db_session: AsyncSession, tracker: MasteryTracker
    ) -> None:
        alice = await _create_student(db_session)
        bob = await _create_student(db_session)

        await tracker.update_from_evaluation(
            db_session,
            student_id=alice.id,
            topic_scores=[TopicScore(topic="iron_studies", score=100.0, finding_count=1)],
        )
        await tracker.update_from_evaluation(
            db_session,
            student_id=bob.id,
            topic_scores=[TopicScore(topic="iron_studies", score=0.0, finding_count=1)],
        )

        alice_row = (
            await db_session.execute(
                select(StudentTopicMastery).where(StudentTopicMastery.student_id == alice.id)
            )
        ).scalar_one()
        bob_row = (
            await db_session.execute(
                select(StudentTopicMastery).where(StudentTopicMastery.student_id == bob.id)
            )
        ).scalar_one()

        assert alice_row.mastery_score == 100.0
        assert bob_row.mastery_score == 0.0

    async def test_untouched_topics_are_left_alone(
        self, db_session: AsyncSession, tracker: MasteryTracker
    ) -> None:
        student = await _create_student(db_session)

        await tracker.update_from_evaluation(
            db_session,
            student_id=student.id,
            topic_scores=[
                TopicScore(topic="red_cell_indices", score=90.0, finding_count=1),
                TopicScore(topic="platelet_count", score=10.0, finding_count=1),
            ],
        )
        await tracker.update_from_evaluation(
            db_session,
            student_id=student.id,
            topic_scores=[TopicScore(topic="red_cell_indices", score=95.0, finding_count=1)],
        )

        platelet_row = (
            await db_session.execute(
                select(StudentTopicMastery).where(
                    StudentTopicMastery.student_id == student.id,
                    StudentTopicMastery.topic == "platelet_count",
                )
            )
        ).scalar_one()
        assert platelet_row.mastery_score == 10.0
        assert platelet_row.attempts_count == 1

    async def test_empty_topic_scores_is_a_no_op(
        self, db_session: AsyncSession, tracker: MasteryTracker
    ) -> None:
        student = await _create_student(db_session)
        rows = await tracker.update_from_evaluation(
            db_session, student_id=student.id, topic_scores=[]
        )
        assert rows == []

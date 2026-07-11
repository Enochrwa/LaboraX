"""Interpretation submission + evaluation routes.

`POST /interpretations` is the core Sprint 4 deliverable: a student submits
free text describing what a case's results show, `AnswerEvaluator` scores it
against the case's disease `expected_findings`, and the scored result is
persisted so a submission history accumulates per case (kept as a thin
transport/persistence layer over the service, per `docs/HLD.md` §3.2 — same
shape as `app/api/v1/routes/tests.py`).
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, require_roles
from app.db.models.case import Case
from app.db.models.interpretation_result import InterpretationResult
from app.db.models.user import User, UserRole
from app.schemas.interpretation import InterpretationRequest, InterpretationResultRead
from app.services.answer_evaluator.evaluator import AnswerEvaluator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interpretations", tags=["interpretations"])

_evaluator = AnswerEvaluator()


async def _load_owned_case(db: DbSession, current_user: User, case_id: uuid.UUID) -> Case:
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    if case.requested_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to submit an interpretation for this case.",
        )
    return case


@router.post(
    "",
    response_model=InterpretationResultRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def submit_interpretation(
    payload: InterpretationRequest, db: DbSession, current_user: CurrentUser
) -> InterpretationResult:
    """Evaluate and persist a student's free-text interpretation of a case.

    Each submission is scored independently and stored as a new row —
    students may resubmit for the same case (e.g. after reviewing tutor
    feedback) and every attempt is kept for `student_topic_mastery` history
    (Sprint 5).
    """
    case = await _load_owned_case(db, current_user, payload.case_id)

    evaluation = _evaluator.evaluate(disease=case.disease, student_text=payload.free_text)

    interpretation = InterpretationResult(
        case_id=case.id,
        student_id=current_user.id,
        submitted_text=payload.free_text,
        score=evaluation.score,
        confirmed_findings=[vars(f) for f in evaluation.confirmed_findings],
        missing_findings=[vars(f) for f in evaluation.missing_findings],
        incorrect_findings=[vars(f) for f in evaluation.incorrect_findings],
        tutor_feedback=evaluation.tutor_feedback,
    )
    db.add(interpretation)
    await db.commit()
    await db.refresh(interpretation)

    logger.info(
        "interpretation_evaluated",
        extra={
            "case_id": str(case.id),
            "student_id": str(current_user.id),
            "score": evaluation.score,
        },
    )

    return interpretation


@router.get(
    "/{case_id}",
    response_model=list[InterpretationResultRead],
    dependencies=[
        Depends(require_roles(UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN)),
    ],
)
async def get_interpretations_for_case(
    case_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> list[InterpretationResult]:
    """List every interpretation attempt submitted for a case, newest first."""
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    if current_user.role == UserRole.STUDENT and case.requested_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view interpretations for this case.",
        )

    result = await db.execute(
        select(InterpretationResult)
        .where(InterpretationResult.case_id == case_id)
        .order_by(InterpretationResult.evaluated_at.desc())
    )
    return list(result.scalars().all())

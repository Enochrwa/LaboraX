"""Lecturer routes — Sprint 6's `case_assignments` + cohort analytics.

Matches `docs/LLD.md` §7:
    POST /api/v1/lecturer/cases/assign        assign case/exam to a group
    GET  /api/v1/lecturer/analytics/{group_id} cohort performance

**Making an assigned case attemptable by a whole group.** Before Sprint 6,
`Case.requested_by_id` is the single student who generated it, and
`interpretations.py`'s `_load_owned_case` only lets *that* student submit an
interpretation for it — correct for the Sprint 2-5 self-practice flow, but
it can't work for an assigned case a whole group needs to attempt. Rather
than bolt on a new membership/enrollment model the LLD's data model doesn't
define (`docs/LLD.md` §3 lists no `groups`/`enrollments` table), Sprint 6
reuses the `CaseGeneratedBy.LECTURER` enum value that has existed on `Case`
since Sprint 2 but was never set by any route: a lecturer-generated case has
no single owning student (`requested_by_id` stays `None`) and is therefore
open to interpretation by any authenticated student, the same way a printed
exam paper isn't "owned" by whichever student picks it up first.
`interpretations.py`'s ownership check is extended accordingly (see the
updated `_load_owned_case`). This keeps the change additive and scoped to
exactly the Sprint 6 need instead of introducing a general-purpose
class-roster feature.

**Who can assign a given case.** `POST /lecturer/cases/assign` accepts
either a brand-new `disease_name` (+ optional deterministic `seed`, per
`docs/LLD.md` §4's `CaseGenerator.generate` docstring: "Deterministic if
seed provided (lecturer-assigned exams)") which is generated as a
`LECTURER`-owned case in the same request, or an existing `case_id` that
must already be `LECTURER`-owned — an existing student's private practice
case can never be repurposed into a shared assignment.

**Who can see a group's analytics.** `GET /lecturer/analytics/{group_id}`
scopes strictly to assignments the *requesting* lecturer created
(`CaseAssignment.lecturer_id == current_user.id`). `assigned_to_group` is a
free-text label a lecturer chooses (e.g. a class code), not a table with its
own access-control list, so without this scoping any lecturer could read
any other lecturer's cohort by guessing/reusing a group label.

**How cohort performance is computed.** Rather than re-deriving per-topic
scores from raw `interpretation_results.missing_findings`/
`confirmed_findings` JSON, cohort topic performance reuses the
`student_topic_mastery` rows Sprint 5's `MasteryTracker` already maintains
for every student who submitted an interpretation on an assigned case — the
same "don't recompute a running signal that already exists" reasoning
`scoring.py` applies to `GET /api/v1/scoring/me`. "Commonly-missed findings"
(`docs/PRD.md` §5: "Identify commonly-missed findings across a cohort") is
the one signal genuinely only available in the raw `missing_findings` JSON,
so that field alone is scanned and tallied.
"""

from __future__ import annotations

import logging
import uuid
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, require_roles
from app.db.models.case import Case, CaseGeneratedBy
from app.db.models.case_assignment import CaseAssignment
from app.db.models.disease import Disease
from app.db.models.interpretation_result import InterpretationResult
from app.db.models.student_topic_mastery import StudentTopicMastery
from app.db.models.user import UserRole
from app.schemas.lecturer import (
    CaseAssignmentCreate,
    CaseAssignmentRead,
    CohortAnalytics,
    CohortCaseBreakdown,
    CohortTopicBreakdown,
    CommonlyMissedFinding,
)
from app.services.case_generator.generator import CaseGenerator, CaseGeneratorError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lecturer", tags=["lecturer"])

_TOP_MISSED_FINDINGS_LIMIT = 10


async def _resolve_case_for_assignment(
    db: DbSession, current_user: CurrentUser, payload: CaseAssignmentCreate
) -> Case:
    """Return the `LECTURER`-owned case to attach a new assignment to.

    Either generates one fresh from `payload.disease_name` or validates and
    reuses an existing `payload.case_id` — see this module's docstring.
    """
    if payload.disease_name is not None:
        result = await db.execute(select(Disease))
        diseases = list(result.scalars().all())
        if not diseases:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No disease templates are available.",
            )
        generator = CaseGenerator(diseases)
        try:
            disease, generated = generator.generate(
                disease_name=payload.disease_name,
                difficulty=payload.difficulty.value,
                seed=payload.seed,
            )
        except CaseGeneratorError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc

        case = Case(
            patient_pseudo_id=generated.patient_pseudo_id,
            age=generated.age,
            sex=generated.sex,
            clinical_history=generated.clinical_history,
            doctor_request=generated.doctor_request,
            disease_id=disease.id,
            difficulty=generated.difficulty,
            seed=generated.seed,
            generated_by=CaseGeneratedBy.LECTURER,
            requested_by_id=None,
        )
        db.add(case)
        await db.flush()
        await db.refresh(case, attribute_names=["disease"])
        return case

    assert payload.case_id is not None  # enforced by CaseAssignmentCreate's validator
    existing_case = await db.get(Case, payload.case_id)
    if existing_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    if existing_case.generated_by != CaseGeneratedBy.LECTURER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only lecturer-generated cases can be assigned to a group.",
        )
    return existing_case


@router.post(
    "/cases/assign",
    response_model=CaseAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.LECTURER, UserRole.ADMIN))],
)
async def assign_case(
    payload: CaseAssignmentCreate, db: DbSession, current_user: CurrentUser
) -> CaseAssignment:
    """Assign a case (existing or freshly generated) to a student group."""
    case = await _resolve_case_for_assignment(db, current_user, payload)

    assignment = CaseAssignment(
        lecturer_id=current_user.id,
        case_id=case.id,
        assigned_to_group=payload.assigned_to_group,
        due_at=payload.due_at,
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment, attribute_names=["case"])

    logger.info(
        "case_assigned",
        extra={
            "assignment_id": str(assignment.id),
            "case_id": str(case.id),
            "assigned_to_group": assignment.assigned_to_group,
            "lecturer_id": str(current_user.id),
        },
    )
    return assignment


@router.get(
    "/assignments",
    response_model=list[CaseAssignmentRead],
    dependencies=[Depends(require_roles(UserRole.LECTURER, UserRole.ADMIN))],
)
async def list_my_assignments(db: DbSession, current_user: CurrentUser) -> list[CaseAssignment]:
    """Every assignment the requesting lecturer has created, newest first.

    Not in `docs/LLD.md`'s API table, but needed so the lecturer dashboard
    (`docs/SPRINT_PLAN.md` Sprint 6: "frontend: lecturer dashboard (assign
    cases, view class performance)") has a way to list which group labels
    exist at all, rather than requiring the lecturer to already know a
    `group_id` before `GET /lecturer/analytics/{group_id}` becomes useful.
    """
    result = await db.execute(
        select(CaseAssignment)
        .where(CaseAssignment.lecturer_id == current_user.id)
        .order_by(CaseAssignment.created_at.desc())
    )
    return list(result.scalars().all())


@router.get(
    "/analytics/{group_id}",
    response_model=CohortAnalytics,
    dependencies=[Depends(require_roles(UserRole.LECTURER, UserRole.ADMIN))],
)
async def get_cohort_analytics(
    group_id: str, db: DbSession, current_user: CurrentUser
) -> CohortAnalytics:
    """Aggregate performance for every case the requesting lecturer assigned to `group_id`."""
    assignments_result = await db.execute(
        select(CaseAssignment)
        .where(
            CaseAssignment.assigned_to_group == group_id,
            CaseAssignment.lecturer_id == current_user.id,
        )
        .order_by(CaseAssignment.created_at.desc())
    )
    assignments = list(assignments_result.scalars().all())
    if not assignments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assignments found for this group.",
        )

    case_ids = {a.case_id for a in assignments}
    due_at_by_case: dict[uuid.UUID, object] = {a.case_id: a.due_at for a in assignments}

    interpretations_result = await db.execute(
        select(InterpretationResult).where(InterpretationResult.case_id.in_(case_ids))
    )
    interpretations = list(interpretations_result.scalars().all())

    by_case: dict[uuid.UUID, list[InterpretationResult]] = defaultdict(list)
    for interp in interpretations:
        by_case[interp.case_id].append(interp)

    cases_by_id = {a.case_id: a.case for a in assignments}
    case_breakdowns: list[CohortCaseBreakdown] = []
    for case_id, case in cases_by_id.items():
        attempts = by_case.get(case_id, [])
        distinct_students = {i.student_id for i in attempts}
        average = round(sum(i.score for i in attempts) / len(attempts), 1) if attempts else 0.0
        case_breakdowns.append(
            CohortCaseBreakdown(
                case_id=case_id,
                disease_name=case.disease.name,
                difficulty=case.difficulty,
                due_at=due_at_by_case.get(case_id),
                attempts_count=len(attempts),
                distinct_students=len(distinct_students),
                average_score=average,
            )
        )
    case_breakdowns.sort(key=lambda c: c.disease_name)

    distinct_students_overall = {i.student_id for i in interpretations}
    total_attempts = len(interpretations)
    overall_average = (
        round(sum(i.score for i in interpretations) / total_attempts, 1) if total_attempts else 0.0
    )

    topics: list[CohortTopicBreakdown] = []
    if distinct_students_overall:
        mastery_result = await db.execute(
            select(StudentTopicMastery).where(
                StudentTopicMastery.student_id.in_(distinct_students_overall)
            )
        )
        mastery_rows = list(mastery_result.scalars().all())
        mastery_by_topic: dict[str, list[float]] = defaultdict(list)
        for row in mastery_rows:
            mastery_by_topic[row.topic].append(row.mastery_score)
        for topic, scores in sorted(mastery_by_topic.items()):
            topics.append(
                CohortTopicBreakdown(
                    topic=topic,
                    average_mastery=round(sum(scores) / len(scores), 1),
                    students_count=len(scores),
                )
            )

    missing_counter: Counter[str] = Counter()
    for interp in interpretations:
        for finding in interp.missing_findings:
            text = finding.get("expected_finding") if isinstance(finding, dict) else None
            if text:
                missing_counter[text] += 1
    commonly_missed = [
        CommonlyMissedFinding(finding=finding, miss_count=count)
        for finding, count in missing_counter.most_common(_TOP_MISSED_FINDINGS_LIMIT)
    ]

    return CohortAnalytics(
        group_id=group_id,
        assignment_count=len(assignments),
        case_count=len(case_ids),
        distinct_students=len(distinct_students_overall),
        total_attempts=total_attempts,
        overall_average_score=overall_average,
        cases=case_breakdowns,
        topics=topics,
        commonly_missed_findings=commonly_missed,
        assignments=list(assignments),
    )

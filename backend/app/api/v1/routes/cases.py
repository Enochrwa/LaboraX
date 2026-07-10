"""Case retrieval/generation routes.

`GET /cases/next` is the core Sprint 2 deliverable: a student requests a
case and receives a freshly generated, persisted virtual patient scenario.
Generation itself is delegated to `CaseGenerator` (see
`app/services/case_generator/generator.py`) so this route stays a thin
transport/persistence layer, per `docs/HLD.md` §3.2.
"""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, require_roles
from app.db.models.case import Case, CaseGeneratedBy, DifficultyLevel
from app.db.models.disease import Disease, DiseaseCategory
from app.db.models.user import UserRole
from app.schemas.case import CaseRead
from app.services.case_generator.generator import CaseGenerator, CaseGeneratorError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cases", tags=["cases"])


async def _load_diseases(db: DbSession, category: str | None) -> list[Disease]:
    query = select(Disease)
    if category is not None:
        try:
            category_enum = DiseaseCategory(category)
        except ValueError:
            # Not a real category — no rows can possibly match, so behave the
            # same as any other filter with zero results rather than letting
            # an invalid value reach the database as a bind parameter.
            return []
        query = query.where(Disease.category == category_enum)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get(
    "/next", response_model=CaseRead, dependencies=[Depends(require_roles(UserRole.STUDENT))]
)
async def get_next_case(
    db: DbSession,
    current_user: CurrentUser,
    category: Annotated[str | None, Query(description="Filter by disease category.")] = None,
    disease_name: Annotated[
        str | None, Query(description="Request a specific disease by name.")
    ] = None,
    difficulty: Annotated[DifficultyLevel, Query()] = DifficultyLevel.NOVICE,
    seed: Annotated[
        int | None, Query(description="Deterministic seed for reproducible cases.")
    ] = None,
) -> Case:
    """Generate (and persist) the next virtual patient case for the student.

    Every call produces a brand-new case — Sprint 2 does not yet track a
    "current in-progress case" per student (that arrives with the test
    ordering/results flow in Sprint 3). A `seed` may be supplied to
    reproduce an identical case, which lecturer-assigned exams rely on from
    Sprint 6 onward.
    """
    diseases = await _load_diseases(db, category)
    if not diseases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No disease templates are available for the requested filters.",
        )

    generator = CaseGenerator(diseases)
    try:
        disease, generated = generator.generate(
            category=category,
            disease_name=disease_name,
            difficulty=difficulty.value,
            seed=seed,
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
        generated_by=CaseGeneratedBy.SYSTEM,
        requested_by_id=current_user.id,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case, attribute_names=["disease"])

    logger.info(
        "case_generated",
        extra={
            "case_id": str(case.id),
            "disease": disease.name,
            "difficulty": str(case.difficulty),
            "student_id": str(current_user.id),
        },
    )
    return case


@router.get(
    "/{case_id}",
    response_model=CaseRead,
    dependencies=[Depends(require_roles(UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN))],
)
async def get_case(case_id: uuid.UUID, db: DbSession) -> Case:
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return case

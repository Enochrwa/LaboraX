"""Disease template listing.

Sprint 6 adds this alongside the lecturer dashboard: `POST
/lecturer/cases/assign` (`app/api/v1/routes/lecturer.py`) needs a
`disease_name`, and the frontend assign-case form needs a real list to
populate its picker from rather than a hardcoded, driftable copy of the
seed data. Kept as its own tiny route module (not folded into
`cases.py`) since it's a read-only reference list, not part of the
case-generation flow. Open to any authenticated role — a student browsing
"what diseases exist" leaks nothing `GET /cases/next` doesn't already
reveal one case at a time.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.deps import DbSession, require_roles
from app.db.models.disease import Disease, DiseaseCategory
from app.db.models.user import UserRole
from app.schemas.disease import DiseaseSummary

router = APIRouter(prefix="/diseases", tags=["diseases"])


@router.get(
    "",
    response_model=list[DiseaseSummary],
    dependencies=[
        Depends(require_roles(UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN)),
    ],
)
async def list_diseases(
    db: DbSession,
    category: DiseaseCategory | None = None,
) -> list[Disease]:
    """Every disease template, optionally filtered by category, name-sorted."""
    query = select(Disease).order_by(Disease.name)
    if category is not None:
        query = query.where(Disease.category == category)
    result = await db.execute(query)
    return list(result.scalars().all())

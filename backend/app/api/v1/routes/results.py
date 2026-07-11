"""Result retrieval routes.

`GET /results/{case_id}` returns every result generated so far for a case
— i.e. only for tests the student has actually ordered (see
`app/api/v1/routes/tests.py`), never eagerly for the full catalog, per
`docs/PRD.md` §5.2's cost-stewardship principle.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, require_roles
from app.db.models.case import Case
from app.db.models.result import Result
from app.db.models.test_order import TestOrder
from app.db.models.user import UserRole
from app.schemas.result import CaseResultsRead, ResultRead

router = APIRouter(prefix="/results", tags=["results"])


@router.get(
    "/{case_id}",
    response_model=CaseResultsRead,
    dependencies=[
        Depends(require_roles(UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN)),
    ],
)
async def get_case_results(
    case_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> CaseResultsRead:
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    if current_user.role == UserRole.STUDENT and case.requested_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view results for this case.",
        )

    results_result = await db.execute(
        select(Result).where(Result.case_id == case_id).order_by(Result.generated_at)
    )
    results = list(results_result.scalars().all())

    orders_result = await db.execute(select(TestOrder).where(TestOrder.case_id == case_id))
    total_penalty = sum(order.penalty_applied for order in orders_result.scalars().all())

    return CaseResultsRead(
        case_id=case_id,
        total_penalty=total_penalty,
        results=[ResultRead.model_validate(result) for result in results],
    )

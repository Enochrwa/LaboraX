"""Test catalog retrieval + test ordering routes.

`POST /tests/order` is the core Sprint 3 deliverable: a student orders one
or more tests for a case they own, each order's appropriateness/penalty is
computed by `evaluate_relevance` (see
`app/services/test_ordering/relevance.py`), and a result is generated (if
not already present) by `ResultGenerator`
(`app/services/result_generator/generator.py`) — kept as a thin
transport/persistence layer over both services, per `docs/HLD.md` §3.2.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, require_roles
from app.db.models.case import Case
from app.db.models.result import Result
from app.db.models.test_catalog import TestCatalog
from app.db.models.test_order import TestOrder
from app.db.models.user import User, UserRole
from app.schemas.test_catalog import TestCatalogRead
from app.schemas.test_order import TestOrderBatchRead, TestOrderRead, TestOrderRequest
from app.services.result_generator.generator import ResultGenerator
from app.services.test_ordering.relevance import evaluate_relevance

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tests", tags=["tests"])

_result_generator = ResultGenerator()


async def _load_owned_case(db: DbSession, current_user: User, case_id: uuid.UUID) -> Case:
    case = await db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    if case.requested_by_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to order tests for this case.",
        )
    return case


@router.get(
    "/catalog",
    response_model=list[TestCatalogRead],
    dependencies=[
        Depends(require_roles(UserRole.STUDENT, UserRole.LECTURER, UserRole.ADMIN)),
    ],
)
async def get_test_catalog(db: DbSession) -> list[TestCatalog]:
    """List every orderable test, for the frontend's test-selection checklist."""
    result = await db.execute(select(TestCatalog).order_by(TestCatalog.code))
    return list(result.scalars().all())


@router.post(
    "/order",
    response_model=TestOrderBatchRead,
    dependencies=[Depends(require_roles(UserRole.STUDENT))],
)
async def order_tests(
    payload: TestOrderRequest, db: DbSession, current_user: CurrentUser
) -> TestOrderBatchRead:
    """Order one or more tests for a case the requesting student owns.

    Idempotent per `(case, test)`: re-submitting a test code that was
    already ordered for this case returns the existing order/result rather
    than creating a duplicate or re-charging a penalty.
    """
    case = await _load_owned_case(db, current_user, payload.case_id)

    # De-duplicate while preserving submission order.
    requested_codes = list(dict.fromkeys(payload.test_codes))

    catalog_result = await db.execute(
        select(TestCatalog).where(TestCatalog.code.in_(requested_codes))
    )
    tests_by_code = {test.code: test for test in catalog_result.scalars().all()}

    missing_codes = [code for code in requested_codes if code not in tests_by_code]
    if missing_codes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown test code(s): {', '.join(missing_codes)}",
        )

    existing_orders_result = await db.execute(select(TestOrder).where(TestOrder.case_id == case.id))
    existing_orders_by_test_id = {
        order.test_id: order for order in existing_orders_result.scalars().all()
    }

    orders: list[TestOrder] = []
    newly_created: list[TestOrder] = []
    for code in requested_codes:
        test = tests_by_code[code]
        existing_order = existing_orders_by_test_id.get(test.id)
        if existing_order is not None:
            orders.append(existing_order)
            continue

        is_appropriate, penalty_applied = evaluate_relevance(test, case.disease)
        order = TestOrder(
            case_id=case.id,
            student_id=current_user.id,
            test_id=test.id,
            is_appropriate=is_appropriate,
            penalty_applied=penalty_applied,
        )
        db.add(order)
        orders.append(order)
        newly_created.append(order)

        existing_result = await db.execute(
            select(Result).where(Result.case_id == case.id, Result.test_id == test.id)
        )
        if existing_result.scalar_one_or_none() is None:
            result_payload = _result_generator.generate(
                disease=case.disease,
                test=test,
                case_seed=case.seed,
                patient_sex=case.sex.value,
            )
            db.add(Result(case_id=case.id, test_id=test.id, result_payload=result_payload))

    await db.commit()
    for order in orders:
        await db.refresh(order, attribute_names=["test"])

    total_penalty = sum(order.penalty_applied for order in orders)

    if newly_created:
        logger.info(
            "tests_ordered",
            extra={
                "case_id": str(case.id),
                "student_id": str(current_user.id),
                "codes": [order.test.code for order in newly_created],
            },
        )

    return TestOrderBatchRead(
        orders=[TestOrderRead.model_validate(order) for order in orders],
        total_penalty=total_penalty,
    )

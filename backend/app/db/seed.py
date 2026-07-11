"""Idempotent seeding of `diseases` and `test_catalog` from `app/ml/data/*.json`.

Run via `make seed` (see `backend/Makefile`) or `python -m app.db.seed`.
Also used directly by the test suite so integration tests always have a
known, deterministic set of disease templates and orderable tests.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.disease import Disease, DiseaseCategory
from app.db.models.test_catalog import TestCatalog
from app.services.case_generator.seed_data import load_disease_seed_definitions
from app.services.test_ordering.catalog_seed_data import load_test_catalog_definitions

logger = logging.getLogger(__name__)


async def seed_diseases(db: AsyncSession) -> list[Disease]:
    """Insert any disease seed definitions not already present (by name).

    Existing rows are left untouched — this is additive/idempotent, not a
    destructive resync, so lecturer edits made directly in the DB are not
    silently overwritten by re-running the seed script.
    """
    definitions = load_disease_seed_definitions()
    if not definitions:
        logger.warning("seed_diseases_no_definitions_found")
        return []

    existing_names = set(
        (await db.execute(select(Disease.name))).scalars().all(),
    )

    created: list[Disease] = []
    for definition in definitions:
        if definition["name"] in existing_names:
            continue
        disease = Disease(
            name=definition["name"],
            category=DiseaseCategory(definition["category"]),
            symptom_template=definition["symptom_template"],
            lab_pattern_template=definition["lab_pattern_template"],
            difficulty_levels=definition["difficulty_levels"],
        )
        db.add(disease)
        created.append(disease)

    if created:
        await db.commit()
        for disease in created:
            await db.refresh(disease)
        logger.info("seed_diseases_created", extra={"count": len(created)})

    all_diseases = (await db.execute(select(Disease))).scalars().all()
    return list(all_diseases)


async def seed_test_catalog(db: AsyncSession) -> list[TestCatalog]:
    """Insert any test-catalog seed definitions not already present (by code).

    Additive/idempotent, mirroring `seed_diseases` above.
    """
    definitions = load_test_catalog_definitions()
    if not definitions:
        logger.warning("seed_test_catalog_no_definitions_found")
        return []

    existing_codes = set(
        (await db.execute(select(TestCatalog.code))).scalars().all(),
    )

    created: list[TestCatalog] = []
    for definition in definitions:
        if definition["code"] in existing_codes:
            continue
        test = TestCatalog(
            code=definition["code"],
            name=definition["name"],
            category=DiseaseCategory(definition["category"]),
            cost_weight=float(definition["cost_weight"]),
            relevance_rules=definition["relevance_rules"],
        )
        db.add(test)
        created.append(test)

    if created:
        await db.commit()
        for test in created:
            await db.refresh(test)
        logger.info("seed_test_catalog_created", extra={"count": len(created)})

    all_tests = (await db.execute(select(TestCatalog))).scalars().all()
    return list(all_tests)


async def _main() -> None:
    from app.core.logging import configure_logging
    from app.db.session import AsyncSessionLocal

    configure_logging()
    async with AsyncSessionLocal() as session:
        diseases = await seed_diseases(session)
        tests = await seed_test_catalog(session)
    logger.info(
        "seed_complete",
        extra={"diseases_total": len(diseases), "tests_total": len(tests)},
    )


if __name__ == "__main__":
    asyncio.run(_main())

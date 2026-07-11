"""Result model — a generated lab result for a (case, test) pair.

Produced by `ResultGenerator` (see `app/services/result_generator/generator.py`)
the first time a test is ordered for a case. Deterministic given
`(case.seed, test.code)`, so re-fetching results never changes what a
student already saw, and lecturer-assigned exam cases (Sprint 2/Sprint 24)
reproduce identical results for every student.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.test_catalog import TestCatalog


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (UniqueConstraint("case_id", "test_id", name="uq_results_case_test"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    result_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    test: Mapped[TestCatalog] = relationship(TestCatalog, lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Result(id={self.id!r}, case_id={self.case_id!r}, test_id={self.test_id!r})"

"""TestOrder model — a student ordering a test for a case.

`is_appropriate`/`penalty_applied` are computed once, at order time, by
`app.services.test_ordering.relevance.evaluate_relevance` and persisted so
the cost-stewardship signal (see `docs/PRD.md` §5.2) survives independently
of whether the disease's rule set changes later.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.test_catalog import TestCatalog


class TestOrder(Base):
    __tablename__ = "test_orders"
    __table_args__ = (UniqueConstraint("case_id", "test_id", name="uq_test_orders_case_test"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_appropriate: Mapped[bool] = mapped_column(Boolean, nullable=False)
    penalty_applied: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    test: Mapped[TestCatalog] = relationship(TestCatalog, lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"TestOrder(id={self.id!r}, case_id={self.case_id!r}, test_id={self.test_id!r})"

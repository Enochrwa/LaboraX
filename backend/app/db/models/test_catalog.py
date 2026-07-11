"""TestCatalog model — the catalog of orderable laboratory tests.

Each row is a test a student can order for a case (e.g. "Complete Blood
Count", "Peripheral Blood Film"). `relevance_rules` is a small data-driven
rule set (see `app/services/test_ordering/relevance.py`) that determines
whether ordering this test for a given `Disease` is clinically appropriate,
without hardcoding disease names into the ordering logic: a test is
appropriate whenever its `measured_parameters` overlap with the keys the
disease's own `lab_pattern_template.cbc_deltas` defines (or, for tests keyed
off `requires_pattern`, whenever that pattern key is present at all). This
keeps the relevance logic forward-compatible with Phase 2 categories (new
diseases simply define the parameters they affect; no test-ordering code
needs to change).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.disease import DiseaseCategory


class TestCatalog(Base):
    __tablename__ = "test_catalog"

    # Not a pytest test class — this class name coincidentally matches
    # pytest's default `Test*` collection pattern.
    __test__ = False

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[DiseaseCategory] = mapped_column(
        Enum(DiseaseCategory, name="disease_category", native_enum=True),
        nullable=False,
        index=True,
    )
    cost_weight: Mapped[float] = mapped_column(Float, nullable=False)
    relevance_rules: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"TestCatalog(id={self.id!r}, code={self.code!r})"

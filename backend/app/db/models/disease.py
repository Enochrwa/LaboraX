"""Disease model — the knowledge-base entry driving case generation.

Each row is a template (not a patient case): a symptom pattern, an expected
lab-finding pattern, and per-difficulty generation parameters. `CaseGenerator`
samples from these templates to produce unique, internally-consistent patient
cases (see `app/services/case_generator`).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiseaseCategory(StrEnum):
    HEMATOLOGY = "hematology"
    CHEMISTRY = "chemistry"
    MICROBIOLOGY = "microbiology"
    PARASITOLOGY = "parasitology"


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    category: Mapped[DiseaseCategory] = mapped_column(
        Enum(DiseaseCategory, name="disease_category", native_enum=True),
        nullable=False,
        index=True,
    )
    symptom_template: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    lab_pattern_template: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    difficulty_levels: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Disease(id={self.id!r}, name={self.name!r}, category={self.category!r})"

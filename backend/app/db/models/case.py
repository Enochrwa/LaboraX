"""Case model — a single generated virtual patient scenario.

Produced by `CaseGenerator` (see `app/services/case_generator`) from a
`Disease` template. Deterministic when a `seed` is supplied, which lets a
lecturer re-issue the exact same case for standardized/reproducible exams
(Phase 4's practical-exam mode reuses this same mechanism).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.disease import Disease


class PatientSex(StrEnum):
    MALE = "male"
    FEMALE = "female"


class DifficultyLevel(StrEnum):
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CaseGeneratedBy(StrEnum):
    SYSTEM = "system"
    LECTURER = "lecturer"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_pseudo_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[PatientSex] = mapped_column(
        Enum(PatientSex, name="patient_sex", native_enum=True), nullable=False
    )
    clinical_history: Mapped[str] = mapped_column(Text, nullable=False)
    doctor_request: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"), nullable=False
    )
    disease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diseases.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level", native_enum=True), nullable=False
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_by: Mapped[CaseGeneratedBy] = mapped_column(
        Enum(CaseGeneratedBy, name="case_generated_by", native_enum=True),
        default=CaseGeneratedBy.SYSTEM,
        nullable=False,
    )
    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    disease: Mapped[Disease] = relationship(Disease, lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Case(id={self.id!r}, patient_pseudo_id={self.patient_pseudo_id!r})"

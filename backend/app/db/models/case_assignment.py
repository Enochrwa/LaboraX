"""CaseAssignment model — a lecturer assigning a case to a student group.

Sprint 6 (`docs/SPRINT_PLAN.md`): "`case_assignments` table, lecturer
assignment endpoints". Matches `docs/LLD.md` §3's
`case_assignments (id, lecturer_id FK, case_id FK, assigned_to_group,
due_at, created_at)` exactly.

`assigned_to_group` is deliberately a free-text/string identifier rather
than a foreign key into a formal "groups"/"cohorts" table — the LLD's data
model does not define one, and Sprint 6 does not introduce one either, to
avoid a scope-creep enrollment/membership system this MVP doesn't need yet.
A lecturer types a group label (e.g. a class code like `"BLS-Y3-2026"`)
when assigning a case; `GET /api/v1/lecturer/analytics/{group_id}`
(`app/api/v1/routes/lecturer.py`) treats that same string as the cohort key
and aggregates performance from whichever students have submitted
interpretations against the cases assigned to that group — see that
route's module docstring for the full reasoning.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.case import Case


class CaseAssignment(Base):
    __tablename__ = "case_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lecturer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to_group: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    case: Mapped[Case] = relationship(Case, lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"CaseAssignment(id={self.id!r}, case_id={self.case_id!r}, "
            f"assigned_to_group={self.assigned_to_group!r})"
        )

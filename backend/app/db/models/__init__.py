"""SQLAlchemy model registry — import every model so Alembic autogenerate
and `Base.metadata` see the full schema."""

from app.db.models.case import Case, CaseGeneratedBy, DifficultyLevel, PatientSex
from app.db.models.disease import Disease, DiseaseCategory
from app.db.models.user import User, UserRole

__all__ = [
    "Case",
    "CaseGeneratedBy",
    "DifficultyLevel",
    "Disease",
    "DiseaseCategory",
    "PatientSex",
    "User",
    "UserRole",
]

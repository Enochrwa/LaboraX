"""SQLAlchemy model registry — import every model so Alembic autogenerate
and `Base.metadata` see the full schema."""

from app.db.models.case import Case, CaseGeneratedBy, DifficultyLevel, PatientSex
from app.db.models.case_assignment import CaseAssignment
from app.db.models.disease import Disease, DiseaseCategory
from app.db.models.interpretation_result import InterpretationResult
from app.db.models.result import Result
from app.db.models.student_topic_mastery import StudentTopicMastery
from app.db.models.test_catalog import TestCatalog
from app.db.models.test_order import TestOrder
from app.db.models.user import User, UserRole

__all__ = [
    "Case",
    "CaseAssignment",
    "CaseGeneratedBy",
    "DifficultyLevel",
    "Disease",
    "DiseaseCategory",
    "InterpretationResult",
    "PatientSex",
    "Result",
    "StudentTopicMastery",
    "TestCatalog",
    "TestOrder",
    "User",
    "UserRole",
]

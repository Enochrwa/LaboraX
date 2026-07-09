"""SQLAlchemy model registry — import every model so Alembic autogenerate
and `Base.metadata` see the full schema."""

from app.db.models.user import User, UserRole

__all__ = ["User", "UserRole"]

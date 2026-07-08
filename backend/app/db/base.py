"""Declarative base + model registry import point for Alembic autogenerate."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models here so Alembic autogenerate can discover them, e.g.:
# from app.db.models.user import User  # noqa: F401

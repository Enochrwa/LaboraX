"""Declarative base + model registry import point for Alembic autogenerate."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models here so Alembic autogenerate can discover them.
from app.db.models import User  # noqa: E402,F401

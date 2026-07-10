"""Declarative base.

Deliberately does NOT import `app.db.models` here: every model submodule
imports `Base` from this module, so importing models back from `base.py`
creates a circular import as soon as there's more than one model file (each
model's `from app.db.base import Base` would re-enter this file mid-init).

Instead, `app.db.models` (the package `__init__.py`) is the single model
registry — every model is imported there, which is enough for SQLAlchemy's
declarative registry (and therefore `Base.metadata`) to see the full schema,
since class definition itself registers a model on `Base.metadata`. Anything
that needs the full schema (Alembic autogenerate, `Base.metadata.create_all`
in tests) must ensure `app.db.models` has been imported first — Alembic's
`env.py` does this explicitly; the app/test suite gets it for free via
`app.main` transitively importing model modules through the API routes.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

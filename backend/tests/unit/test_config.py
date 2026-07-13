"""Unit tests for `app.core.config`.

Covers `normalize_database_url` in isolation — this is a regression suite
for a real bug found via CI: `str(url)` on a SQLAlchemy `URL` masks the
password as `"***"` by default, so the "normalized" DSN silently stopped
being a working connection string against any Postgres with password auth
actually enabled (i.e. everywhere except a local trust-auth database).
"""

from __future__ import annotations

from app.core.config import normalize_database_url


def test_normalizes_bare_postgresql_scheme_to_asyncpg() -> None:
    result = normalize_database_url("postgresql://laborax:laborax@localhost:5432/laborax")
    assert result.startswith("postgresql+asyncpg://")


def test_leaves_asyncpg_scheme_untouched() -> None:
    raw = "postgresql+asyncpg://laborax:laborax@localhost:5432/laborax"
    assert normalize_database_url(raw) == raw


def test_preserves_the_real_password_rather_than_masking_it() -> None:
    """The regression this suite exists for: `str(url)` renders the
    password as the literal string "***", which happens to "work" against
    an unauthenticated local database but fails everywhere auth is
    enforced."""
    result = normalize_database_url("postgresql://laborax:s3cr3t-pw@localhost:5432/laborax")
    assert "s3cr3t-pw" in result
    assert "***" not in result


def test_preserves_host_port_and_database_name() -> None:
    result = normalize_database_url("postgresql://user:pw@db.example.com:5433/mydb")
    assert result == "postgresql+asyncpg://user:pw@db.example.com:5433/mydb"

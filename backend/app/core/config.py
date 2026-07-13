"""Centralized, environment-driven application settings."""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(str(ROOT_DIR / ".env"), override=False)


def normalize_database_url(raw_url: str) -> str:
    url = make_url(raw_url)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")
    # `str(url)` / `repr(url)` deliberately mask the password with "***" to
    # keep secrets out of logs/tracebacks (SQLAlchemy's default since 1.4).
    # That's exactly wrong here: this is the literal DSN handed to the
    # driver to connect, not something being logged. Using `str(url)`
    # silently produced a connection string with a literal "***" in place
    # of the real password, which connects fine locally against an
    # empty/trust-auth Postgres but fails password authentication anywhere
    # auth is actually enforced (every CI run's `postgres:16-alpine`
    # service, any real deployment). `render_as_string(hide_password=False)`
    # is the explicit, intentional opt-out.
    return url.render_as_string(hide_password=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"), extra="ignore", case_sensitive=False
    )

    environment: str = "local"
    debug: bool = True

    database_url_raw: str = Field(
        "postgresql+asyncpg://laborax:laborax@localhost:5432/laborax",
        alias="DATABASE_URL",
    )
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-in-production-please-use-a-random-32-byte-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    allowed_origins: str = "http://localhost:5173"

    ml_models_dir: str = "app/ml/models"

    @property
    def database_url(self) -> str:
        return normalize_database_url(self.database_url_raw)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

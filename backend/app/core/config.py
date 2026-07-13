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
    return str(url)


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

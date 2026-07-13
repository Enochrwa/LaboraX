"""FastAPI application factory for LaboraX."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_ctx_var
from app.db.session import engine

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level="DEBUG" if settings.debug else "INFO")

    app = FastAPI(
        title="LaboraX API",
        description="AI Practical Laboratory Simulator - backend API",
        version="0.1.0",
        debug=settings.debug,
    )

    @app.on_event("startup")
    async def run_migrations() -> None:
        alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: command.upgrade(alembic_cfg, "head")
            )
            logger.info("alembic_migrations_applied")
        except Exception:
            logger.warning("alembic_migrations_failed", exc_info=True)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming_id = request.headers.get("x-request-id")
        request_id = incoming_id or uuid.uuid4().hex
        token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)
        response.headers["x-request-id"] = request_id
        return response

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        db_status = "ok"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            db_status = "down"
            logger.warning("health_check_db_unavailable")
        return {"status": db_status, "environment": settings.environment}

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()

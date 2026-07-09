"""FastAPI application factory for LaboraX."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, request_id_ctx_var


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level="DEBUG" if settings.debug else "INFO")

    app = FastAPI(
        title="LaboraX API",
        description="AI Practical Laboratory Simulator - backend API",
        version="0.1.0",
        debug=settings.debug,
    )

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
        return {"status": "ok", "environment": settings.environment}

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()

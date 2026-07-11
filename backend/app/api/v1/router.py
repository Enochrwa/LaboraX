"""Aggregates all v1 route modules into a single router."""

from fastapi import APIRouter

from app.api.v1.routes import auth, cases, results, tests

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(cases.router)
api_router.include_router(tests.router)
api_router.include_router(results.router)

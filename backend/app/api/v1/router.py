"""Aggregates all v1 route modules into a single router."""

from fastapi import APIRouter

from app.api.v1.routes import auth, cases, interpretations, results, scoring, tests

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(cases.router)
api_router.include_router(tests.router)
api_router.include_router(results.router)
api_router.include_router(interpretations.router)
api_router.include_router(scoring.router)

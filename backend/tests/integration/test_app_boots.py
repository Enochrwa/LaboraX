"""Integration-level smoke test: the app object builds without error."""
from app.main import create_app


def test_create_app_builds_fastapi_instance() -> None:
    app = create_app()
    assert app.title == "LaboraX API"

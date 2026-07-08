.PHONY: install dev lint format typecheck test cov run migrate

install:
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy app

test:
	pytest

cov:
	pytest --cov=app --cov-report=html

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

# Contributing to LaboraX

## Local setup

```bash
# Root tooling (git hooks, commit linting)
npm install

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Or run the full stack with Docker
docker compose up --build
```

## Commit conventions

This repo uses [Conventional Commits](https://www.conventionalcommits.org/), enforced by commitlint via a Husky `commit-msg` hook:

```
feat: add case generator seeding
fix(backend): correct malaria lab-pattern template
docs: update HLD with scaling section
```

## Before opening a PR

- Backend: `make lint && make typecheck && make test` (from `backend/`)
- Frontend: `npm run lint && npm run typecheck && npm run test` (from `frontend/`)
- Husky pre-commit/pre-push hooks run these automatically once you've run `npm install` at the repo root

## Branching

- `main` is protected; land work via PRs
- Feature branches: `feature/<short-description>`
- Fix branches: `fix/<short-description>`

## Docs

Significant architecture or scope changes should be reflected in `docs/PRD.md`, `docs/HLD.md`, `docs/LLD.md`, or `docs/SPRINT_PLAN.md` as part of the same PR.

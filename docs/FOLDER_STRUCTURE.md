# LaboraX — Folder Structure

```
LaboraX/
├── README.md
├── CONTRIBUTING.md
├── CODEOWNERS
├── .gitignore
├── .editorconfig
├── package.json               # root: husky, lint-staged, commitlint
├── commitlint.config.js
├── .lintstagedrc.json
├── .husky/                     # pre-commit / commit-msg / pre-push git hooks
├── docker-compose.yml           # full local stack: postgres, redis, backend, frontend
├── .github/
│   ├── workflows/                # ci.yml, commitlint.yml, deploy.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
├── docs/
│   ├── PRD.md                     # Product Requirements Document
│   ├── HLD.md                     # High-Level Design
│   ├── LLD.md                     # Low-Level Design
│   ├── SPRINT_PLAN.md             # Full sprint plan (Phase 1-3)
│   └── FOLDER_STRUCTURE.md        # This file
│
├── backend/                        # Single unified FastAPI backend
│   ├── pyproject.toml               # ruff + mypy + pytest config
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── Makefile                      # lint/format/typecheck/test/run/migrate
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/                    # DB migrations (async env.py)
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory
│   │   ├── core/                     # config, security, deps, logging
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   ├── base.py
│   │   │   └── models/                # SQLAlchemy ORM models
│   │   ├── schemas/                    # Pydantic request/response models
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── routes/               # auth, cases, tests, results,
│   │   │                                 # interpretations, scoring,
│   │   │                                 # lecturer, admin
│   │   ├── services/
│   │   │   ├── case_generator/
│   │   │   ├── result_predictor/
│   │   │   ├── answer_evaluator/
│   │   │   └── recommender/
│   │   ├── ml/
│   │   │   ├── models/                    # serialized model artifacts
│   │   │   ├── training/                  # offline training scripts
│   │   │   └── data/                      # disease/symptom/lab-pattern seeds
│   │   ├── workers/                        # ARQ background tasks
│   │   └── utils/
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── frontend/                        # React + TypeScript
│   ├── package.json
│   ├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
│   ├── vite.config.ts               # includes vitest config
│   ├── .eslintrc.cjs
│   ├── .prettierrc.json / .prettierignore
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── app/                       # app shell, routing, providers
│       ├── api/                        # typed API client
│       ├── store/                       # Redux Toolkit slices
│       ├── features/
│       │   ├── dashboard/
│       │   ├── hematology/
│       │   ├── microbiology/
│       │   ├── clinicalChemistry/
│       │   ├── parasitology/
│       │   └── lecturerDashboard/
│       ├── components/                    # shared UI components
│       ├── hooks/                          # shared React hooks
│       ├── i18n/                            # en / fr / rw translations
│       └── theme/                            # MUI theme tokens
│
├── infra/
│   ├── docker/                        # Dockerfiles, docker-compose (local dev)
│   └── ci/                             # GitHub Actions workflow definitions
│
└── scripts/                            # dev/deploy helper scripts
```

## Notes
- `backend/` is a **single FastAPI service** — API, services, and ML/NLP inference all live in one deployable app, per the architectural decision in `HLD.md` §7.
- `.gitkeep` files mark currently-empty scaffold directories; they will be removed as real files land in Sprint 1 onward per `SPRINT_PLAN.md`.
- Model artifacts under `backend/app/ml/models/` are versioned but kept small (CPU-inference models only); large binary artifacts should use Git LFS or be pulled from object storage at deploy time rather than committed directly once they exceed a few MB.

# LaboraX — High-Level Design (HLD v1.0)

## 1. Architectural Principle

**Single unified FastAPI backend.** Rather than splitting business logic (Node.js) from AI/ML services (Python/FastAPI) as is common in similar stacks, LaboraX runs one FastAPI application that owns the REST API, business/domain logic, and ML/NLP inference in-process (or via internal async workers). This reduces operational complexity, avoids cross-service serialization overhead, and fits a solo-developer, free-tier-budget context.

## 2. System Context

```
                         ┌────────────────────┐
                         │   Student / Lecturer │
                         │     (Browser/App)    │
                         └──────────┬───────────┘
                                    │ HTTPS
                         ┌──────────▼───────────┐
                         │   React + TypeScript   │
                         │   Frontend (Vercel)    │
                         └──────────┬───────────┘
                                    │ REST/JSON (JWT auth)
                         ┌──────────▼───────────┐
                         │      FastAPI App        │
                         │  (Render / Fly.io)      │
                         │ ┌──────────────────┐  │
                         │ │  API Layer (v1)    │  │
                         │ ├──────────────────┤  │
                         │ │ Domain Services     │  │
                         │ │ - Case Generator    │  │
                         │ │ - Result Predictor  │  │
                         │ │ - Answer Evaluator  │  │
                         │ │ - Recommender       │  │
                         │ ├──────────────────┤  │
                         │ │  ML/NLP Layer       │  │
                         │ │ (sklearn/XGBoost/   │  │
                         │ │  sentence-transf.)  │  │
                         │ └──────────────────┘  │
                         └────┬─────────────┬────┘
                              │             │
                   ┌──────────▼───┐   ┌────▼──────────┐
                   │  PostgreSQL    │   │     Redis        │
                   │ (Neon/Supabase)│   │ (cache + queue)  │
                   └────────────────┘   └────────┬────────┘
                                                  │
                                       ┌──────────▼─────────┐
                                       │  ARQ Background      │
                                       │  Workers (async jobs, │
                                       │  case pre-generation) │
                                       └───────────────────────┘
```

## 3. Components

### 3.1 Frontend (React + TypeScript)
- MUI component library, Redux Toolkit + TanStack Query for state/data fetching
- Feature-sliced structure: `dashboard`, `hematology`, `microbiology`, `clinicalChemistry`, `parasitology`, `lecturerDashboard`
- i18n (English/French/Kinyarwanda)
- Deployed on Vercel free tier

### 3.2 FastAPI Backend (single service)
- **API layer:** versioned REST routers (`/api/v1/...`) — auth, cases, tests, results, interpretations, scoring, lecturer, admin
- **Domain services layer:** encapsulates business rules, independent of transport (reusable by workers)
- **ML/NLP layer:** wraps model inference behind clean service interfaces so models can be swapped without touching API code
- **Persistence layer:** SQLAlchemy 2.0 async ORM + Alembic migrations
- **Background workers:** ARQ (Redis-backed) for expensive/batch operations (bulk case pre-generation, nightly analytics rollups)

### 3.3 AI Components (mapped to FastAPI internal services)

| Component | Purpose | Approach |
|---|---|---|
| Case Generator | Produce unlimited realistic patient scenarios | Template + rule-constrained generation from disease/symptom/lab-pattern database; optional Bayesian/Decision-Tree variation layer |
| Result Prediction Model | Predict/rank likely conditions from symptom + lab inputs (used to validate generated cases and, later, as a differential-diagnosis teaching aid) | Logistic Regression / Random Forest / XGBoost, CPU inference |
| Answer Evaluation | Score free-text student interpretations against expected findings | Sentence-Transformers (small models) + spaCy preprocessing; cosine similarity + rule-based finding extraction |
| Recommender | Suggest next cases based on weak topics | Collaborative filtering / simple rule-based weighted scoring on topic mastery |

All models are CPU-only, small, and versioned as artifacts under `backend/app/ml/models/`.

### 3.4 Data Store
- **PostgreSQL** — system of record: users, cases, test orders, results, interpretations, scores, recommendations
- **Redis** — response caching, rate limiting, ARQ job queue, session/token blacklist

### 3.5 Auth & RBAC
- JWT access + refresh tokens
- Roles: `student`, `lecturer`, `admin`
- Route-level dependency-injected permission checks in FastAPI

## 4. Deployment View (Free-Tier First)

| Layer | Service | Notes |
|---|---|---|
| Frontend | Vercel | Free tier, auto-deploy from `main` |
| Backend | Render or Fly.io | Free/low-cost tier, single FastAPI container |
| Database | Neon or Supabase Postgres | Free tier, autoscaling connection pooling via PgBouncer |
| Cache/Queue | Upstash Redis | Free tier, serverless Redis |
| CI/CD | GitHub Actions | Lint, type-check, test, build on PR + push to `main` |
| Object storage (future, images) | Cloudflare R2 | Free tier, for virtual microscopy images in Phase 3 |

## 5. Cross-Cutting Concerns

- **Observability:** structured logging (JSON), request ID correlation, basic Prometheus-compatible metrics endpoint
- **Config:** Pydantic Settings, environment-variable driven, `.env` for local dev
- **Security:** input validation via Pydantic schemas, rate limiting via Redis, CORS restricted to known frontend origins, secrets never committed (see `.gitignore`)
- **Testing:** pytest (unit + integration), httpx `AsyncClient` for API tests, coverage gate in CI
- **Migrations:** Alembic, forward-only, reviewed per PR

## 6. Scaling Path

1. **Pilot (MVP):** single FastAPI instance, free-tier Postgres/Redis — target ≤200 concurrent students
2. **Growth:** horizontal scale of stateless FastAPI containers behind a load balancer; move heavy case-generation to ARQ workers; add read replicas
3. **Scale:** introduce dedicated inference workers if ML load grows beyond what the API containers should absorb; consider managed vector store if semantic search/evaluation volume grows significantly

## 7. Why Not Split Node.js + FastAPI

A prior draft considered a Node.js API with a separate FastAPI ML microservice (a pattern used in some of the author's other projects). For LaboraX this is intentionally avoided: as a solo-developer project, one language/runtime end-to-end reduces context-switching, deployment surface area, and cross-service contract drift. FastAPI's async support, Pydantic validation, and native Python ML ecosystem access make a single-service architecture both simpler and sufficient at MVP-to-growth scale.

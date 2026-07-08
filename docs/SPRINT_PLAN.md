# LaboraX — Sprint Plan (Solo Developer, 2-Week Sprints)

Scope: Phase 1 (MVP) → Phase 2 → Phase 3, matching `docs/PRD.md`. All sprints assume a single unified FastAPI backend.

## Phase 1 — MVP: Hematology Simulator (Sprints 1–6, ~12 weeks)

### Sprint 1 — Foundations
- Repo scaffolding (this structure), CI pipeline (GitHub Actions: lint, type-check, test)
- FastAPI app skeleton: `main.py`, `core/config.py`, `core/logging.py`
- PostgreSQL setup (Neon/Supabase), Alembic init, base models (`users`)
- Auth: register/login/refresh (JWT), RBAC dependency scaffolding
- Frontend scaffolding: Vite + React + TS + MUI, routing shell, auth pages

**Deliverable:** deployable skeleton with working auth end-to-end.

### Sprint 2 — Case Data Model & Generator v1
- `diseases`, `cases` tables + migrations
- Seed disease/symptom/lab-pattern data (Hematology: malaria, anemia, generic infection)
- `CaseGenerator` service v1 (template-based, deterministic seeding)
- `GET /api/v1/cases/next` endpoint
- Frontend: dashboard + case intake view

**Deliverable:** student can log in and receive a generated virtual patient case.

### Sprint 3 — Test Ordering & Result Generation
- `test_catalog`, `test_orders`, `results` tables
- Test relevance rules + cost-penalty logic
- Result generator (CBC values, differential count, blood film findings) tied to case pathology
- Endpoints: `POST /tests/order`, `GET /results/{case_id}`
- Frontend: test selection checklist UI, results display panel

**Deliverable:** full order → result flow for CBC/Blood Film cases.

### Sprint 4 — Answer Evaluation Engine
- `interpretation_results` table
- `AnswerEvaluator` service: spaCy preprocessing + sentence-transformer similarity scoring
- Golden-case regression test fixtures
- `POST /api/v1/interpretations` endpoint
- Frontend: interpretation text input + score/feedback display

**Deliverable:** student can submit a free-text interpretation and receive an AI-evaluated score.

### Sprint 5 — AI Tutor Feedback & Scoring
- Domain rule-based tutor explanation templates (why a finding matters, tied to disease template)
- `student_topic_mastery` table + update logic
- `GET /api/v1/scoring/me` endpoint
- Frontend: tutor feedback panel, personal progress view

**Deliverable:** students see *why* answers are right/wrong and track topic mastery over time.

### Sprint 6 — Lecturer Dashboard & MVP Hardening
- `case_assignments` table, lecturer assignment endpoints
- Cohort analytics endpoint (`GET /lecturer/analytics/{group_id}`)
- Frontend: lecturer dashboard (assign cases, view class performance)
- Full regression pass: backend (pytest + coverage), frontend (ESLint/Prettier/tsc), load smoke test
- Deploy to Render/Fly.io + Vercel, free-tier infra wiring finalized

**Deliverable:** MVP complete — Hematology module fully usable by students and lecturers, deployed.

---

## Phase 2 — Expansion (Sprints 7–11, ~10 weeks)

### Sprint 7 — Clinical Chemistry Module
- Seed disease/lab-pattern data for Chemistry (LFTs, RFTs, electrolytes)
- Extend `CaseGenerator`/result generator for chemistry result types
- Frontend: Clinical Chemistry feature module

### Sprint 8 — Result Prediction Model
- `ResultPredictor` service (Logistic Regression / Random Forest / XGBoost)
- Case-consistency validation using predictor during generation
- Endpoint exposing differential-condition probabilities (teaching aid)

### Sprint 9 — Microbiology Module
- Culture/sensitivity case templates, organism ID scenarios
- Frontend: Microbiology feature module

### Sprint 10 — Parasitology Module + Recommender v1
- Stool/blood parasite case templates
- `Recommender` service v1 (weighted topic-mastery-based next-case suggestions)
- `recommendations` table + endpoint
- Frontend: "recommended for you" widget on dashboard

### Sprint 11 — Analytics & Lecturer Tooling v2
- Item-level difficulty analysis (which findings are most-missed cohort-wide)
- Expanded lecturer export (CSV/PDF class reports)
- Performance/regression pass across Phase 2 modules

---

## Phase 3 — Advanced (Sprints 12–16+, ~10+ weeks)

### Sprint 12 — Molecular Biology + Histopathology Data Models
- New disease/case templates for both departments
- Frontend feature modules

### Sprint 13 — Conversational AI Tutor (Grounded)
- Constrain any generative follow-up Q&A strictly to case's structured clinical/lab data (no open-domain chat)
- Guardrails + evaluation harness for tutor responses

### Sprint 14 — Virtual Microscopy (Computer Vision) v1
- Image dataset curation/licensing for parasite/cell/organism recognition
- Lightweight CV model integration (MobileNet/EfficientNet/YOLO-lite), CPU inference
- Object storage integration (Cloudflare R2) for images
- Frontend: image upload + annotated result view

### Sprint 15 — Mobile App Kickoff (React Native)
- Shared API client reuse, auth flow, core case-practice flow on mobile

### Sprint 16 — Speech-Based Evaluation (Exploratory)
- Student verbal case discussion → transcription → evaluated against same finding-extraction pipeline
- Feasibility spike; may extend beyond this sprint depending on results

---

## Cross-Sprint (Ongoing Every Sprint)
- CI must stay green: ruff, mypy, pytest (backend); ESLint, Prettier, tsc (frontend)
- Alembic migration review on every schema change
- Update `docs/` (PRD/HLD/LLD) when scope materially changes
- Keep infra within free-tier budget; flag before any paid-tier dependency is introduced

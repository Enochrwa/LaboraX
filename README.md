# LaboraX 🧪

**A virtual laboratory where students practice diagnosis, testing, and interpretation anytime — without needing physical samples or expensive laboratory resources.**

> Think of it as a flight simulator, but for laboratory scientists.

LaboraX is an AI-powered practical laboratory simulator for Biomedical Laboratory Science, Medicine, Nursing, Pharmacy, and Public Health students. It generates unlimited realistic virtual patient cases, simulates test results, and evaluates student interpretations with instant, explainable AI feedback — built to work in low-resource, high-student-volume environments such as African university health science programs.

---

## Why LaboraX

Universities across Rwanda and the wider region face limited reagents, few laboratory instruments, expensive practical sessions, and large student cohorts sharing scarce equipment. LaboraX removes the physical bottleneck: unlimited virtual patients, zero reagent cost, standardized assessment, and practice available from anywhere.

## Core Modules (Phase 1 → Phase 3)

| Phase | Departments | Status |
|---|---|---|
| Phase 1 (MVP) | Hematology (CBC, Blood Film, Anemia, Malaria) | Planned |
| Phase 2 | Clinical Chemistry, Microbiology, Parasitology | Planned |
| Phase 3 | Molecular Biology, Histopathology, AI Tutor, Virtual Microscopy, Mobile App | Planned |

## Tech Stack

LaboraX uses a **single unified FastAPI backend** — no mixed Node.js/FastAPI split. Python end-to-end on the server keeps the ML/NLP pipeline, business logic, and API in one deployable service.

- **Backend:** FastAPI (async), SQLAlchemy 2.0 + Alembic, Pydantic v2, PostgreSQL, Redis (cache/queue), ARQ (background workers)
- **AI/ML:** scikit-learn, XGBoost, sentence-transformers (answer similarity), spaCy (NLP), TensorFlow Lite (future CV models) — CPU-only inference
- **Frontend:** React + TypeScript, MUI, Redux Toolkit / TanStack Query, React Hook Form, i18n (English/Kinyarwanda/French), Vite
- **Auth:** JWT (access + refresh), role-based access control (Student, Lecturer, Admin)
- **Infra (free-tier friendly):** Vercel (frontend), Render/Fly.io (FastAPI backend), Supabase or Neon (Postgres), Upstash (Redis)

See [`docs/HLD.md`](docs/HLD.md) for architecture, [`docs/LLD.md`](docs/LLD.md) for implementation-level design, and [`docs/PRD.md`](docs/PRD.md) for product scope.

## Repository Structure

See [`docs/FOLDER_STRUCTURE.md`](docs/FOLDER_STRUCTURE.md) for the full annotated tree.

```
LaboraX/
├── backend/        # FastAPI monolith (API, services, ML, workers)
├── frontend/       # React + TypeScript web app
├── infra/          # Docker, CI/CD configs
├── docs/           # PRD, HLD, LLD, sprint plan
└── scripts/        # dev/deploy helper scripts
```

## Documentation

- [Product Requirements Document (PRD)](docs/PRD.md)
- [High-Level Design (HLD)](docs/HLD.md)
- [Low-Level Design (LLD)](docs/LLD.md)
- [Sprint Plan](docs/SPRINT_PLAN.md)
- [Folder Structure](docs/FOLDER_STRUCTURE.md)

## Getting Started (once code lands)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## License

TBD.

## Author

Maintained by [james7dev](https://github.com/james7dev).

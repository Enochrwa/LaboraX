# LaboraX — Sprint Plan (Solo Developer, 2-Week Sprints)

Scope: Phase 1 (MVP) → Phase 2 → Phase 3 → **Phase 4 (Immersive XR: VR/AR)**, matching `docs/PRD.md`. All sprints assume a single unified FastAPI backend. Phase 4 is new: it takes LaboraX from a text/data-driven simulator to a fully immersive virtual laboratory, while preserving the free-tier-first, low-resource-friendly principle that defines the product (see "XR Design Philosophy" below).

## XR Design Philosophy (read before Phase 4)

VR/AR must be an **enhancement layer, not a hard requirement**. A student on a low-end Android phone with patchy data must still get the full core learning loop (Phases 1–3). The XR layer is added as **progressive enhancement** on top of that same case/result/evaluation engine — same backend, same data model, same scoring — so nothing already built has to be thrown away:

- **Tier 0 — Text/2D (existing MVP):** works everywhere, zero extra hardware.
- **Tier 1 — AR passthrough (phone camera):** markerless AR overlays (organism/cell recognition, virtual slide-on-desk) using the phone the student already owns. No headset needed.
- **Tier 2 — WebXR VR (headset optional):** full 3D lab bench, hand tracking, haptics — runs in-browser via WebXR, degrades gracefully to a 3D "desktop mode" (mouse/keyboard/touch) on devices without a headset, so nobody is blocked from the immersive scenes.
- **Tier 3 — Shared/institutional hardware:** low-cost cardboard/Quest-class headsets on a lab cart, shared across a cohort, for the highest-fidelity sessions (practical exams, cohort VR classes).

This mirrors the same reasoning already in `HLD.md` §7 (why the backend stayed a single service) — the immersive layer must not fragment the codebase or the infra budget. All 3D/AR/VR features are additive frontend surfaces on top of the existing `/api/v1/...` domain services; no change to the core Answer Evaluation or Case Generator algorithms is required for Phase 4 to work.

---

## Phase 1 — MVP: Hematology Simulator (Sprints 1–6, ~12 weeks)

### Sprint 1 — Foundations
- Repo scaffolding (this structure), CI pipeline (GitHub Actions: lint, type-check, test)
- FastAPI app skeleton: `main.py`, `core/config.py`, `core/logging.py`
- PostgreSQL setup (Neon/Supabase), Alembic init, base models (`users`)
- Auth: register/login/refresh (JWT), RBAC dependency scaffolding
- Frontend scaffolding: Vite + React + TS + MUI, routing shell, auth pages

**Deliverable:** deployable skeleton with working auth end-to-end.

### Sprint 2 — Case Data Model & Generator v1 ✅
- `diseases`, `cases` tables + migrations
- Seed disease/symptom/lab-pattern data (Hematology: malaria, anemia, generic infection)
- `CaseGenerator` service v1 (template-based, deterministic seeding)
- `GET /api/v1/cases/next` endpoint
- Frontend: dashboard + case intake view

**Deliverable:** student can log in and receive a generated virtual patient case.

> **Status:** implemented on `feature/sprint-two-implementation`. `Disease`/`Case` models +
> Alembic migration (`4f931cec4aae`); three hematology disease templates seeded via
> `app/db/seed.py` (`make seed`); `CaseGenerator` (`app/services/case_generator/generator.py`)
> produces deterministic, difficulty-scaled cases from a `(disease, difficulty, seed)` triple;
> `GET /api/v1/cases/next` (student-only) and `GET /api/v1/cases/{id}` (student/lecturer/admin)
> routes added; dashboard now links to a new `/hematology/case` intake page showing patient
> demographics, chief complaint, presenting symptoms, and vitals, with a "get a new case" action.
> 46 backend tests / 13 frontend tests added, all green; ruff, mypy, ESLint, Prettier, tsc all clean.

### Sprint 3 — Test Ordering & Result Generation
- `test_catalog`, `test_orders`, `results` tables
- Test relevance rules + cost-penalty logic
- Result generator (CBC values, differential count, blood film findings) tied to case pathology
- Endpoints: `POST /tests/order`, `GET /results/{case_id}`
- Frontend: test selection checklist UI, results display panel

**Deliverable:** full order → result flow for CBC/Blood Film cases.

### Sprint 4 — Answer Evaluation Engine ✅
- `interpretation_results` table
- `AnswerEvaluator` service: spaCy preprocessing + sentence-transformer similarity scoring
- Golden-case regression test fixtures
- `POST /api/v1/interpretations` endpoint
- Frontend: interpretation text input + score/feedback display

**Deliverable:** student can submit a free-text interpretation and receive an AI-evaluated score.

> **Status:** implemented on `feature/sprint-four-implementation`. `InterpretationResult` model +
> Alembic migration (`739c748e925d`); `AnswerEvaluator`
> (`app/services/answer_evaluator/evaluator.py`) segments a submission into candidate
> finding-statements, matches them against a disease's `expected_findings` via TF-IDF +
> cosine similarity, and applies a rule-based polarity/parameter check to catch statements that
> lexically resemble a finding but contradict its direction (e.g. "hemoglobin is normal" vs an
> expected "hemoglobin is decreased"). **Deviates from the LLD's sentence-transformer sketch:**
> a downloaded HuggingFace model adds a cold-start/network dependency that conflicts with the
> free-tier/low-resource principle in `docs/HLD.md` §1/§7 — the same call already made on
> HandyRwanda. The similarity backend sits behind `_similarity_matrix()` specifically so it can
> be swapped for a semantic-embedding model later without touching the scoring algorithm.
> `POST /api/v1/interpretations` (student-only, creates a new attempt each submission) and
> `GET /api/v1/interpretations/{case_id}` (student/lecturer/admin, ownership-checked) routes
> added; frontend `InterpretationPage` (free-text box, score chip + progress bar, confirmed/
> missing/incorrect finding lists, tutor feedback, submission history) linked from the results
> panel once a case has at least one result. Golden-case regression fixtures cover all three
> seeded diseases plus empty/irrelevant/contradictory submissions. 113 backend tests / 21
> frontend tests, all green; ruff, mypy (strict), ESLint, Prettier, tsc all clean; 97%+ backend
> coverage, 96%+ frontend coverage on `InterpretationPage`.

### Sprint 5 — AI Tutor Feedback & Scoring ✅
- Domain rule-based tutor explanation templates (why a finding matters, tied to disease template)
- `student_topic_mastery` table + update logic
- `GET /api/v1/scoring/me` endpoint
- Frontend: tutor feedback panel, personal progress view

**Deliverable:** students see *why* answers are right/wrong and track topic mastery over time.

> **Status:** implemented on `feature/sprint-five-implementation`. `app/services/tutor/
> explanations.py` maps the same canonical parameter/polarity vocabulary
> `AnswerEvaluator`/`preprocessing.py` already extracts to a coarser learning `topic` (e.g.
> `red_cell_indices`, `parasitology`) plus a "why this matters" explanation, reusing that
> extraction rather than a second NLP pass — every `FindingMatchResult` and
> `IncorrectStatementResult` now carries both, and the tutor feedback summary surfaces the
> explanation for the most important gap. `AnswerEvaluator.evaluate()` also rolls findings up
> into a per-topic `TopicScore` breakdown. `student_topic_mastery` table + Alembic migration
> (`a1c3f6b2d9e4`, one row per `(student, topic)`); `MasteryTracker`
> (`app/services/mastery/tracker.py`) blends each submission's `TopicScore`s into the running
> mastery value via an exponential moving average (alpha=0.35), called synchronously right after
> `POST /api/v1/interpretations` persists its result. **Deviates from the LLD's "async, via ARQ
> task if computation is non-trivial" sketch:** the computation is a handful of dict lookups plus
> one upsert-shaped query per touched topic — not non-trivial — so, matching the same reasoning
> already applied to `AnswerEvaluator` in Sprint 4, this runs in-request rather than standing up
> the ARQ worker/Redis queue infra a full async pipeline would need; `app/workers/` remains an
> empty scaffold this can move onto later without changing either service's public interface.
> `GET /api/v1/scoring/me` (student-only) returns topic mastery + a weighted overall mastery
> score + recent submission history. Frontend: `InterpretationResultCard` now shows each
> finding's explanation inline; new `ScoringPage` (`/progress`, linked from the dashboard and the
> interpretation page) shows overall mastery, a progress bar per topic, and recent attempts, with
> full en/fr/rw translations. 143 backend tests / 24 frontend tests, all green; ruff, mypy
> (strict), ESLint, Prettier, tsc all clean; 97%+ backend coverage.

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

## Phase 3 — Advanced (Sprints 12–16, ~10 weeks)

### Sprint 12 — Molecular Biology + Histopathology Data Models
- New disease/case templates for both departments
- Frontend feature modules

### Sprint 13 — Conversational AI Tutor (Grounded)
- Constrain any generative follow-up Q&A strictly to case's structured clinical/lab data (no open-domain chat)
- Guardrails + evaluation harness for tutor responses

### Sprint 14 — Virtual Microscopy (Computer Vision) v1 — *XR Foundation Sprint*
- Image dataset curation/licensing for parasite/cell/organism recognition
- Lightweight CV model integration (MobileNet/EfficientNet/YOLO-lite), CPU inference
- Object storage integration (Cloudflare R2) for images
- Frontend: image upload + annotated result view
- **Foundation for Phase 4:** structure specimen image metadata (organism class, bounding boxes, stain type, magnification) so the same CV outputs can drive the AR overlay and 3D slide renderer in Sprint 18 without re-deriving them

### Sprint 15 — Mobile App Kickoff (React Native)
- Shared API client reuse, auth flow, core case-practice flow on mobile
- Camera-permission plumbing and device-capability detection (GPU tier, ARCore/ARKit support) added here so Phase 4's AR sprints can build directly on it

### Sprint 16 — Speech-Based Evaluation (Exploratory)
- Student verbal case discussion → transcription → evaluated against same finding-extraction pipeline
- Feasibility spike; may extend beyond this sprint depending on results
- Spike doubles as groundwork for in-VR voice commands (Sprint 19) and the spatial AI tutor voice (Sprint 22)

---

## Phase 4 — Immersive XR: VR & AR Realism Layer (Sprints 17–24, ~16 weeks)

Goal: make LaboraX feel like an actual physical lab — a real bench, real specimens under a real-feeling microscope, real lab sounds, teammates working beside you — while keeping the Tier 0 (text/2D) experience fully intact for students without capable hardware.

### Sprint 17 — 3D Asset Pipeline & WebXR Foundations
- Evaluate/select rendering stack: Three.js + `@react-three/fiber` + `@react-three/xr` (WebXR Device API), glTF/GLB as the standard asset format
- Blender-based (or licensed asset marketplace) pipeline for lab equipment models: microscope, centrifuge, analyzer, pipettes, slide rack, reagent bottles — optimized/low-poly with baked PBR textures for CPU/mobile-GPU-friendly rendering
- Device-capability detection service (WebXR support, GPU tier, headset presence) reused from Sprint 15's mobile capability check; renders Tier 0/1/2 automatically based on device
- Establish a performance budget (target frame time, draw calls, texture memory) so later sprints don't regress low-end devices
- CI addition: visual/asset build smoke test (glTF validation, bundle-size budget check)

**Deliverable:** an empty but navigable 3D lab bench scene, loads on desktop/mobile browsers, WebXR-ready but functions in plain 3D "desktop mode" with no headset.

### Sprint 18 — AR Specimen Scanning & Markerless Overlay
- Markerless AR (WebXR AR module / AR.js / 8th Wall-class approach) for phone camera passthrough
- AR overlay pipeline reusing the Sprint 14 CV model output: point the phone at a printed/physical reference card or a "virtual slide" and see annotated organisms/cells/parasites rendered in-place with bounding boxes and labels
- 3D slide renderer: a photoreal virtual blood film / stool smear rendered as a navigable 3D plane with simulated depth-of-field focus (mouse-drag or phone-tilt "focus knob"), replacing the flat 2D image with something that feels like looking through an eyepiece
- Frontend: AR mode toggle inside the existing Virtual Microscopy feature module (Tier 1 enhancement, not a separate app)

**Deliverable:** a student can scan/view a virtual slide through their phone camera and see AI-identified findings annotated in real time, in addition to the existing 2D flow.

### Sprint 19 — VR Virtual Lab Bench (Hand Tracking & Interaction)
- Full VR scene: pick up a pipette, draw reagent, add it to a sample, place a slide under the virtual microscope, adjust focus — using WebXR hand-tracking/controller input
- Physics-based interaction (grab, pour, drop) via a lightweight physics engine (e.g. Rapier/Cannon-es) tuned for realistic-but-forgiving lab handling (spills, breakage feedback reinforce careful technique without being punitive)
- Voice command layer (building on Sprint 16 speech spike): "load slide", "increase magnification", "next test" for hands-free lab flow
- Comfort/accessibility settings: seated vs. standing mode, teleport vs. smooth locomotion, motion-sickness mitigation (vignette on movement), full keyboard/mouse fallback for non-headset users (WCAG-aligned per PRD §6)

**Deliverable:** a full order → test → result loop completable entirely inside a VR headset session, with a fully equivalent desktop-mode fallback.

### Sprint 20 — Sensory Realism Layer (Haptics, Spatial Audio, Physically-Based Rendering)
- Spatial audio (Web Audio API positional sound): centrifuge hum, analyzer beeps, ambient lab noise, footsteps — tied to 3D scene position for presence
- Haptic feedback via WebXR controller haptics API where supported (pipette resistance, glass clink, slide click-into-place)
- Lighting/material realism pass: physically-based rendering for glassware, fluids (reagent color/opacity), and stained slide materials so results *look* clinically correct, not just numerically correct (e.g., anemia case renders visibly pale film)
- Procedural variation layer so repeated cases don't visually reuse identical assets (subtle stain/lighting/specimen variation per generated case)

**Deliverable:** the VR/AR experience is sensorially distinct per case — sound, light, and material response reinforce what the data says, closing the loop between AI-generated results and what the student perceives.

### Sprint 21 — Collaborative & Multiplayer VR Labs
- Multi-user WebXR session support (shared room state via WebSocket, avatar representation, hand/head position sync)
- Lecturer-led VR classroom mode: lecturer avatar can spawn a case, point at slide regions, broadcast annotations into every connected student's view
- Peer lab-partner mode: two students collaboratively order tests/interpret one case (mirrors real bench-partner workflows); score attribution keeps individual accountability
- Backend: session/presence service (Redis pub/sub, reusing the existing ARQ/Redis infra rather than introducing a new stack) for room membership and low-latency state sync

**Deliverable:** a lecturer can run a live shared VR practical session with a full cohort, each seeing synced avatars and shared slide focus.

### Sprint 22 — Embodied AI Tutor (Spatial Avatar + Voice)
- 3D avatar for the existing grounded AI Tutor (Sprint 5/13 logic — no new generative scope, same guardrails) with lip-sync and simple gesture-pointing at relevant slide regions/values
- Text-to-speech narration of tutor feedback, spatialized so the avatar "speaks" from its position in the scene
- Gaze/point-based Q&A trigger ("look at" a flagged region to hear the explanation) layered on the existing grounded Q&A guardrails from Sprint 13 — strictly no open-domain chat capability added

**Deliverable:** the AI Tutor becomes a visible, audible presence in the lab scene rather than a text panel, while remaining bounded to the same case-grounded explanation engine.

### Sprint 23 — Performance Tiering, Accessibility & Low-Resource Fallback Hardening
- Formal Tier 0/1/2/3 device-detection and graceful-degradation test matrix (low-end Android, mid-tier phone, desktop no-headset, Quest-class headset)
- Cloud/remote-rendering fallback spike for institutions with shared low-end lab computers but a good campus network (stream a rendered VR/AR session rather than render locally) — evaluated strictly as **optional**, not required for the product to function, to protect the $0–$25/month infra target from PRD §6
- Accessibility pass in XR: captioning for all spatial audio/tutor speech, colorblind-safe stain/result palettes, full non-VR keyboard/screen-reader equivalents for every VR-exclusive interaction
- Full regression + load test across all four tiers; asset bundle-size and frame-time budgets enforced in CI (extends the Sprint 17 CI check into a hard gate)

**Deliverable:** confidence that no student is blocked or degraded below the Phase 1–3 experience by the existence of the XR layer; documented minimum/recommended device spec sheet for institutions.

### Sprint 24 — XR Practical Exam Mode & Institutional Pilot
- Deterministic-seed VR/AR practical exam mode (mirrors Sprint 2's seeded case generation) so lecturers can run standardized, reproducible immersive practical exams
- Proctoring-lite signals for lecturers (session replay of key actions/timings, not biometric surveillance) surfaced in the existing Lecturer Dashboard (Sprint 6/11)
- Hardware pilot plan: shared low-cost headset cart (e.g. Quest-class devices) sized for one department, cost model added to `docs/PRD.md` §6 non-functional targets, partnership outreach for a pilot cohort
- End-to-end regression across the full stack (Phase 1–4), deploy XR-enabled build behind a feature flag so Tier 0 users see zero change until opted in

**Deliverable:** LaboraX can run a fully immersive, standardized VR/AR practical exam for a pilot cohort, with the core low-resource product completely unaffected for everyone else.

---

## Cross-Sprint (Ongoing Every Sprint)
- CI must stay green: ruff, mypy, pytest (backend); ESLint, Prettier, tsc (frontend)
- Alembic migration review on every schema change
- Update `docs/` (PRD/HLD/LLD) when scope materially changes
- Keep infra within free-tier budget; flag before any paid-tier dependency is introduced
- **From Sprint 17 onward:** enforce the 3D/XR asset performance budget (bundle size, draw calls, frame time) in CI; every XR feature ships with an equivalent Tier 0/1 fallback in the same PR, never as a follow-up
- **From Sprint 17 onward:** any new XR interaction must have a documented keyboard/screen-reader/non-headset equivalent before merge (WCAG 2.1 AA target per `PRD.md` §6 applies to XR surfaces too)

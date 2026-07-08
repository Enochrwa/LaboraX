# LaboraX — Product Requirements Document (PRD v1.0)

## 1. Vision

LaboraX is a virtual laboratory practical simulator that lets health science students receive simulated patient cases, choose and run laboratory tests, review AI-generated realistic results, write interpretations, and get instant AI-driven feedback — with zero reagent cost and unlimited repeatability. It is the "flight simulator" for laboratory science education, purpose-built for institutions with limited practical resources, starting in Rwanda and expanding across Africa.

Independent research on virtual simulation platforms in clinical microbiology and biochemistry education supports this approach: randomized studies of web-based lab simulation report that structured virtual practice with real-time feedback and automated assessment improves operational accuracy and produces measurable, personalized learning curves compared with traditional teaching alone, while reducing consumable and equipment costs.

## 2. Problem Statement

Health science programs — especially in resource-constrained regions — cannot give every student enough hands-on time with real specimens, reagents, and instruments. This creates:

- Inconsistent practical exposure across students and cohorts
- High per-session costs from consumed reagents and damaged equipment
- Limited practical assessment standardization
- No way to practice outside scheduled lab sessions
- Bottlenecks when cohort size scales faster than lab capacity

## 3. Target Users

| User | Needs |
|---|---|
| **Students** (Biomedical Lab Science, Medicine, Nursing, Pharmacy, Public Health, Biotechnology) | Repeatable practice, instant feedback, self-paced learning, exam prep |
| **Lecturers** | Create/assign practical exams, monitor performance, identify weak topics, standardize grading |
| **Institutions** | Increase practical exposure without new lab investment, reduce reagent spend, support large cohorts, generate outcome data for accreditation |

## 4. Product Scope by Phase

### Phase 1 — MVP (Hematology Simulator, ~2–3 months)
- Virtual patient case generator (Hematology only: CBC, Blood Film, Anemia, Malaria)
- Test ordering workflow with cost/resource-penalty feedback for unnecessary tests
- Realistic lab result generation (CBC values, differential count, blood film findings)
- Free-text interpretation submission + AI evaluation against expected findings
- AI tutor explanation for correct/missing findings
- Student scoring and case history
- Lecturer dashboard: case assignment, class performance overview
- Auth + role-based access (Student, Lecturer, Admin)

### Phase 2 — Expansion
- Clinical Chemistry module (LFTs, RFTs, electrolytes, result-pattern prediction)
- Microbiology module (culture/sensitivity scenarios, organism identification)
- Parasitology module (stool/blood parasite identification cases)
- Personalized recommendation engine (weak-topic-based case suggestions)
- Expanded lecturer analytics (cohort trends, item-level difficulty analysis)

### Phase 3 — Advanced
- Molecular Biology and Histopathology modules
- Conversational AI tutor (deeper explanations, follow-up Q&A)
- Virtual microscopy with image-based parasite/cell/organism recognition (CV models)
- Mobile app (React Native)
- Speech-based case discussion evaluation

## 5. Core Feature Requirements (MVP Detail)

### 5.1 Case Generator
- Generates unlimited unique patient scenarios from a disease/symptom/lab-pattern knowledge base
- Configurable difficulty levels (novice → advanced)
- Deterministic seeding for lecturer-assigned exam cases (reproducible for grading)

### 5.2 Test Ordering
- Student selects from available test panel
- System tracks appropriateness of ordered tests vs. clinical presentation
- Unnecessary/irrelevant test orders incur a simulated cost penalty, reinforcing real-world stewardship

### 5.3 Result Generation
- Generates internally consistent lab values tied to the underlying case pathology (e.g., malaria → ↓Hb, ↓platelets, ring-form parasites on film)
- Supports numeric, categorical, and descriptive/image-simulation result types

### 5.4 AI Interpretation Evaluation
- Free-text student interpretation compared against an expected-findings reference using semantic similarity (not exact string match)
- Partial credit for partially correct interpretations
- Structured feedback: confirmed findings, missed findings, incorrect findings

### 5.5 AI Tutor Feedback
- Explains *why* an interpretation is correct/incorrect using domain rules tied to the case pathology
- Not a general-purpose chatbot — grounded in the case's structured clinical/lab data

### 5.6 Scoring & Progress Tracking
- Per-case score, per-topic mastery tracking (e.g., Hematology 85%, Microbiology 52%)
- Personalized recommended next cases based on weak areas

### 5.7 Lecturer Tools
- Create/assign case sets and practical exams
- View class-wide and per-student performance
- Identify commonly-missed findings across a cohort

## 6. Non-Functional Requirements

- **Cost:** Must run on free/low-cost infrastructure tiers at MVP scale (target: $0–$25/month infra cost for pilot cohort)
- **Performance:** CPU-only ML inference; case generation and evaluation responses within 2–3 seconds
- **Scalability:** Support 1,000+ concurrent students practicing simultaneously without reagent/hardware constraints
- **Availability:** Practice available anytime, not limited to scheduled lab sessions
- **Localization:** UI supports English, French, and Kinyarwanda
- **Accessibility:** WCAG 2.1 AA target for core flows
- **Data integrity:** Case generation must remain clinically internally-consistent (no contradictory lab patterns)

## 7. Out of Scope (MVP)

- Real diagnostic use (this is an educational simulator only — not a clinical decision support tool)
- Full LLM-based open-ended chat tutor (deferred to Phase 3, and even then grounded/constrained)
- Native mobile apps (deferred to Phase 3)
- Payment/monetization flows (deferred until product-market fit is validated)

## 8. Success Metrics

| Metric | MVP Target |
|---|---|
| Active pilot students | 100+ within first university partnership |
| Cases completed per student/week | 3+ |
| Interpretation-evaluation accuracy vs. lecturer grading (spot-check) | ≥85% agreement |
| Lecturer-reported time saved on grading | ≥30% |
| Infra cost at pilot scale | $0–$25/month |

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| AI-generated cases become clinically inconsistent | Rule-constrained generation (disease → symptom/lab-pattern templates), lecturer review queue |
| Semantic similarity scoring misgrades edge-case answers | Human-in-the-loop grading override for lecturers; confidence threshold flags for manual review |
| Free-tier infra limits under real load | Modular scaling plan (documented in HLD); caching via Redis; async workers for heavy generation tasks |
| Low institutional trust without clinical accreditation | Position explicitly as an educational supplement, not a diagnostic tool; partner with faculty early |

## 10. Competitive / Market Context

Virtual simulation in medical and lab education is an active, evidence-backed field — recent randomized trials of web-based microbiology lab simulation across multiple specialties and flipped-classroom biochemistry simulation platforms report measurable gains in operational accuracy, biosafety awareness, and personalized learning outcomes versus traditional-only teaching. Most existing platforms are institution-licensed, hardware/VR-heavy, or region-specific (e.g., North America/China-focused). LaboraX's differentiation is a **lightweight, free-tier-first, text/data-driven simulator** purpose-built for African biomedical laboratory science programs, with a growth path into VR/CV-based microscopy later rather than as a hardware-dependent starting requirement.

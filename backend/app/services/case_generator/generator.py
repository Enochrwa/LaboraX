"""`CaseGenerator` — template + rule-constrained virtual patient case generator.

Given a `Disease` template (symptom pattern + difficulty parameters), produces
a unique, internally-consistent patient case: demographics, chief complaint,
clinical history, and a structured "doctor's request" payload (presenting
symptoms + vitals) for the frontend case-intake view.

Deterministic when a `seed` is supplied: the same `(disease, difficulty, seed)`
triple always yields the exact same case. This is what lets a lecturer
re-issue an identical case to every student for a standardized practical exam
(see `docs/SPRINT_PLAN.md` Sprint 24), without needing any special-cased "exam
mode" in the generation algorithm itself.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from typing import Any

from app.db.models.disease import Disease


class CaseGeneratorError(Exception):
    """Raised when a case cannot be generated from the available templates."""


@dataclass(frozen=True, slots=True)
class GeneratedCase:
    """Transport-independent output of `CaseGenerator.generate`.

    Deliberately plain (not a Pydantic/ORM model) so the service layer stays
    reusable by API routes, ARQ background workers, and tests alike, per
    `docs/LLD.md` §1 (services independent of transport).
    """

    patient_pseudo_id: str
    age: int
    sex: str
    clinical_history: str
    doctor_request: dict[str, Any]
    difficulty: str
    seed: int


_MIN_ADULT_AGE = 5
_MAX_ADULT_AGE = 80
_SEX_OPTIONS = ("male", "female")


class CaseGenerator:
    """Deterministic, template-based generator for Phase 1 (Hematology) cases.

    Usage::

        generator = CaseGenerator(diseases)
        disease, case = generator.generate(difficulty="novice", seed=42)
    """

    def __init__(self, diseases: list[Disease]) -> None:
        if not diseases:
            raise CaseGeneratorError(
                "At least one disease template is required to generate a case."
            )
        self._diseases = list(diseases)

    def generate(
        self,
        *,
        category: str | None = None,
        disease_name: str | None = None,
        difficulty: str = "novice",
        seed: int | None = None,
    ) -> tuple[Disease, GeneratedCase]:
        """Generate a case. Deterministic if `seed` is provided.

        Raises `CaseGeneratorError` if no disease template matches the given
        `category`/`disease_name` filters, or if the disease has no template
        defined for the requested `difficulty`.
        """
        resolved_seed = seed if seed is not None else random.SystemRandom().randint(0, 2**31 - 1)
        rng = random.Random(resolved_seed)

        disease = self._select_disease(rng, category=category, disease_name=disease_name)
        difficulty_params = disease.difficulty_levels.get(difficulty)
        if difficulty_params is None:
            available = ", ".join(sorted(disease.difficulty_levels))
            raise CaseGeneratorError(
                f"Disease '{disease.name}' has no '{difficulty}' difficulty template "
                f"(available: {available})."
            )

        case = GeneratedCase(
            patient_pseudo_id=self._build_patient_pseudo_id(rng),
            age=rng.randint(_MIN_ADULT_AGE, _MAX_ADULT_AGE),
            sex=rng.choice(_SEX_OPTIONS),
            clinical_history="",  # filled in below, needs age/sex/duration first
            doctor_request={},
            difficulty=difficulty,
            seed=resolved_seed,
        )

        template = disease.symptom_template
        duration_low, duration_high = template.get("duration_days", [1, 7])
        duration_days = rng.randint(int(duration_low), int(duration_high))

        symptoms = self._select_symptoms(rng, template, difficulty_params)
        vitals = self._roll_vitals(rng, template.get("vitals", {}))
        chief_complaint = str(template.get("chief_complaint", "")).format(
            duration_days=duration_days
        )

        clinical_history = self._build_clinical_history(
            age=case.age,
            sex=case.sex,
            chief_complaint=chief_complaint,
            duration_days=duration_days,
            symptoms=symptoms,
        )

        doctor_request = {
            "chief_complaint": chief_complaint,
            "duration_days": duration_days,
            "presenting_symptoms": symptoms,
            "vitals": vitals,
        }

        case = GeneratedCase(
            patient_pseudo_id=case.patient_pseudo_id,
            age=case.age,
            sex=case.sex,
            clinical_history=clinical_history,
            doctor_request=doctor_request,
            difficulty=difficulty,
            seed=resolved_seed,
        )
        return disease, case

    def _select_disease(
        self, rng: random.Random, *, category: str | None, disease_name: str | None
    ) -> Disease:
        candidates = self._diseases
        if disease_name is not None:
            candidates = [d for d in candidates if d.name.lower() == disease_name.lower()]
            if not candidates:
                raise CaseGeneratorError(f"No disease template found named '{disease_name}'.")
        elif category is not None:
            candidates = [d for d in candidates if d.category.value == category]
            if not candidates:
                raise CaseGeneratorError(f"No disease templates found for category '{category}'.")

        # Sort for deterministic ordering before sampling, so `rng.choice` is
        # reproducible regardless of DB row order.
        ordered = sorted(candidates, key=lambda d: d.name)
        return rng.choice(ordered)

    @staticmethod
    def _select_symptoms(
        rng: random.Random, template: dict[str, Any], difficulty_params: dict[str, Any]
    ) -> list[str]:
        required: list[str] = list(template.get("required", []))
        optional: list[str] = list(template.get("optional", []))

        symptom_count = int(difficulty_params.get("symptom_count", len(required)))
        noise_count = int(difficulty_params.get("noise_symptom_count", 0))

        extra_needed = max(0, symptom_count - len(required))
        extra_pool = sorted(optional)
        rng.shuffle(extra_pool)
        extra_symptoms = extra_pool[:extra_needed]

        # "Noise" symptoms are additional optional symptoms beyond what's
        # needed to hit symptom_count — they widen the differential without
        # being required for a correct interpretation (used at higher
        # difficulty to make the case less obviously templated).
        remaining_pool = extra_pool[extra_needed:]
        noise_symptoms = remaining_pool[:noise_count]

        symptoms = sorted(required) + extra_symptoms + noise_symptoms
        # De-duplicate while preserving order (required symptoms take priority).
        seen: set[str] = set()
        deduped = []
        for symptom in symptoms:
            if symptom not in seen:
                seen.add(symptom)
                deduped.append(symptom)
        return deduped

    @staticmethod
    def _roll_vitals(rng: random.Random, vitals_template: dict[str, Any]) -> dict[str, float]:
        vitals: dict[str, float] = {}
        for key, bounds in vitals_template.items():
            low, high = float(bounds[0]), float(bounds[1])
            vitals[key] = round(rng.uniform(low, high), 1)
        return vitals

    @staticmethod
    def _build_patient_pseudo_id(rng: random.Random) -> str:
        return f"PT-{rng.randint(100000, 999999)}"

    @staticmethod
    def _build_clinical_history(
        *, age: int, sex: str, chief_complaint: str, duration_days: int, symptoms: list[str]
    ) -> str:
        pronoun = "He" if sex == "male" else "She"
        symptom_list = ", ".join(symptoms) if symptoms else "no additional symptoms reported"
        return (
            f"A {age}-year-old {sex} patient presents with {chief_complaint}. "
            f"{pronoun} reports the following: {symptom_list}. "
            f"Symptom duration: {duration_days} day(s)."
        )


def random_generation_id() -> str:
    """Utility for callers that want a display-safe generation correlation id."""
    return uuid.uuid4().hex[:12]

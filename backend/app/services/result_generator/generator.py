"""`ResultGenerator` — deterministic lab result generation tied to case pathology.

Given a `Disease` template (its `lab_pattern_template`) and the ordered
`TestCatalog` entry, produces the JSON `result_payload` persisted on the
`Result` row. Deterministic given `(case_seed, test.code)`: the same case
always yields the same result for the same test, regardless of how many
times it's re-fetched, and lecturer-assigned exam cases reproduce
identical results for every student (mirrors `CaseGenerator`'s seeding
approach, see `docs/SPRINT_PLAN.md` Sprint 3 and Sprint 24).

Two result shapes:

- **Blood film tests** (`relevance_rules.requires_pattern ==
  "blood_film_findings"`): a list of morphological findings straight from
  the disease's `lab_pattern_template`, or a normal/no-abnormality message
  if the disease defines none.
- **Numeric panel tests** (CBC, Reticulocyte Count, Ferritin, CRP, LFT,
  Urinalysis, ...): one sampled value + flag (`low`/`normal`/`high`) per
  parameter in `relevance_rules.measured_parameters`. A parameter shifted
  by the disease's `cbc_deltas` is sampled around that shift; anything
  else is sampled within the plain reference range — so ordering an
  irrelevant test still returns a (usually unremarkable) result, exactly
  as it would in practice.
"""

from __future__ import annotations

import random
from typing import Any

from app.db.models.disease import Disease
from app.db.models.test_catalog import TestCatalog
from app.services.result_generator.reference_ranges import (
    CBC_PANEL_PARAMETERS,
    get_reference_range,
)

_NO_ABNORMALITY_MESSAGE = "No significant morphological abnormalities noted."


class ResultGenerator:
    """Stateless generator — safe to share a single instance across requests."""

    def generate(
        self,
        *,
        disease: Disease,
        test: TestCatalog,
        case_seed: int,
        patient_sex: str,
    ) -> dict[str, Any]:
        rng = random.Random(f"{case_seed}:{test.code}")
        rules = test.relevance_rules

        if rules.get("requires_pattern") == "blood_film_findings":
            return self._generate_blood_film(disease)

        measured_parameters: list[str] = list(rules.get("measured_parameters") or [])
        if not measured_parameters:
            measured_parameters = list(CBC_PANEL_PARAMETERS)

        values: dict[str, float] = {}
        flags: dict[str, str] = {}
        for parameter in measured_parameters:
            value, flag = self._sample_value(parameter, disease, patient_sex, rng)
            values[parameter] = value
            flags[parameter] = flag

        return {"values": values, "flags": flags}

    @staticmethod
    def _generate_blood_film(disease: Disease) -> dict[str, Any]:
        findings = list(disease.lab_pattern_template.get("blood_film_findings", []))
        if findings:
            return {"findings": findings, "flag": "abnormal"}
        return {"findings": [_NO_ABNORMALITY_MESSAGE], "flag": "normal"}

    @staticmethod
    def _sample_value(
        parameter: str, disease: Disease, sex: str, rng: random.Random
    ) -> tuple[float, str]:
        low, high = get_reference_range(parameter, sex)
        baseline_mid = (low + high) / 2

        delta_bounds = disease.lab_pattern_template.get("cbc_deltas", {}).get(parameter)
        if delta_bounds is not None:
            delta = rng.uniform(float(delta_bounds[0]), float(delta_bounds[1]))
            value = baseline_mid + delta
        else:
            value = rng.uniform(low, high)

        value = round(value, 1)
        if value < low:
            flag = "low"
        elif value > high:
            flag = "high"
        else:
            flag = "normal"
        return value, flag

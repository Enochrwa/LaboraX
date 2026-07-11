"""Test relevance rules + cost-penalty logic (`docs/SPRINT_PLAN.md` Sprint 3).

Deliberately data-driven rather than hardcoding disease names: a test is
considered clinically appropriate for a case's disease when either

- its `relevance_rules` are marked `"core"` (a foundational test, always
  appropriate — e.g. a Complete Blood Count), or
- its `relevance_rules["requires_pattern"]` names a key that is present
  (and non-empty) on the disease's `lab_pattern_template` (e.g. a
  Peripheral Blood Film is appropriate whenever the disease defines any
  `blood_film_findings`), or
- any of its `relevance_rules["measured_parameters"]` overlaps with the
  keys defined in the disease's `lab_pattern_template["cbc_deltas"]`
  (e.g. a Reticulocyte Count is appropriate only for diseases whose
  pattern actually shifts `reticulocyte_pct`).

Ordering an inappropriate test still returns a result (see
`app.services.result_generator`) — it just isn't diagnostically useful,
and incurs a simulated cost penalty equal to the test's `cost_weight`,
reinforcing real-world test-ordering stewardship per `docs/PRD.md` §5.2.
"""

from __future__ import annotations

from app.db.models.disease import Disease
from app.db.models.test_catalog import TestCatalog


def evaluate_relevance(test: TestCatalog, disease: Disease) -> tuple[bool, float]:
    """Return `(is_appropriate, penalty_applied)` for ordering `test` given `disease`."""
    rules = test.relevance_rules

    if rules.get("core"):
        return True, 0.0

    lab_pattern = disease.lab_pattern_template

    required_pattern = rules.get("requires_pattern")
    if required_pattern is not None:
        is_appropriate = bool(lab_pattern.get(required_pattern))
    else:
        measured_parameters: list[str] = rules.get("measured_parameters", [])
        cbc_deltas: dict[str, object] = lab_pattern.get("cbc_deltas", {})
        is_appropriate = bool(measured_parameters) and any(
            parameter in cbc_deltas for parameter in measured_parameters
        )

    penalty_applied = 0.0 if is_appropriate else float(test.cost_weight)
    return is_appropriate, penalty_applied

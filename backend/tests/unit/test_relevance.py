"""Unit tests for `app.services.test_ordering.relevance.evaluate_relevance`."""

from __future__ import annotations

from app.db.models.disease import Disease, DiseaseCategory
from app.db.models.test_catalog import TestCatalog
from app.services.test_ordering.relevance import evaluate_relevance


def _disease(**lab_pattern_overrides: object) -> Disease:
    lab_pattern_template: dict[str, object] = {
        "expected_findings": [],
        "cbc_deltas": {"hemoglobin_g_dl": [-6.0, -2.0]},
        "blood_film_findings": ["ring-form trophozoites"],
    }
    lab_pattern_template.update(lab_pattern_overrides)
    return Disease(
        name="Test Disease",
        category=DiseaseCategory.HEMATOLOGY,
        symptom_template={},
        lab_pattern_template=lab_pattern_template,
        difficulty_levels={},
    )


def _test(**relevance_rules: object) -> TestCatalog:
    return TestCatalog(
        code="X",
        name="Test",
        category=DiseaseCategory.HEMATOLOGY,
        cost_weight=2.0,
        relevance_rules=relevance_rules,
    )


def test_core_test_is_always_appropriate_and_free() -> None:
    test = _test(core=True)
    disease = _disease(cbc_deltas={})

    is_appropriate, penalty = evaluate_relevance(test, disease)

    assert is_appropriate is True
    assert penalty == 0.0


def test_requires_pattern_appropriate_when_pattern_present() -> None:
    test = _test(requires_pattern="blood_film_findings")
    disease = _disease(blood_film_findings=["microcytosis"])

    is_appropriate, penalty = evaluate_relevance(test, disease)

    assert is_appropriate is True
    assert penalty == 0.0


def test_requires_pattern_inappropriate_when_pattern_missing_or_empty() -> None:
    test = _test(requires_pattern="blood_film_findings")
    disease = _disease(blood_film_findings=[])

    is_appropriate, penalty = evaluate_relevance(test, disease)

    assert is_appropriate is False
    assert penalty == test.cost_weight


def test_measured_parameters_appropriate_when_overlap_exists() -> None:
    test = _test(measured_parameters=["hemoglobin_g_dl", "reticulocyte_pct"])
    disease = _disease(cbc_deltas={"hemoglobin_g_dl": [-6.0, -2.0]})

    is_appropriate, penalty = evaluate_relevance(test, disease)

    assert is_appropriate is True
    assert penalty == 0.0


def test_measured_parameters_inappropriate_when_no_overlap() -> None:
    test = _test(measured_parameters=["alt_u_l", "ast_u_l"])
    disease = _disease(cbc_deltas={"hemoglobin_g_dl": [-6.0, -2.0]})

    is_appropriate, penalty = evaluate_relevance(test, disease)

    assert is_appropriate is False
    assert penalty == test.cost_weight


def test_no_measured_parameters_and_no_required_pattern_is_inappropriate() -> None:
    test = _test()
    disease = _disease()

    is_appropriate, penalty = evaluate_relevance(test, disease)

    assert is_appropriate is False
    assert penalty == test.cost_weight

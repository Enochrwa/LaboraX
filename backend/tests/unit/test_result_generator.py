"""Unit tests for `app.services.result_generator.generator.ResultGenerator`.

Constructs `Disease`/`TestCatalog` ORM instances in-memory (never
persisted), per `docs/LLD.md` §8 ("each service tested in isolation with
fixed seeds/fixtures").
"""

from __future__ import annotations

from app.db.models.disease import Disease, DiseaseCategory
from app.db.models.test_catalog import TestCatalog
from app.services.result_generator.generator import ResultGenerator
from app.services.result_generator.reference_ranges import get_reference_range


def _malaria() -> Disease:
    return Disease(
        name="Malaria",
        category=DiseaseCategory.HEMATOLOGY,
        symptom_template={},
        lab_pattern_template={
            "expected_findings": [],
            "cbc_deltas": {
                "hemoglobin_g_dl": [-6.0, -2.0],
                "platelets_10e9_l": [-160.0, -60.0],
                "wbc_10e9_l": [-2.0, 0.5],
                "reticulocyte_pct": [1.0, 3.5],
            },
            "blood_film_findings": ["ring-form trophozoites", "occasional gametocytes"],
        },
        difficulty_levels={},
    )


def _no_findings_disease() -> Disease:
    return Disease(
        name="Asymptomatic Carrier",
        category=DiseaseCategory.HEMATOLOGY,
        symptom_template={},
        lab_pattern_template={"expected_findings": [], "cbc_deltas": {}, "blood_film_findings": []},
        difficulty_levels={},
    )


def _cbc_test() -> TestCatalog:
    return TestCatalog(
        code="CBC",
        name="Complete Blood Count",
        category=DiseaseCategory.HEMATOLOGY,
        cost_weight=1.0,
        relevance_rules={
            "core": True,
            "measured_parameters": [
                "hemoglobin_g_dl",
                "wbc_10e9_l",
                "platelets_10e9_l",
                "mcv_fl",
                "mch_pg",
                "rdw_pct",
                "neutrophil_pct",
            ],
        },
    )


def _blood_film_test() -> TestCatalog:
    return TestCatalog(
        code="PBF",
        name="Peripheral Blood Film",
        category=DiseaseCategory.HEMATOLOGY,
        cost_weight=1.5,
        relevance_rules={"requires_pattern": "blood_film_findings"},
    )


def _reticulocyte_test() -> TestCatalog:
    return TestCatalog(
        code="RETIC",
        name="Reticulocyte Count",
        category=DiseaseCategory.HEMATOLOGY,
        cost_weight=1.0,
        relevance_rules={"measured_parameters": ["reticulocyte_pct"]},
    )


def test_same_seed_and_test_code_are_deterministic() -> None:
    generator = ResultGenerator()
    disease = _malaria()
    test = _cbc_test()

    first = generator.generate(disease=disease, test=test, case_seed=42, patient_sex="male")
    second = generator.generate(disease=disease, test=test, case_seed=42, patient_sex="male")

    assert first == second


def test_different_seeds_produce_different_values() -> None:
    generator = ResultGenerator()
    disease = _malaria()
    test = _cbc_test()

    first = generator.generate(disease=disease, test=test, case_seed=1, patient_sex="male")
    second = generator.generate(disease=disease, test=test, case_seed=2, patient_sex="male")

    assert first != second


def test_cbc_panel_includes_every_measured_parameter() -> None:
    generator = ResultGenerator()
    disease = _malaria()
    test = _cbc_test()

    payload = generator.generate(disease=disease, test=test, case_seed=7, patient_sex="female")

    for parameter in test.relevance_rules["measured_parameters"]:
        assert parameter in payload["values"]
        assert parameter in payload["flags"]
        assert payload["flags"][parameter] in {"low", "normal", "high"}


def test_malaria_hemoglobin_is_flagged_low() -> None:
    generator = ResultGenerator()
    disease = _malaria()
    test = _cbc_test()

    payload = generator.generate(disease=disease, test=test, case_seed=123, patient_sex="male")

    low, _high = get_reference_range("hemoglobin_g_dl", "male")
    assert payload["values"]["hemoglobin_g_dl"] < low
    assert payload["flags"]["hemoglobin_g_dl"] == "low"


def test_blood_film_returns_disease_findings_when_present() -> None:
    generator = ResultGenerator()
    disease = _malaria()
    test = _blood_film_test()

    payload = generator.generate(disease=disease, test=test, case_seed=5, patient_sex="male")

    assert payload["findings"] == ["ring-form trophozoites", "occasional gametocytes"]
    assert payload["flag"] == "abnormal"


def test_blood_film_returns_normal_message_when_disease_has_no_findings() -> None:
    generator = ResultGenerator()
    disease = _no_findings_disease()
    test = _blood_film_test()

    payload = generator.generate(disease=disease, test=test, case_seed=5, patient_sex="male")

    assert payload["flag"] == "normal"
    assert payload["findings"] == ["No significant morphological abnormalities noted."]


def test_irrelevant_test_still_returns_a_value_within_or_near_normal_range() -> None:
    """Ordering an inappropriate test (no matching disease pattern) still
    returns a result — it just isn't diagnostically useful, matching the
    cost-penalty stewardship principle from `docs/PRD.md` §5.2."""
    generator = ResultGenerator()
    disease = _no_findings_disease()
    test = _reticulocyte_test()

    payload = generator.generate(disease=disease, test=test, case_seed=9, patient_sex="male")

    low, high = get_reference_range("reticulocyte_pct", "male")
    assert low <= payload["values"]["reticulocyte_pct"] <= high
    assert payload["flags"]["reticulocyte_pct"] == "normal"


def test_reticulocyte_elevated_for_malaria() -> None:
    generator = ResultGenerator()
    disease = _malaria()
    test = _reticulocyte_test()

    payload = generator.generate(disease=disease, test=test, case_seed=11, patient_sex="male")

    _low, high = get_reference_range("reticulocyte_pct", "male")
    assert payload["values"]["reticulocyte_pct"] > high
    assert payload["flags"]["reticulocyte_pct"] == "high"

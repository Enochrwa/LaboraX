"""Unit tests for `app.services.case_generator.generator.CaseGenerator`.

Constructs `Disease` ORM instances in-memory (never persisted) so this suite
tests the generation algorithm in isolation, per `docs/LLD.md` §8 ("each
service tested in isolation with fixed seeds/fixtures").
"""

from __future__ import annotations

import pytest

from app.db.models.disease import Disease, DiseaseCategory
from app.services.case_generator.generator import CaseGenerator, CaseGeneratorError
from app.services.case_generator.seed_data import load_disease_seed_definitions


def _disease_from_definition(definition: dict) -> Disease:
    return Disease(
        name=definition["name"],
        category=DiseaseCategory(definition["category"]),
        symptom_template=definition["symptom_template"],
        lab_pattern_template=definition["lab_pattern_template"],
        difficulty_levels=definition["difficulty_levels"],
    )


@pytest.fixture
def hematology_diseases() -> list[Disease]:
    definitions = load_disease_seed_definitions()
    assert definitions, "expected at least one seed definition to be bundled"
    return [_disease_from_definition(d) for d in definitions]


@pytest.fixture
def malaria(hematology_diseases: list[Disease]) -> Disease:
    return next(d for d in hematology_diseases if d.name == "Malaria")


def test_generate_requires_at_least_one_disease() -> None:
    with pytest.raises(CaseGeneratorError):
        CaseGenerator([])


def test_same_seed_produces_an_identical_case(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])

    _, case_a = generator.generate(difficulty="novice", seed=1234)
    _, case_b = generator.generate(difficulty="novice", seed=1234)

    assert case_a == case_b


def test_different_seeds_produce_different_cases(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])

    _, case_a = generator.generate(difficulty="novice", seed=1)
    _, case_b = generator.generate(difficulty="novice", seed=2)

    assert case_a != case_b


def test_omitting_seed_still_returns_a_reproducible_seed_value(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])
    disease, case = generator.generate(difficulty="novice", seed=None)

    assert isinstance(case.seed, int)
    # The returned seed must itself be replayable.
    _, replayed = generator.generate(difficulty="novice", seed=case.seed)
    assert replayed == case
    assert disease.name == "Malaria"


def test_generated_case_includes_all_required_symptoms(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])
    _, case = generator.generate(difficulty="novice", seed=42)

    required = set(malaria.symptom_template["required"])
    presenting = set(case.doctor_request["presenting_symptoms"])
    assert required.issubset(presenting)


def test_higher_difficulty_yields_more_symptoms(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])

    _, novice_case = generator.generate(difficulty="novice", seed=7)
    _, advanced_case = generator.generate(difficulty="advanced", seed=7)

    novice_count = len(novice_case.doctor_request["presenting_symptoms"])
    advanced_count = len(advanced_case.doctor_request["presenting_symptoms"])
    assert advanced_count >= novice_count


def test_generate_rejects_unknown_difficulty(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])
    with pytest.raises(CaseGeneratorError):
        generator.generate(difficulty="expert-mode", seed=1)


def test_generate_filters_by_category(hematology_diseases: list[Disease]) -> None:
    generator = CaseGenerator(hematology_diseases)
    disease, _ = generator.generate(category="hematology", difficulty="novice", seed=1)
    assert disease.category == DiseaseCategory.HEMATOLOGY


def test_generate_rejects_unknown_category(hematology_diseases: list[Disease]) -> None:
    generator = CaseGenerator(hematology_diseases)
    with pytest.raises(CaseGeneratorError):
        generator.generate(category="histopathology", difficulty="novice", seed=1)


def test_generate_by_disease_name(hematology_diseases: list[Disease]) -> None:
    generator = CaseGenerator(hematology_diseases)
    disease, _ = generator.generate(disease_name="Iron Deficiency Anemia", seed=1)
    assert disease.name == "Iron Deficiency Anemia"


def test_generate_rejects_unknown_disease_name(hematology_diseases: list[Disease]) -> None:
    generator = CaseGenerator(hematology_diseases)
    with pytest.raises(CaseGeneratorError):
        generator.generate(disease_name="Scurvy", seed=1)


def test_patient_pseudo_id_is_well_formed(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])
    _, case = generator.generate(difficulty="novice", seed=99)
    assert case.patient_pseudo_id.startswith("PT-")
    assert case.patient_pseudo_id[3:].isdigit()


def test_vitals_are_within_template_bounds(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])
    _, case = generator.generate(difficulty="advanced", seed=17)

    vitals_template = malaria.symptom_template["vitals"]
    vitals = case.doctor_request["vitals"]
    for key, (low, high) in vitals_template.items():
        assert low <= vitals[key] <= high


def test_clinical_history_mentions_age_and_chief_complaint(malaria: Disease) -> None:
    generator = CaseGenerator([malaria])
    _, case = generator.generate(difficulty="novice", seed=3)

    assert str(case.age) in case.clinical_history
    assert case.doctor_request["chief_complaint"] in case.clinical_history

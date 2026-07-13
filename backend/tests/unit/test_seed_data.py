"""Unit tests for `app.services.case_generator.seed_data`."""

from __future__ import annotations

from pathlib import Path

from app.services.case_generator.seed_data import load_disease_seed_definitions


def test_load_disease_seed_definitions_returns_hematology_diseases() -> None:
    definitions = load_disease_seed_definitions()
    names = {d["name"] for d in definitions}

    assert {"Malaria", "Iron Deficiency Anemia", "Generic Bacterial Infection"} <= names


def test_load_disease_seed_definitions_returns_chemistry_diseases() -> None:
    definitions = load_disease_seed_definitions()
    names = {d["name"] for d in definitions}

    assert {
        "Acute Viral Hepatitis",
        "Acute Kidney Injury",
        "Diabetic Ketoacidosis",
    } <= names


def test_every_definition_has_required_shape() -> None:
    definitions = load_disease_seed_definitions()

    for definition in definitions:
        assert definition["category"] in {"hematology", "chemistry"}
        assert "required" in definition["symptom_template"]
        assert "expected_findings" in definition["lab_pattern_template"]
        assert set(definition["difficulty_levels"]) == {"novice", "intermediate", "advanced"}


def test_missing_data_dir_returns_empty_list(tmp_path: Path) -> None:
    assert load_disease_seed_definitions(data_dir=tmp_path) == []

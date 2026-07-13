"""Unit tests for `app.services.test_ordering.catalog_seed_data`."""

from __future__ import annotations

from pathlib import Path

from app.services.test_ordering.catalog_seed_data import load_test_catalog_definitions


def test_load_test_catalog_definitions_returns_expected_codes() -> None:
    definitions = load_test_catalog_definitions()
    codes = {d["code"] for d in definitions}

    assert codes == {
        "CBC",
        "PBF",
        "RETIC",
        "FERRITIN",
        "CRP",
        "LFT",
        "RFT",
        "ELECTROLYTES",
        "GLUCOSE",
        "URINALYSIS",
    }


def test_every_definition_has_required_shape() -> None:
    definitions = load_test_catalog_definitions()

    for definition in definitions:
        assert isinstance(definition["code"], str) and definition["code"]
        assert isinstance(definition["name"], str) and definition["name"]
        assert definition["category"] in {
            "hematology",
            "chemistry",
            "microbiology",
            "parasitology",
        }
        assert isinstance(definition["cost_weight"], (int, float))
        assert isinstance(definition["relevance_rules"], dict)


def test_core_cbc_test_declares_the_full_panel() -> None:
    definitions = load_test_catalog_definitions()
    cbc = next(d for d in definitions if d["code"] == "CBC")

    assert cbc["relevance_rules"]["core"] is True
    assert set(cbc["relevance_rules"]["measured_parameters"]) == {
        "hemoglobin_g_dl",
        "wbc_10e9_l",
        "platelets_10e9_l",
        "mcv_fl",
        "mch_pg",
        "rdw_pct",
        "neutrophil_pct",
    }


def test_missing_data_dir_returns_empty_list(tmp_path: Path) -> None:
    assert load_test_catalog_definitions(data_dir=tmp_path) == []

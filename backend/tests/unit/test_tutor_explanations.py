"""Unit tests for `app.services.tutor.explanations` — Sprint 5's domain
rule-based tutor explanation templates."""

from __future__ import annotations

from app.services.tutor.explanations import (
    DEFAULT_TOPIC,
    explain,
    explain_finding,
    topic_for_parameter,
)


class TestTopicForParameter:
    def test_known_parameter_maps_to_its_topic(self) -> None:
        assert topic_for_parameter("hemoglobin") == "red_cell_indices"
        assert topic_for_parameter("trophozoite") == "parasitology"
        assert topic_for_parameter("crp") == "inflammatory_markers"

    def test_unknown_parameter_falls_back_to_default_topic(self) -> None:
        assert topic_for_parameter("some_future_parameter") == DEFAULT_TOPIC


class TestExplain:
    def test_exact_parameter_polarity_match_returns_specific_explanation(self) -> None:
        result = explain("hemoglobin", "decreased")
        assert result.topic == "red_cell_indices"
        assert "oxygen" in result.explanation.lower()

    def test_polarity_agnostic_parameter_falls_back_to_none_entry(self) -> None:
        result = explain("trophozoite", None)
        assert result.topic == "parasitology"
        assert "malaria" in result.explanation.lower() or "plasmodium" in result.explanation.lower()

    def test_completely_unmapped_combination_returns_generic_explanation(self) -> None:
        result = explain("some_future_parameter", "increased")
        assert result.topic == DEFAULT_TOPIC
        assert result.explanation  # never empty, never raises


class TestExplainFinding:
    def test_extracts_parameter_and_polarity_from_normalized_text(self) -> None:
        result = explain_finding("hemoglobin is decreased consistent with hemolytic anemia")
        assert result is not None
        assert result.topic == "red_cell_indices"

    def test_returns_none_when_no_known_parameter_present(self) -> None:
        assert explain_finding("the weather is nice today") is None

    def test_multi_parameter_statement_picks_deterministic_parameter(self) -> None:
        # "hemoglobin" and "platelets" both present; alphabetically "hemoglobin" wins.
        first = explain_finding("hemoglobin and platelets are both decreased")
        second = explain_finding("platelets and hemoglobin are both decreased")
        assert first == second


class TestSprint7ChemistryTopicsAndExplanations:
    """Sprint 7 (Clinical Chemistry) parameter -> topic + explanation coverage."""

    def test_hepatic_parameters_map_to_hepatic_function_topic(self) -> None:
        assert topic_for_parameter("alt") == "hepatic_function"
        assert topic_for_parameter("ast") == "hepatic_function"
        assert topic_for_parameter("bilirubin") == "hepatic_function"

    def test_renal_parameters_map_to_renal_function_topic(self) -> None:
        assert topic_for_parameter("urea") == "renal_function"
        assert topic_for_parameter("creatinine") == "renal_function"

    def test_electrolyte_parameters_map_to_electrolyte_balance_topic(self) -> None:
        assert topic_for_parameter("sodium") == "electrolyte_balance"
        assert topic_for_parameter("potassium") == "electrolyte_balance"
        assert topic_for_parameter("bicarbonate") == "electrolyte_balance"

    def test_glucose_maps_to_glucose_metabolism_topic(self) -> None:
        assert topic_for_parameter("glucose") == "glucose_metabolism"

    def test_creatinine_explanation_is_specific(self) -> None:
        result = explain("creatinine", "increased")
        assert result.topic == "renal_function"
        assert "kidney" in result.explanation.lower()

    def test_bicarbonate_decreased_explanation_mentions_acidosis(self) -> None:
        result = explain("bicarbonate", "decreased")
        assert "acidosis" in result.explanation.lower()

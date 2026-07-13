"""Unit tests for `app.services.answer_evaluator.preprocessing`."""

from __future__ import annotations

from app.services.answer_evaluator import preprocessing


class TestSplitSentences:
    def test_splits_on_sentence_terminators(self) -> None:
        text = "Hemoglobin is low. Platelets are decreased! What about WBC? Normal."
        assert preprocessing.split_sentences(text) == [
            "Hemoglobin is low.",
            "Platelets are decreased!",
            "What about WBC?",
            "Normal.",
        ]

    def test_splits_on_newlines_and_semicolons(self) -> None:
        text = "Hemoglobin is low\nPlatelets are decreased; WBC is normal"
        result = preprocessing.split_sentences(text)
        assert len(result) == 3

    def test_blank_text_returns_empty_list(self) -> None:
        assert preprocessing.split_sentences("   ") == []
        assert preprocessing.split_sentences("") == []

    def test_collapses_internal_whitespace(self) -> None:
        result = preprocessing.split_sentences("Hemoglobin    is   low.")
        assert result == ["Hemoglobin is low."]


class TestNormalize:
    def test_lowercases(self) -> None:
        assert "hemoglobin" in preprocessing.normalize("HEMOGLOBIN is Low")

    def test_canonicalizes_abbreviations(self) -> None:
        assert preprocessing.normalize("Hb is low") == "hemoglobin is decreased"
        assert preprocessing.normalize("WBC is high") == "wbc is increased"

    def test_canonicalizes_multi_word_phrases(self) -> None:
        assert preprocessing.normalize("total white cell count is elevated") == "wbc is increased"

    def test_canonicalizes_polarity_synonyms(self) -> None:
        assert preprocessing.normalize("platelets are reduced") == "platelets are decreased"
        assert preprocessing.normalize("ferritin is depleted") == "ferritin is decreased"


class TestExtractParameters:
    def test_extracts_known_parameters(self) -> None:
        normalized = preprocessing.normalize("hemoglobin and platelets are decreased")
        assert preprocessing.extract_parameters(normalized) == {"hemoglobin", "platelets"}

    def test_returns_empty_set_for_no_known_parameters(self) -> None:
        normalized = preprocessing.normalize("the patient has a fever")
        assert preprocessing.extract_parameters(normalized) == set()


class TestExtractPolarity:
    def test_extracts_single_polarity(self) -> None:
        normalized = preprocessing.normalize("hemoglobin is decreased")
        assert preprocessing.extract_polarity(normalized) == "decreased"

    def test_returns_none_when_no_polarity_present(self) -> None:
        normalized = preprocessing.normalize("ring-form trophozoites are visible")
        assert preprocessing.extract_polarity(normalized) is None

    def test_returns_none_when_multiple_conflicting_polarities(self) -> None:
        normalized = preprocessing.normalize("hemoglobin is decreased but wbc is increased")
        assert preprocessing.extract_polarity(normalized) is None


class TestSprint7ChemistrySynonyms:
    """Sprint 7 (Clinical Chemistry) parameter/abbreviation vocabulary."""

    def test_canonicalizes_hepatic_abbreviations(self) -> None:
        assert preprocessing.normalize("ALT is elevated") == "alt is increased"
        assert preprocessing.normalize("AST is high") == "ast is increased"
        assert preprocessing.normalize("total bilirubin is raised") == "bilirubin is increased"

    def test_canonicalizes_renal_terms(self) -> None:
        assert preprocessing.normalize("serum urea is increased") == "urea is increased"
        assert preprocessing.normalize("Creatinine is high") == "creatinine is increased"

    def test_canonicalizes_electrolyte_terms(self) -> None:
        assert preprocessing.normalize("sodium is low") == "sodium is decreased"
        assert preprocessing.normalize("potassium is elevated") == "potassium is increased"
        assert preprocessing.normalize("bicarbonate is reduced") == "bicarbonate is decreased"

    def test_canonicalizes_glucose_terms(self) -> None:
        assert preprocessing.normalize("blood glucose is high") == "glucose is increased"

    def test_extracts_chemistry_parameters(self) -> None:
        normalized = preprocessing.normalize("ALT and AST are both increased")
        assert preprocessing.extract_parameters(normalized) == {"alt", "ast"}

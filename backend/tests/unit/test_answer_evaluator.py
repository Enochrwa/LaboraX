"""Unit tests for `AnswerEvaluator` — Sprint 4's core deliverable.

Includes golden-case regression fixtures (`docs/LLD.md` §8: "known case ->
known expected evaluation output within tolerance") so future changes to the
similarity backend or thresholds can't silently regress scoring without a
test failing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.models.disease import Disease, DiseaseCategory
from app.services.answer_evaluator.evaluator import AnswerEvaluator

_DISEASE_DATA_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "ml" / "data" / "hematology_diseases.json"
)
_CHEMISTRY_DISEASE_DATA_PATH = (
    Path(__file__).resolve().parents[2] / "app" / "ml" / "data" / "chemistry_diseases.json"
)


def _load_disease(name: str, *, data_path: Path = _DISEASE_DATA_PATH) -> Disease:
    definitions = json.loads(data_path.read_text())
    definition = next(d for d in definitions if d["name"] == name)
    return Disease(
        name=definition["name"],
        category=DiseaseCategory(definition["category"]),
        symptom_template=definition["symptom_template"],
        lab_pattern_template=definition["lab_pattern_template"],
        difficulty_levels=definition["difficulty_levels"],
    )


@pytest.fixture
def evaluator() -> AnswerEvaluator:
    return AnswerEvaluator()


@pytest.fixture
def malaria() -> Disease:
    return _load_disease("Malaria")


@pytest.fixture
def iron_deficiency_anemia() -> Disease:
    return _load_disease("Iron Deficiency Anemia")


@pytest.fixture
def generic_bacterial_infection() -> Disease:
    return _load_disease("Generic Bacterial Infection")


@pytest.fixture
def acute_viral_hepatitis() -> Disease:
    return _load_disease("Acute Viral Hepatitis", data_path=_CHEMISTRY_DISEASE_DATA_PATH)


@pytest.fixture
def acute_kidney_injury() -> Disease:
    return _load_disease("Acute Kidney Injury", data_path=_CHEMISTRY_DISEASE_DATA_PATH)


@pytest.fixture
def diabetic_ketoacidosis() -> Disease:
    return _load_disease("Diabetic Ketoacidosis", data_path=_CHEMISTRY_DISEASE_DATA_PATH)


# ---------------------------------------------------------------------------
# Golden-case regressions: known (disease, submission) -> known score range.
# ---------------------------------------------------------------------------


class TestGoldenCases:
    def test_malaria_strong_interpretation_scores_highly(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        text = (
            "The hemoglobin is decreased, consistent with a hemolytic anemia. "
            "Platelets are low, showing thrombocytopenia. "
            "The blood film shows ring-form trophozoites. "
            "White cell count is roughly normal. "
            "Reticulocyte count is elevated due to compensatory marrow response."
        )
        result = evaluator.evaluate(disease=malaria, student_text=text)
        assert 60.0 <= result.score <= 100.0
        assert len(result.confirmed_findings) == 5
        assert not result.incorrect_findings

    def test_iron_deficiency_anemia_strong_interpretation_scores_highly(
        self, evaluator: AnswerEvaluator, iron_deficiency_anemia: Disease
    ) -> None:
        text = (
            "Hemoglobin is decreased consistent with microcytic hypochromic anemia. "
            "MCV is decreased showing microcytosis. "
            "MCH is decreased showing hypochromia. "
            "RDW is increased reflecting anisocytosis. "
            "Serum ferritin is decreased confirming depleted iron stores."
        )
        result = evaluator.evaluate(disease=iron_deficiency_anemia, student_text=text)
        assert result.score == pytest.approx(100.0, abs=5.0)
        assert len(result.confirmed_findings) == 5
        assert not result.missing_findings
        assert not result.incorrect_findings

    def test_bacterial_infection_strong_interpretation_scores_highly(
        self, evaluator: AnswerEvaluator, generic_bacterial_infection: Disease
    ) -> None:
        text = (
            "White cell count is elevated showing leukocytosis. "
            "Neutrophil count is elevated with a left shift. "
            "CRP is elevated consistent with acute inflammation. "
            "Hemoglobin and platelet counts are normal."
        )
        result = evaluator.evaluate(disease=generic_bacterial_infection, student_text=text)
        assert result.score == pytest.approx(100.0, abs=5.0)
        assert not result.incorrect_findings

    def test_empty_submission_scores_zero(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        result = evaluator.evaluate(disease=malaria, student_text="   ")
        assert result.score == 0.0
        assert len(result.missing_findings) == 5
        assert not result.confirmed_findings

    def test_irrelevant_submission_scores_near_zero(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        result = evaluator.evaluate(
            disease=malaria, student_text="The weather today is sunny and warm."
        )
        assert result.score <= 10.0

    def test_contradictory_statement_is_flagged_incorrect_and_penalized(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        text = "Hemoglobin is normal. Platelets are increased. The patient has a fever."
        result = evaluator.evaluate(disease=malaria, student_text=text)

        assert len(result.incorrect_findings) == 1
        assert "platelets" in result.incorrect_findings[0].reason.lower()
        # A statement that lexically overlaps a finding but contradicts its
        # polarity must never be credited as confirming that finding.
        confirmed_texts = {f.expected_finding for f in result.confirmed_findings}
        assert "Hemoglobin is decreased, consistent with hemolytic anemia" not in confirmed_texts

    def test_partial_credit_scores_between_missing_and_confirmed(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        # Loosely worded — mentions the right parameters and directions for
        # two of the five findings but is far from a complete, precise
        # restatement, so it should land as partial credit rather than
        # either a full match or a total miss.
        text = "Hemoglobin is low and platelets are low, with an increased reticulocyte count."
        result = evaluator.evaluate(disease=malaria, student_text=text)
        assert 0.0 < result.score < 100.0


# ---------------------------------------------------------------------------
# Algorithm-level behavior (not tied to one golden fixture)
# ---------------------------------------------------------------------------


class TestAnswerEvaluatorBehavior:
    def test_disease_without_expected_findings_returns_neutral_result(
        self, evaluator: AnswerEvaluator
    ) -> None:
        disease = Disease(
            name="Undefined Template",
            category=DiseaseCategory.HEMATOLOGY,
            symptom_template={},
            lab_pattern_template={},
            difficulty_levels={},
        )
        result = evaluator.evaluate(disease=disease, student_text="Anything at all.")
        assert result.score == 0.0
        assert not result.confirmed_findings
        assert not result.missing_findings

    def test_score_is_bounded_between_zero_and_hundred(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        many_wrong_statements = ". ".join(
            [
                "Platelets are increased",
                "White cell count is decreased",
                "Reticulocyte count is decreased",
            ]
        )
        result = evaluator.evaluate(disease=malaria, student_text=many_wrong_statements)
        assert 0.0 <= result.score <= 100.0

    def test_tutor_feedback_is_never_empty(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        for text in ["", "   ", "Hemoglobin is decreased.", "Irrelevant text entirely."]:
            result = evaluator.evaluate(disease=malaria, student_text=text)
            assert result.tutor_feedback


class TestSprint5TutorExplanationsAndTopics:
    """`docs/SPRINT_PLAN.md` Sprint 5: tutor explanation templates + topic scoring."""

    def test_confirmed_findings_carry_topic_and_explanation(
        self, evaluator: AnswerEvaluator, iron_deficiency_anemia: Disease
    ) -> None:
        text = "Hemoglobin is decreased consistent with microcytic hypochromic anemia."
        result = evaluator.evaluate(disease=iron_deficiency_anemia, student_text=text)

        confirmed = next(
            f
            for f in result.confirmed_findings
            if f.expected_finding.startswith("Hemoglobin is decreased")
        )
        assert confirmed.topic == "red_cell_indices"
        assert confirmed.explanation
        assert "oxygen" in confirmed.explanation.lower()

    def test_missing_findings_carry_topic_and_explanation(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        result = evaluator.evaluate(disease=malaria, student_text="The weather is nice today.")
        assert result.missing_findings
        for finding in result.missing_findings:
            assert finding.topic
            assert finding.explanation

    def test_incorrect_statement_carries_topic(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        result = evaluator.evaluate(disease=malaria, student_text="Platelets are increased.")
        assert result.incorrect_findings
        assert result.incorrect_findings[0].topic == "platelet_count"

    def test_topic_scores_cover_every_topic_touched_by_expected_findings(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        text = (
            "The hemoglobin is decreased, consistent with a hemolytic anemia. "
            "Platelets are low, showing thrombocytopenia. "
            "The blood film shows ring-form trophozoites. "
            "White cell count is roughly normal. "
            "Reticulocyte count is elevated due to compensatory marrow response."
        )
        result = evaluator.evaluate(disease=malaria, student_text=text)

        topics = {ts.topic for ts in result.topic_scores}
        assert topics == {
            "red_cell_indices",
            "platelet_count",
            "parasitology",
            "white_cell_response",
            "marrow_response",
        }
        for topic_score in result.topic_scores:
            assert 0.0 <= topic_score.score <= 100.0
            assert topic_score.finding_count >= 1

    def test_topic_score_penalized_by_contradictory_statement_about_that_topic(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        result = evaluator.evaluate(disease=malaria, student_text="Platelets are increased.")
        platelet_topic = next(ts for ts in result.topic_scores if ts.topic == "platelet_count")
        # Missing (0 credit) minus the topic-level incorrect penalty, floored at 0.
        assert platelet_topic.score == 0.0

    def test_empty_submission_still_produces_topic_scores(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        result = evaluator.evaluate(disease=malaria, student_text="")
        assert result.topic_scores
        assert all(ts.score == 0.0 for ts in result.topic_scores)

    def test_tutor_feedback_surfaces_why_the_top_missing_finding_matters(
        self, evaluator: AnswerEvaluator, malaria: Disease
    ) -> None:
        result = evaluator.evaluate(disease=malaria, student_text="Irrelevant text entirely.")
        assert "Why it matters:" in result.tutor_feedback


class TestSprint7ChemistryGoldenCases:
    """Golden-case regressions for Clinical Chemistry disease templates.

    Mirrors `TestGoldenCases` above — same evaluator, same thresholds, only
    the disease/expected-findings data differs, confirming the Sprint 4
    algorithm generalizes to a new department without modification.
    """

    def test_acute_viral_hepatitis_strong_interpretation_scores_highly(
        self, evaluator: AnswerEvaluator, acute_viral_hepatitis: Disease
    ) -> None:
        text = (
            "ALT is markedly increased, consistent with hepatocellular injury. "
            "AST is increased, though to a lesser degree than ALT. "
            "Total bilirubin is increased, consistent with the clinical jaundice. "
            "Hemoglobin and platelet counts remain within normal limits."
        )
        result = evaluator.evaluate(disease=acute_viral_hepatitis, student_text=text)
        assert result.score == pytest.approx(100.0, abs=5.0)
        assert len(result.confirmed_findings) == 4
        assert not result.missing_findings
        assert not result.incorrect_findings

    def test_acute_kidney_injury_strong_interpretation_scores_highly(
        self, evaluator: AnswerEvaluator, acute_kidney_injury: Disease
    ) -> None:
        text = (
            "Serum urea is increased, consistent with reduced renal clearance. "
            "Serum creatinine is increased, confirming impaired kidney function. "
            "Potassium is increased, reflecting reduced renal excretion. "
            "Hemoglobin remains within normal limits."
        )
        result = evaluator.evaluate(disease=acute_kidney_injury, student_text=text)
        assert result.score == pytest.approx(100.0, abs=5.0)
        assert len(result.confirmed_findings) == 4
        assert not result.incorrect_findings

    def test_diabetic_ketoacidosis_strong_interpretation_scores_highly(
        self, evaluator: AnswerEvaluator, diabetic_ketoacidosis: Disease
    ) -> None:
        text = (
            "Blood glucose is markedly increased, consistent with uncontrolled hyperglycemia. "
            "Bicarbonate is decreased, consistent with a metabolic acidosis. "
            "Potassium is increased despite total-body depletion, reflecting the acidosis shift. "
            "Sodium is decreased, consistent with osmotic dilution from hyperglycemia."
        )
        result = evaluator.evaluate(disease=diabetic_ketoacidosis, student_text=text)
        assert result.score == pytest.approx(100.0, abs=5.0)
        assert len(result.confirmed_findings) == 4
        assert not result.incorrect_findings

    def test_contradicting_creatinine_polarity_is_flagged_incorrect(
        self, evaluator: AnswerEvaluator, acute_kidney_injury: Disease
    ) -> None:
        text = "Serum creatinine is decreased. The patient reports leg swelling."
        result = evaluator.evaluate(disease=acute_kidney_injury, student_text=text)

        assert len(result.incorrect_findings) == 1
        assert "creatinine" in result.incorrect_findings[0].reason.lower()
        confirmed_texts = {f.expected_finding for f in result.confirmed_findings}
        assert (
            "Serum creatinine is increased, confirming impaired kidney function"
            not in confirmed_texts
        )

    def test_chemistry_findings_map_to_dedicated_topics(
        self, evaluator: AnswerEvaluator, acute_viral_hepatitis: Disease
    ) -> None:
        text = "ALT is increased. AST is increased. Bilirubin is increased."
        result = evaluator.evaluate(disease=acute_viral_hepatitis, student_text=text)
        topics = {f.topic for f in result.confirmed_findings}
        assert topics <= {"hepatic_function"}

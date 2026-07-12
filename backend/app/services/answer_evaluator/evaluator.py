"""`AnswerEvaluator` — scores a student's free-text interpretation.

Implements `docs/LLD.md` §5's algorithm:

1. Normalize student text (lowercase, canonical domain terms — see
   `preprocessing.normalize`).
2. Split into candidate finding-statements (sentence segmentation).
3. Vectorize each candidate statement and each of the case's
   `expected_findings` and compute a cosine-similarity matrix between them.
4. Match each expected finding to its best-scoring candidate statement.
5. Threshold the best score per expected finding: >= `CONFIRMED_THRESHOLD`
   is confirmed, >= `PARTIAL_THRESHOLD` is partial credit, otherwise missing.
6. Flag candidate statements that reference a known lab parameter with a
   polarity (increased/decreased/normal) opposite to every expected finding
   mentioning that parameter as "incorrect" — the rule-based
   finding-extraction half of `docs/HLD.md` §3.3's "cosine similarity +
   rule-based finding extraction" description.
7. Composite score = weighted sum (confirmed=full weight, partial=half
   weight) normalized to 100, minus a small penalty per incorrect statement,
   floored at 0.
8. Sprint 5: each finding is additionally tagged with a `topic` and a
   rule-based "why this matters" `explanation` via
   `app.services.tutor.explanations`, and a per-topic score breakdown
   (`topic_scores`) is computed so `MasteryTracker` (see
   `app/services/mastery/tracker.py`) can update `student_topic_mastery`
   without re-deriving parameters/topics from the raw findings again.

Similarity backend: TF-IDF (character+word n-grams) + cosine similarity via
scikit-learn, fit fresh on each small evaluation's own statement corpus.
See `preprocessing.py`'s module docstring for why this replaces a
sentence-transformer model. The backend is isolated behind
`_similarity_matrix` precisely so a semantic-embedding backend can be
swapped in later (`docs/HLD.md` §3.2: "wraps model inference behind clean
service interfaces so models can be swapped without touching API code")
without touching the scoring logic below it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import numpy.typing as npt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.db.models.disease import Disease
from app.services.answer_evaluator import preprocessing
from app.services.tutor.explanations import DEFAULT_TOPIC, explain_finding, topic_for_parameter

CONFIRMED_THRESHOLD = 0.45
PARTIAL_THRESHOLD = 0.22
INCORRECT_PENALTY = 5.0

# Per-topic incorrect-statement penalty, smaller than the overall score's
# `INCORRECT_PENALTY` since one contradictory statement about a topic
# shouldn't wipe out that topic's mastery signal the way it dents the
# overall composite score.
_TOPIC_INCORRECT_PENALTY = 25.0


@dataclass
class FindingMatchResult:
    expected_finding: str
    matched_statement: str | None
    similarity: float
    topic: str = DEFAULT_TOPIC
    explanation: str = ""


@dataclass
class IncorrectStatementResult:
    statement: str
    reason: str
    topic: str = DEFAULT_TOPIC


@dataclass
class TopicScore:
    """This submission's performance on one learning topic (0-100 scale).

    Consumed by `MasteryTracker.update_from_evaluation` to blend into the
    student's running `student_topic_mastery` row for `topic` — see
    `app/services/mastery/tracker.py`.
    """

    topic: str
    score: float
    finding_count: int


@dataclass
class EvaluationResult:
    score: float
    confirmed_findings: list[FindingMatchResult] = field(default_factory=list)
    missing_findings: list[FindingMatchResult] = field(default_factory=list)
    incorrect_findings: list[IncorrectStatementResult] = field(default_factory=list)
    tutor_feedback: str = ""
    topic_scores: list[TopicScore] = field(default_factory=list)


def _similarity_matrix(candidates: list[str], expected: list[str]) -> npt.NDArray[np.float64]:
    """Return an `(len(expected), len(candidates))` cosine-similarity matrix.

    Vectorized over word unigrams+bigrams so short paraphrases ("hemoglobin
    is low" vs "hemoglobin decreased") still share n-gram overlap after
    `preprocessing.normalize` has canonicalized both to the same tokens.
    """
    corpus = candidates + expected
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(corpus)
    candidate_vectors = matrix[: len(candidates)]
    expected_vectors = matrix[len(candidates) :]
    similarity: npt.NDArray[np.float64] = cosine_similarity(expected_vectors, candidate_vectors)
    return similarity


def _finding_match(
    *,
    expected_finding: str,
    matched_statement: str | None,
    similarity: float,
    normalized_finding: str | None = None,
) -> FindingMatchResult:
    """Build a `FindingMatchResult`, attaching its Sprint 5 topic + explanation.

    `normalized_finding` lets callers pass an already-normalized string
    (the hot path in `evaluate()` already computed it); when omitted this
    normalizes `expected_finding` itself, which keeps the empty-submission
    fallback path in `evaluate()` — which never runs `preprocessing.normalize`
    over the expected findings — correct too.
    """
    normalized = normalized_finding or preprocessing.normalize(expected_finding)
    explanation = explain_finding(normalized)
    if explanation is None:
        return FindingMatchResult(
            expected_finding=expected_finding,
            matched_statement=matched_statement,
            similarity=similarity,
        )
    return FindingMatchResult(
        expected_finding=expected_finding,
        matched_statement=matched_statement,
        similarity=similarity,
        topic=explanation.topic,
        explanation=explanation.explanation,
    )


def _aggregate_topic_scores(
    *,
    confirmed: list[FindingMatchResult],
    missing: list[FindingMatchResult],
    incorrect: list[IncorrectStatementResult],
) -> list[TopicScore]:
    """Roll confirmed/missing/incorrect findings up into a per-topic 0-100 score.

    Mirrors `evaluate()`'s overall composite-score weighting (confirmed=full
    credit, `PARTIAL_THRESHOLD`-only matches=half credit) but per topic, plus
    a smaller `_TOPIC_INCORRECT_PENALTY` per contradictory statement about
    that specific topic. This is what `MasteryTracker` blends into
    `student_topic_mastery` — see `app/services/mastery/tracker.py`.
    """
    weight_by_topic: dict[str, float] = {}
    count_by_topic: dict[str, int] = {}

    for f in confirmed:
        weight_by_topic[f.topic] = weight_by_topic.get(f.topic, 0.0) + (
            1.0 if f.similarity >= CONFIRMED_THRESHOLD else 0.5
        )
        count_by_topic[f.topic] = count_by_topic.get(f.topic, 0) + 1
    for f in missing:
        count_by_topic[f.topic] = count_by_topic.get(f.topic, 0) + 1

    penalty_by_topic: dict[str, float] = {}
    for i in incorrect:
        penalty_by_topic[i.topic] = penalty_by_topic.get(i.topic, 0.0) + _TOPIC_INCORRECT_PENALTY

    topics = sorted(count_by_topic.keys())
    scores: list[TopicScore] = []
    for topic in topics:
        total = count_by_topic[topic]
        raw = (weight_by_topic.get(topic, 0.0) / total) * 100 if total else 0.0
        score = max(0.0, min(100.0, raw - penalty_by_topic.get(topic, 0.0)))
        scores.append(TopicScore(topic=topic, score=round(score, 1), finding_count=total))
    return scores


class AnswerEvaluator:
    """Stateless evaluator — safe to share a single instance across requests."""

    def evaluate(self, *, disease: Disease, student_text: str) -> EvaluationResult:
        expected_findings: list[str] = list(
            disease.lab_pattern_template.get("expected_findings", [])
        )
        raw_candidates = preprocessing.split_sentences(student_text)

        if not expected_findings:
            # No answer key on this disease template - nothing to score
            # against. Return a neutral result rather than raising, so a
            # malformed/legacy disease row can't 500 the whole endpoint.
            return EvaluationResult(
                score=0.0,
                tutor_feedback=(
                    "This case has no reference findings configured yet, so it "
                    "can't be auto-scored. Please flag this to your lecturer."
                ),
            )

        if not raw_candidates:
            empty_missing = [
                _finding_match(expected_finding=f, matched_statement=None, similarity=0.0)
                for f in expected_findings
            ]
            return EvaluationResult(
                score=0.0,
                missing_findings=empty_missing,
                topic_scores=_aggregate_topic_scores(
                    confirmed=[], missing=empty_missing, incorrect=[]
                ),
                tutor_feedback=(
                    "You didn't submit any interpretation text. Try describing "
                    "what the results show, one finding per sentence."
                ),
            )

        normalized_candidates = [preprocessing.normalize(c) for c in raw_candidates]
        normalized_expected = [preprocessing.normalize(f) for f in expected_findings]

        similarity = _similarity_matrix(normalized_candidates, normalized_expected)

        confirmed: list[FindingMatchResult] = []
        missing: list[FindingMatchResult] = []
        matched_candidate_indices: set[int] = set()
        # Parameter keywords "used up" by a confirmed/partial match, so the
        # same statement isn't later double-flagged as contradicting a
        # finding it already (correctly) matched.
        matched_parameters: set[str] = set()

        # Expected-finding polarity lookup, keyed by parameter. Computed
        # up front so the matching loop below can refuse to credit a
        # candidate statement whose polarity contradicts the finding it
        # would otherwise lexically match (e.g. TF-IDF alone would happily
        # match "hemoglobin is normal" to "hemoglobin is decreased" on
        # shared vocabulary despite the two being opposite claims).
        expected_polarity_by_parameter: dict[str, str] = {}
        for normalized_finding in normalized_expected:
            polarity = preprocessing.extract_polarity(normalized_finding)
            if polarity is None:
                continue
            for parameter in preprocessing.extract_parameters(normalized_finding):
                expected_polarity_by_parameter[parameter] = polarity

        def _contradicts_finding(candidate_idx: int, expected_normalized: str) -> bool:
            candidate_normalized = normalized_candidates[candidate_idx]
            candidate_polarity = preprocessing.extract_polarity(candidate_normalized)
            if candidate_polarity is None:
                return False
            expected_polarity = preprocessing.extract_polarity(expected_normalized)
            if expected_polarity is None:
                return False
            shared_parameters = preprocessing.extract_parameters(
                candidate_normalized
            ) & preprocessing.extract_parameters(expected_normalized)
            return bool(shared_parameters) and candidate_polarity != expected_polarity

        for row_idx, expected_finding in enumerate(expected_findings):
            scores = similarity[row_idx]
            ranked_indices = np.argsort(scores)[::-1]

            best_idx: int | None = None
            best_score = 0.0
            for candidate_idx in ranked_indices:
                candidate_idx = int(candidate_idx)
                score = float(scores[candidate_idx])
                if score < PARTIAL_THRESHOLD:
                    break
                if _contradicts_finding(candidate_idx, normalized_expected[row_idx]):
                    continue
                best_idx, best_score = candidate_idx, score
                break

            if best_idx is not None:
                confirmed.append(
                    _finding_match(
                        expected_finding=expected_finding,
                        matched_statement=raw_candidates[best_idx],
                        similarity=round(best_score, 3),
                        normalized_finding=normalized_expected[row_idx],
                    )
                )
                matched_candidate_indices.add(best_idx)
                matched_parameters |= preprocessing.extract_parameters(normalized_expected[row_idx])
            else:
                top_idx = int(ranked_indices[0])
                missing.append(
                    _finding_match(
                        expected_finding=expected_finding,
                        matched_statement=None,
                        similarity=round(float(scores[top_idx]), 3),
                        normalized_finding=normalized_expected[row_idx],
                    )
                )

        incorrect: list[IncorrectStatementResult] = []
        for idx, (raw, normalized) in enumerate(
            zip(raw_candidates, normalized_candidates, strict=True)
        ):
            if idx in matched_candidate_indices:
                continue
            statement_parameters = preprocessing.extract_parameters(normalized) - matched_parameters
            statement_polarity = preprocessing.extract_polarity(normalized)
            if statement_polarity is None or not statement_parameters:
                continue
            for parameter in statement_parameters:
                expected_polarity = expected_polarity_by_parameter.get(parameter)
                if expected_polarity is not None and expected_polarity != statement_polarity:
                    incorrect.append(
                        IncorrectStatementResult(
                            statement=raw,
                            reason=(
                                f"Expected {parameter} to be {expected_polarity}, "
                                f"but this statement says {statement_polarity}."
                            ),
                            topic=topic_for_parameter(parameter),
                        )
                    )
                    break

        confirmed_weight = sum(
            1.0 if f.similarity >= CONFIRMED_THRESHOLD else 0.5 for f in confirmed
        )
        raw_score = (confirmed_weight / len(expected_findings)) * 100
        penalty = len(incorrect) * INCORRECT_PENALTY
        score = max(0.0, min(100.0, raw_score - penalty))

        tutor_feedback = _build_tutor_feedback(
            score=score, confirmed=confirmed, missing=missing, incorrect=incorrect
        )
        topic_scores = _aggregate_topic_scores(
            confirmed=confirmed, missing=missing, incorrect=incorrect
        )

        return EvaluationResult(
            score=round(score, 1),
            confirmed_findings=confirmed,
            missing_findings=missing,
            topic_scores=topic_scores,
            incorrect_findings=incorrect,
            tutor_feedback=tutor_feedback,
        )


def _build_tutor_feedback(
    *,
    score: float,
    confirmed: list[FindingMatchResult],
    missing: list[FindingMatchResult],
    incorrect: list[IncorrectStatementResult],
) -> str:
    """Rule-based feedback summary (no free-form LLM call — `docs/LLD.md` §2).

    Sprint 5 formalizes the per-finding "why this matters" explanation
    templates (`app.services.tutor.explanations`, attached to every finding
    via `_finding_match`) that Sprint 4 flagged as future work: the
    aggregate summary below now surfaces the explanation for the single
    most important gap — the first missing finding — rather than only
    naming what was missed, so the tutor panel teaches the underlying
    physiology, not just the checklist. Every individual finding's full
    explanation is still available via `FindingMatchResult.explanation` for
    the frontend's per-finding display (`InterpretationResultCard`).
    """
    parts: list[str] = []

    if score >= 85:
        parts.append("Strong interpretation.")
    elif score >= 60:
        parts.append("Good start, but a few findings need more attention.")
    elif score >= 30:
        parts.append("Several key findings are missing from your interpretation.")
    else:
        parts.append("This interpretation is missing most of the expected findings.")

    if confirmed:
        parts.append(f"You correctly identified {len(confirmed)} finding(s).")
    if missing:
        parts.append(
            "Still to address: "
            + "; ".join(f.expected_finding for f in missing[:3])
            + ("..." if len(missing) > 3 else "")
        )
        top_gap = missing[0]
        if top_gap.explanation:
            parts.append(f"Why it matters: {top_gap.explanation}")
    if incorrect:
        parts.append(
            f"{len(incorrect)} statement(s) contradict the case findings — review those results again."
        )

    return " ".join(parts)

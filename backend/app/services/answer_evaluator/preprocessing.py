"""Text preprocessing for `AnswerEvaluator`.

`docs/LLD.md` §5 sketches this step as "spaCy preprocessing". This module
deliberately implements the same *steps* (sentence segmentation, lowercase
normalization, lemmatization-equivalent term normalization) with a small,
dependency-free rule set rather than loading a spaCy language model.

Why: a downloaded spaCy/HuggingFace model pins the service to a
network-available model registry at build *and* first-boot time, which
conflicts with `docs/HLD.md` §1/§7's free-tier, low-resource, solo-developer
principle — it adds a multi-hundred-MB artifact, a cold-start download (or a
committed binary blob), and a CI dependency on an external registry being
reachable, purely to segment English sentences and canonicalize a handful of
hematology terms. Enock has made the same call before on HandyRwanda
(replacing a HuggingFace API dependency with local TF-IDF + dictionary
translation) for identical reasons.

The domain synonym table below started intentionally small and
hematology-scoped for Sprint 4 (Phase 1). Sprint 7 (Clinical Chemistry)
extends it with LFT/RFT/electrolyte vocabulary, in place, without touching
the scoring algorithm in `evaluator.py` — exactly the extension point this
module's Sprint 4 docstring anticipated. Sprint 9+ (Microbiology,
Parasitology, ...) can keep extending the same way.
"""

from __future__ import annotations

import re

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;\n])\s+|\n+")
_WHITESPACE_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"[a-z0-9]+")

# Canonical parameter keywords a clinical statement might reference, mapped
# from common phrasings/abbreviations a student might type. Order matters:
# longer/more specific phrases are matched first via sorted-by-length lookup.
PARAMETER_SYNONYMS: dict[str, str] = {
    "hemoglobin": "hemoglobin",
    "haemoglobin": "hemoglobin",
    "hb": "hemoglobin",
    "hgb": "hemoglobin",
    "platelet": "platelets",
    "platelets": "platelets",
    "plt": "platelets",
    "white cell count": "wbc",
    "white blood cell count": "wbc",
    "white blood cells": "wbc",
    "white cell": "wbc",
    "wbc": "wbc",
    "total white cell count": "wbc",
    "mean corpuscular volume": "mcv",
    "mcv": "mcv",
    "mean corpuscular hemoglobin": "mch",
    "mch": "mch",
    "red cell distribution width": "rdw",
    "rdw": "rdw",
    "reticulocyte": "reticulocyte",
    "reticulocytes": "reticulocyte",
    "retic": "reticulocyte",
    "neutrophil": "neutrophil",
    "neutrophils": "neutrophil",
    "neutrophil count": "neutrophil",
    "c-reactive protein": "crp",
    "c reactive protein": "crp",
    "crp": "crp",
    "ferritin": "ferritin",
    "serum ferritin": "ferritin",
    "iron stores": "ferritin",
    "trophozoite": "trophozoite",
    "trophozoites": "trophozoite",
    "ring-form trophozoites": "trophozoite",
    "ring form trophozoites": "trophozoite",
    "gametocyte": "gametocyte",
    "gametocytes": "gametocyte",
    "microcytosis": "microcytosis",
    "microcytic": "microcytosis",
    "hypochromia": "hypochromia",
    "hypochromic": "hypochromia",
    "anisocytosis": "anisocytosis",
    "anisopoikilocytosis": "anisocytosis",
    "leukocytosis": "leukocytosis",
    "left shift": "left_shift",
    "band forms": "left_shift",
    # --- Sprint 7 (Clinical Chemistry) ---
    "alanine aminotransferase": "alt",
    "alanine transaminase": "alt",
    "alt": "alt",
    "aspartate aminotransferase": "ast",
    "aspartate transaminase": "ast",
    "ast": "ast",
    "total bilirubin": "bilirubin",
    "bilirubin": "bilirubin",
    "serum urea": "urea",
    "blood urea": "urea",
    "urea": "urea",
    "bun": "urea",
    "serum creatinine": "creatinine",
    "creatinine": "creatinine",
    "sodium": "sodium",
    "na+": "sodium",
    "potassium": "potassium",
    "k+": "potassium",
    "chloride": "chloride",
    "bicarbonate": "bicarbonate",
    "hco3": "bicarbonate",
    "blood glucose": "glucose",
    "serum glucose": "glucose",
    "glucose": "glucose",
    "blood sugar": "glucose",
    "hyperglycemia": "hyperglycemia",
    "hypoglycemia": "hypoglycemia",
    "metabolic acidosis": "metabolic_acidosis",
    "acidosis": "metabolic_acidosis",
    "hepatocellular injury": "hepatocellular_injury",
    "renal clearance": "renal_function",
    "kidney function": "renal_function",
}

# Direction/polarity vocabulary, canonicalized to one of "increased",
# "decreased", or "normal". Used by `evaluator.py` to detect when a student
# states the opposite of what a case's findings actually show.
POLARITY_SYNONYMS: dict[str, str] = {
    "increased": "increased",
    "elevated": "increased",
    "raised": "increased",
    "high": "increased",
    "higher": "increased",
    "above normal": "increased",
    "decreased": "decreased",
    "reduced": "decreased",
    "low": "decreased",
    "lower": "decreased",
    "depleted": "decreased",
    "below normal": "decreased",
    "normal": "normal",
    "unremarkable": "normal",
    "within normal limits": "normal",
    "within normal range": "normal",
    "not elevated": "normal",
    "not decreased": "normal",
    "no abnormality": "normal",
    "absent": "normal",
}


def split_sentences(text: str) -> list[str]:
    """Segment free text into candidate finding-statements.

    Splits on sentence-ending punctuation/newlines/semicolons — the same
    granularity spaCy's rule-based `sentencizer` would produce for this kind
    of short clinical prose, without requiring a loaded pipeline.

    Whitespace is only collapsed *within* each resulting sentence (not
    beforehand), since collapsing it first would erase the very newline
    boundaries this function is meant to split on.
    """
    if not text or not text.strip():
        return []
    candidates = _SENTENCE_SPLIT_RE.split(text)
    sentences = (_WHITESPACE_RE.sub(" ", c).strip() for c in candidates)
    return [s for s in sentences if s]


def normalize(text: str) -> str:
    """Lowercase + canonicalize known domain terms (lemmatization-equivalent).

    Longer synonym phrases are substituted before shorter/overlapping ones
    so e.g. "total white cell count" collapses to "wbc" as a whole, rather
    than leaving fragments behind.
    """
    lowered = text.lower()
    for phrase in sorted(PARAMETER_SYNONYMS, key=len, reverse=True):
        lowered = re.sub(rf"\b{re.escape(phrase)}\b", PARAMETER_SYNONYMS[phrase], lowered)
    for phrase in sorted(POLARITY_SYNONYMS, key=len, reverse=True):
        lowered = re.sub(rf"\b{re.escape(phrase)}\b", POLARITY_SYNONYMS[phrase], lowered)
    return _WHITESPACE_RE.sub(" ", lowered).strip()


def extract_parameters(normalized_text: str) -> set[str]:
    """Return the set of canonical parameter keywords present in a normalized string."""
    tokens = set(_WORD_RE.findall(normalized_text))
    return tokens & set(PARAMETER_SYNONYMS.values())


def extract_polarity(normalized_text: str) -> str | None:
    """Return the single dominant polarity ("increased"/"decreased"/"normal") if any.

    If a statement mentions more than one polarity term (rare, but possible
    in a run-on sentence), returns None rather than guessing — such a
    statement is too ambiguous to safely flag as contradicting anything.
    """
    tokens: list[str] = _WORD_RE.findall(normalized_text)
    found: set[str] = {tok for tok in tokens if tok in {"increased", "decreased", "normal"}}
    if len(found) == 1:
        (polarity,) = found
        return polarity
    return None

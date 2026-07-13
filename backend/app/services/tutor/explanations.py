"""Domain rule-based tutor explanation templates.

`docs/SPRINT_PLAN.md` Sprint 5: "Domain rule-based tutor explanation
templates (why a finding matters, tied to disease template)". This module
is the template table; `app/services/answer_evaluator/evaluator.py` calls
into it (via `explain_finding`) once per expected/incorrect finding it has
already extracted a canonical parameter + polarity for (reusing
`answer_evaluator.preprocessing`, not a second NLP pass).

Design notes:
- Keyed by the same canonical parameter vocabulary
  `preprocessing.PARAMETER_SYNONYMS` already normalizes free text down to,
  so this table never has to re-derive what a statement is "about" — it
  only has to explain it.
- Every parameter is also assigned a `topic` — a coarser grouping (e.g.
  several red-cell-index parameters share the `red_cell_indices` topic).
  Topics, not raw parameters, are what `student_topic_mastery` (Sprint 5)
  tracks, since "how is the student doing on red cell indices overall" is a
  more useful mastery signal than one row per lab parameter.
- Sprint 5 (Phase 1) scoped this table to hematology; Sprint 7 (Clinical
  Chemistry) extends it in place with hepatic/renal/electrolyte parameters,
  without touching `evaluator.py` or `MasteryTracker` — the extension point
  this module's Sprint 5 docstring anticipated. Sprint 9+ (Microbiology,
  Parasitology, ...) can keep extending the same way.
"""

from __future__ import annotations

from dataclasses import dataclass

# Canonical parameter -> coarser learning topic. Anything not listed here
# falls back to "general_interpretation" (see `topic_for_parameter`) rather
# than raising, so a new parameter added to `preprocessing.py` without a
# matching topic here degrades gracefully instead of 500ing the evaluation
# endpoint.
TOPIC_BY_PARAMETER: dict[str, str] = {
    "hemoglobin": "red_cell_indices",
    "mcv": "red_cell_indices",
    "mch": "red_cell_indices",
    "rdw": "red_cell_indices",
    "microcytosis": "red_cell_morphology",
    "hypochromia": "red_cell_morphology",
    "anisocytosis": "red_cell_morphology",
    "reticulocyte": "marrow_response",
    "platelets": "platelet_count",
    "wbc": "white_cell_response",
    "neutrophil": "white_cell_response",
    "leukocytosis": "white_cell_response",
    "left_shift": "white_cell_response",
    "crp": "inflammatory_markers",
    "ferritin": "iron_studies",
    "trophozoite": "parasitology",
    "gametocyte": "parasitology",
    # --- Sprint 7 (Clinical Chemistry) ---
    "alt": "hepatic_function",
    "ast": "hepatic_function",
    "bilirubin": "hepatic_function",
    "hepatocellular_injury": "hepatic_function",
    "urea": "renal_function",
    "creatinine": "renal_function",
    "renal_function": "renal_function",
    "sodium": "electrolyte_balance",
    "potassium": "electrolyte_balance",
    "chloride": "electrolyte_balance",
    "bicarbonate": "electrolyte_balance",
    "metabolic_acidosis": "electrolyte_balance",
    "glucose": "glucose_metabolism",
    "hyperglycemia": "glucose_metabolism",
    "hypoglycemia": "glucose_metabolism",
}

DEFAULT_TOPIC = "general_interpretation"

# (parameter, polarity) -> "why this matters" explanation. `polarity` may be
# "increased", "decreased", "normal", or `None` for parameters that are
# reported as present/absent rather than up/down (blood-film organisms).
# Explanations intentionally teach the underlying physiology, not just
# restate the finding, since the student already saw the finding itself.
_EXPLANATIONS: dict[tuple[str, str | None], str] = {
    ("hemoglobin", "decreased"): (
        "A low hemoglobin means the blood is carrying less oxygen than normal — "
        "this is the lab definition of anemia. What matters clinically is *why* "
        "it's low: increased destruction (hemolysis), reduced production "
        "(marrow/iron problems), or blood loss each point to a different disease."
    ),
    ("hemoglobin", "increased"): (
        "An elevated hemoglobin can reflect dehydration (relative concentration) "
        "or true overproduction of red cells — worth distinguishing before "
        "assuming pathology."
    ),
    ("mcv", "decreased"): (
        "A decreased MCV (microcytosis) means the red cells themselves are "
        "smaller than normal — classically seen when hemoglobin synthesis is "
        "impaired, as in iron deficiency or thalassemia."
    ),
    ("mch", "decreased"): (
        "A decreased MCH (hypochromia) means each red cell is carrying less "
        "hemoglobin than normal, which is why the cells look pale under the "
        "microscope — it tracks with, and reinforces, a microcytic picture."
    ),
    ("rdw", "increased"): (
        "An increased RDW means the red cell population is more variable in "
        "size (anisocytosis) than normal — a useful clue that new, differently "
        "sized cells are being produced in response to a deficiency, rather "
        "than a single uniform population."
    ),
    ("reticulocyte", "increased"): (
        "A raised reticulocyte count shows the bone marrow is actively "
        "compensating by pushing out young red cells faster than usual — "
        "expected when red cells are being destroyed or lost faster than "
        "normal, as in hemolysis."
    ),
    ("platelets", "decreased"): (
        "Thrombocytopenia (low platelets) increases bleeding risk and, in "
        "infections such as malaria, often reflects marrow suppression or "
        "peripheral platelet consumption/destruction rather than a primary "
        "platelet disorder."
    ),
    ("wbc", "increased"): (
        "An elevated total white cell count (leukocytosis) is the body "
        "mobilizing more immune cells — most often a response to bacterial "
        "infection or acute inflammation."
    ),
    ("wbc", "decreased"): (
        "A decreased white cell count can mean the marrow isn't producing "
        "enough white cells, or that an infection (e.g. some parasitic/viral "
        "illnesses) is consuming or suppressing them faster than they're made."
    ),
    ("wbc", "normal"): (
        "A normal-to-only-mildly-changed white cell count doesn't rule out "
        "infection — some pathogens, including malaria, don't reliably drive "
        "leukocytosis, so this finding is best interpreted alongside the rest "
        "of the picture, not in isolation."
    ),
    ("neutrophil", "increased"): (
        "A rise in neutrophils, especially with a left shift (more immature "
        "band forms in circulation), is the classic marrow response to an "
        "acute bacterial infection — the marrow is releasing cells faster "
        "than it can fully mature them."
    ),
    ("leukocytosis", None): (
        "Leukocytosis (a raised white cell count) signals an active immune "
        "response — pairing it with the differential (which cell line is "
        "raised) narrows down bacterial vs. other causes."
    ),
    ("left_shift", None): (
        "A 'left shift' — more immature band-form neutrophils than usual — "
        "means the marrow is releasing white cells before they're fully "
        "mature, a sign of an acute, demanding infection."
    ),
    ("crp", "increased"): (
        "C-reactive protein rises within hours of acute inflammation — it's "
        "sensitive but not specific, so an elevated CRP supports an acute "
        "inflammatory or infectious process but doesn't identify the cause "
        "on its own."
    ),
    ("ferritin", "decreased"): (
        "Ferritin reflects the body's stored iron. A low ferritin is the most "
        "specific routine marker of true iron deficiency, since it's usually "
        "the first thing to fall before hemoglobin itself drops."
    ),
    ("trophozoite", None): (
        "Ring-form trophozoites on a blood film are the definitive "
        "morphological proof of a Plasmodium infection — this is what "
        "confirms a malaria diagnosis rather than just supporting it."
    ),
    ("gametocyte", None): (
        "Gametocytes are the sexual stage of the malaria parasite — their "
        "presence indicates the patient is potentially infectious to "
        "mosquitoes, which matters for transmission control even though it "
        "doesn't change the acute diagnosis."
    ),
    ("microcytosis", None): (
        "Microcytosis (small red cells on the blood film) is the visual "
        "counterpart of a decreased MCV — seeing it directly on the film "
        "confirms the automated count wasn't a measurement artifact."
    ),
    ("hypochromia", None): (
        "Hypochromia (pale-staining red cells on the film) is the visual "
        "counterpart of a decreased MCH — the cells look pale because "
        "they're under-filled with hemoglobin."
    ),
    ("anisocytosis", None): (
        "Anisocytosis (varying red cell sizes on the film) is the visual "
        "counterpart of a raised RDW, and supports an active, evolving "
        "red-cell production problem rather than a long-stable one."
    ),
    # --- Sprint 7 (Clinical Chemistry) ---
    ("alt", "increased"): (
        "ALT is a liver-specific enzyme released when hepatocytes are "
        "injured — a marked rise (usually out of proportion to AST in "
        "hepatocellular disease) points to direct liver-cell damage rather "
        "than a biliary obstruction picture."
    ),
    ("ast", "increased"): (
        "AST rises alongside ALT in hepatocellular injury, but it's also "
        "found in cardiac and skeletal muscle — an ALT-predominant rise "
        "supports a liver-specific cause, while an AST-predominant rise "
        "should prompt you to consider muscle or cardiac sources too."
    ),
    ("bilirubin", "increased"): (
        "A raised total bilirubin is what produces visible jaundice — "
        "pairing it with markedly elevated transaminases points to a "
        "hepatocellular cause rather than pure hemolysis or obstruction."
    ),
    ("hepatocellular_injury", None): (
        "'Hepatocellular injury' describes a pattern where liver-cell "
        "enzymes (ALT/AST) rise disproportionately to bilirubin/ALP — "
        "distinguishing it from a cholestatic/obstructive pattern is a key "
        "first step in narrowing the differential for liver disease."
    ),
    ("urea", "increased"): (
        "A raised serum urea reflects reduced renal clearance of nitrogenous "
        "waste — interpreting it alongside creatinine (which is less "
        "affected by diet/hydration) helps confirm true renal impairment "
        "rather than a purely pre-renal (dehydration) picture."
    ),
    ("creatinine", "increased"): (
        "Creatinine is produced at a fairly constant rate from muscle and "
        "cleared almost entirely by the kidneys, so a rising creatinine is "
        "one of the most specific routine markers of declining kidney "
        "function — the degree of rise roughly tracks the severity of "
        "injury."
    ),
    ("renal_function", None): (
        "Renal function is best judged from urea and creatinine together, "
        "not either alone — creatinine is the more specific marker, while "
        "urea can also rise from dehydration, a high-protein diet, or GI "
        "bleeding."
    ),
    ("sodium", "decreased"): (
        "Hyponatremia here reflects osmotic dilution — severe hyperglycemia "
        "pulls water into the vascular space and lowers the measured sodium "
        "concentration even though total-body sodium hasn't actually "
        "changed, a distinction worth stating explicitly in an "
        "interpretation."
    ),
    ("sodium", "increased"): (
        "Hypernatremia usually reflects a relative water deficit (dehydration "
        "outpacing sodium loss) rather than a true sodium excess — always "
        "interpret it alongside the patient's fluid status."
    ),
    ("potassium", "increased"): (
        "Hyperkalemia is one of the few lab findings that can be immediately "
        "life-threatening (cardiac arrhythmia) — it can arise from reduced "
        "renal excretion, or, as in diabetic ketoacidosis, from acidosis "
        "shifting potassium out of cells even while total-body stores are "
        "actually depleted."
    ),
    ("potassium", "decreased"): (
        "Hypokalemia can result from GI losses, renal wasting, or a shift of "
        "potassium into cells — worth correlating with the rest of the "
        "electrolyte panel before assuming a single cause."
    ),
    ("chloride", "decreased"): (
        "Chloride often tracks with sodium and bicarbonate; a fall usually "
        "reflects the same process driving those changes rather than an "
        "independent chloride-specific problem."
    ),
    ("bicarbonate", "decreased"): (
        "A low bicarbonate signals a metabolic acidosis — the body's "
        "buffering capacity is being consumed faster than it can be "
        "replenished, as seen in diabetic ketoacidosis where ketoacids "
        "accumulate faster than the kidneys/lungs can compensate."
    ),
    ("metabolic_acidosis", None): (
        "A metabolic acidosis (low bicarbonate) combined with rapid, deep "
        "breathing is the body attempting respiratory compensation — "
        "blowing off CO2 to partially correct the pH, which is why the "
        "respiratory rate is part of the clinical picture, not a separate "
        "finding."
    ),
    ("glucose", "increased"): (
        "Marked hyperglycemia in the context of acidosis and electrolyte "
        "shifts is the hallmark of diabetic ketoacidosis — insulin "
        "deficiency prevents cells from using glucose, so it accumulates in "
        "the blood while the body burns fat for energy, producing the "
        "ketoacids that drive the acidosis."
    ),
}

_GENERIC_EXPLANATION = (
    "This finding is part of the expected pattern for this case — think "
    "about which underlying process would produce it, and how it fits with "
    "the other results."
)


@dataclass(frozen=True)
class FindingExplanation:
    topic: str
    explanation: str


def topic_for_parameter(parameter: str) -> str:
    """Coarse learning topic for a canonical parameter (`preprocessing.py` vocabulary)."""
    return TOPIC_BY_PARAMETER.get(parameter, DEFAULT_TOPIC)


def explain(parameter: str, polarity: str | None) -> FindingExplanation:
    """Return the topic + "why it matters" explanation for a parameter/polarity pair.

    Falls back progressively: exact `(parameter, polarity)` match, then
    `(parameter, None)` (organism-presence-style findings), then a generic
    explanation — so an unmapped combination never raises, it just teaches
    less specifically.
    """
    topic = topic_for_parameter(parameter)
    explanation = _EXPLANATIONS.get((parameter, polarity)) or _EXPLANATIONS.get((parameter, None))
    return FindingExplanation(topic=topic, explanation=explanation or _GENERIC_EXPLANATION)


def explain_finding(normalized_text: str) -> FindingExplanation | None:
    """Explain a normalized finding string by extracting its parameter(s)/polarity.

    Reuses `answer_evaluator.preprocessing` rather than re-parsing, so this
    module never drifts out of sync with what the evaluator itself
    considers a "parameter". Returns `None` if no known parameter is
    mentioned (e.g. a free-form finding with no canonical term yet).
    """
    from app.services.answer_evaluator import preprocessing

    parameters = preprocessing.extract_parameters(normalized_text)
    if not parameters:
        return None
    polarity = preprocessing.extract_polarity(normalized_text)
    # A finding can technically reference more than one parameter (rare);
    # deterministically pick the alphabetically-first so results are stable.
    parameter = sorted(parameters)[0]
    return explain(parameter, polarity)

"""Adult reference ranges for every lab parameter `ResultGenerator` can produce.

Values are approximate teaching-grade reference intervals (not intended for
clinical use — see `docs/PRD.md` §7, "Out of Scope"). Hemoglobin and Ferritin
are sex-adjusted, since normal ranges genuinely differ; everything else uses
a single unisex range for simplicity at MVP scope.
"""

from __future__ import annotations

ReferenceRange = tuple[float, float]

REFERENCE_RANGES: dict[str, ReferenceRange | dict[str, ReferenceRange]] = {
    "hemoglobin_g_dl": {"male": (13.5, 17.5), "female": (12.0, 15.5)},
    "wbc_10e9_l": (4.0, 11.0),
    "platelets_10e9_l": (150.0, 400.0),
    "mcv_fl": (80.0, 100.0),
    "mch_pg": (27.0, 33.0),
    "rdw_pct": (11.5, 14.5),
    "neutrophil_pct": (40.0, 70.0),
    "reticulocyte_pct": (0.5, 2.5),
    "ferritin_ng_ml": (30.0, 200.0),
    "crp_mg_l": (0.0, 10.0),
    "alt_u_l": (7.0, 56.0),
    "ast_u_l": (10.0, 40.0),
    "urine_protein_mg_dl": (0.0, 20.0),
    "urine_glucose_mg_dl": (0.0, 15.0),
}

# The full panel returned whenever a "core" test (e.g. CBC) doesn't declare
# its own `measured_parameters` list — kept only as a defensive fallback;
# `test_catalog.json` always declares this explicitly for the CBC test.
CBC_PANEL_PARAMETERS: tuple[str, ...] = (
    "hemoglobin_g_dl",
    "wbc_10e9_l",
    "platelets_10e9_l",
    "mcv_fl",
    "mch_pg",
    "rdw_pct",
    "neutrophil_pct",
)


def get_reference_range(parameter: str, sex: str) -> ReferenceRange:
    """Return the `(low, high)` reference bounds for `parameter`.

    Raises `KeyError` if no reference range is configured — callers should
    treat that as a data-completeness bug (a test declares a
    `measured_parameter` with no corresponding reference range).
    """
    entry = REFERENCE_RANGES.get(parameter)
    if entry is None:
        raise KeyError(f"No reference range configured for parameter '{parameter}'.")
    if isinstance(entry, dict):
        return entry[sex]
    return entry

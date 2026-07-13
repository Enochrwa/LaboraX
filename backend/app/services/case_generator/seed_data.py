"""Loads disease/symptom/lab-pattern seed definitions from `app/ml/data/`.

Seed files are plain JSON so they're easy for a non-engineer domain expert
(e.g. a lecturer) to review or extend without touching Python code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "data"


class DiseaseSeedDefinition(TypedDict):
    name: str
    category: str
    symptom_template: dict[str, Any]
    lab_pattern_template: dict[str, Any]
    difficulty_levels: dict[str, Any]


# Every seed file that should be loaded into the `diseases` table. Extending
# to a new department (Sprint 7+) is just adding another file here.
SEED_FILES: tuple[str, ...] = ("hematology_diseases.json", "chemistry_diseases.json")


def load_disease_seed_definitions(
    data_dir: Path | None = None,
) -> list[DiseaseSeedDefinition]:
    """Read and parse every configured seed file into a flat list of dicts."""
    base_dir = data_dir or DATA_DIR
    definitions: list[DiseaseSeedDefinition] = []
    for filename in SEED_FILES:
        file_path = base_dir / filename
        if not file_path.exists():
            continue
        with file_path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
        definitions.extend(payload)
    return definitions

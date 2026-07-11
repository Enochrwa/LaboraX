"""Loads test-catalog seed definitions from `app/ml/data/test_catalog.json`.

Mirrors `app.services.case_generator.seed_data` — plain JSON so a
non-engineer domain expert can review or extend the orderable test list
without touching Python code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypedDict

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "ml" / "data"
CATALOG_FILE = "test_catalog.json"


class TestCatalogSeedDefinition(TypedDict):
    code: str
    name: str
    category: str
    cost_weight: float
    relevance_rules: dict[str, Any]


def load_test_catalog_definitions(
    data_dir: Path | None = None,
) -> list[TestCatalogSeedDefinition]:
    """Read and parse `test_catalog.json` into a flat list of dicts."""
    base_dir = data_dir or DATA_DIR
    file_path = base_dir / CATALOG_FILE
    if not file_path.exists():
        return []
    with file_path.open(encoding="utf-8") as fh:
        payload: list[TestCatalogSeedDefinition] = json.load(fh)
    return payload

"""Validate the local synthetic corpus without printing record contents."""

# ruff: noqa: E402, I001

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from seed_dev import BLUEPRINTS, EMPLOYEES, ENVIRONMENTS, TECHNOLOGIES


MIN_GENERATED_SOLUTIONS = 1000
MIN_EMPLOYEES = 40
MIN_TECHNOLOGIES = 50
MIN_SOURCE_CATEGORIES = 8


def main() -> int:
    blueprint_keys = [blueprint[0] for blueprint in BLUEPRINTS]
    duplicate_keys = sum(count - 1 for count in Counter(blueprint_keys).values() if count > 1)
    generated_solution_count = len(BLUEPRINTS) * len(ENVIRONMENTS)
    short_step_count = sum(1 for blueprint in BLUEPRINTS if len(blueprint[5]) < 3)
    missing_technology_count = sum(1 for blueprint in BLUEPRINTS if len(blueprint[6]) == 0)
    known_technology_names = {technology[0] for technology in TECHNOLOGIES}
    unknown_technology_references = sum(
        1
        for blueprint in BLUEPRINTS
        for technology in blueprint[6]
        if technology not in known_technology_names
    )
    script_path = Path(__file__).resolve()
    source_catalog_candidates = [
        script_path.parents[1] / "data" / "source_catalog.json",
        script_path.parents[2] / "data" / "source_catalog.json" if len(script_path.parents) > 2 else script_path.parents[1] / "missing",
        script_path.parents[1].parent / "data" / "source_catalog.json",
    ]
    source_catalog_path = next((path for path in source_catalog_candidates if path.exists()), source_catalog_candidates[0])
    source_categories = 0
    source_catalog_valid = False
    if source_catalog_path.exists():
        source_catalog = json.loads(source_catalog_path.read_text(encoding="utf-8"))
        source_categories = len(source_catalog.get("sources", []))
        source_catalog_valid = bool(source_catalog.get("generated_records_are_synthetic")) and not bool(source_catalog.get("private_company_material_used"))

    checks = {
        "employees": len(EMPLOYEES),
        "technologies": len(TECHNOLOGIES),
        "blueprints": len(BLUEPRINTS),
        "environments": len(ENVIRONMENTS),
        "generated_solutions": generated_solution_count,
        "duplicate_blueprint_keys": duplicate_keys,
        "blueprints_with_fewer_than_three_steps": short_step_count,
        "blueprints_without_technologies": missing_technology_count,
        "unknown_technology_references": unknown_technology_references,
        "source_categories": source_categories,
        "source_catalog_valid": int(source_catalog_valid),
    }
    for key, value in checks.items():
        print(f"{key}={value}")

    failed = (
        len(EMPLOYEES) < MIN_EMPLOYEES
        or len(TECHNOLOGIES) < MIN_TECHNOLOGIES
        or generated_solution_count < MIN_GENERATED_SOLUTIONS
        or duplicate_keys > 0
        or short_step_count > 0
        or missing_technology_count > 0
        or unknown_technology_references > 0
        or source_categories < MIN_SOURCE_CATEGORIES
        or not source_catalog_valid
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

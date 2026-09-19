#!/usr/bin/env python3
"""Discover retained preprocessing inputs and write an aggregate report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_retained_rosters,
)
from glioma_selective.preprocessing.discovery import (  # noqa: E402
    build_geometry_report,
    discover_cases,
)
from glioma_selective.utils import paths  # noqa: E402


def main() -> int:
    """Build, print, and write the retained UTSW/UCSF aggregate report."""

    try:
        retained_rosters = build_real_retained_rosters()
        cases = tuple(
            case
            for cohort, retained_ids in retained_rosters.items()
            for case in discover_cases(cohort, retained_patient_ids=retained_ids)
        )
        report = build_geometry_report(cases)
        output_path = paths.manifests_dir() / "preprocessing_discovery_report.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (OSError, RuntimeError, ValueError):
        print("discover_preprocessing_inputs.py: discovery failed", file=sys.stderr)
        return 1

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

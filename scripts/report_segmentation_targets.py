#!/usr/bin/env python3
"""Inspect retained segmentation targets and write an aggregate-only report."""

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
    discover_cases,
)
from glioma_selective.preprocessing.masks import (  # noqa: E402
    build_mask_report,
    inspect_segmentation_target,
)
from glioma_selective.utils import paths  # noqa: E402


def main() -> int:
    """Inspect every retained case without creating stage-cache entries."""

    retained_rosters = build_real_retained_rosters()
    targets = [
        inspect_segmentation_target(case)
        for cohort in sorted(retained_rosters, key=lambda item: item.value)
        for case in discover_cases(
            cohort,
            retained_patient_ids=retained_rosters[cohort],
        )
    ]
    report = build_mask_report(targets)
    destination = paths.manifests_dir() / "segmentation_target_report.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

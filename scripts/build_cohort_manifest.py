#!/usr/bin/env python3
"""Build the committed, roster-free Phase 03 cohort manifest."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_cohort_manifest,
    write_cohort_manifest,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Build and write the real T03.11 manifest."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "docs/research/manifests/cohort_manifest.json",
        help="committed manifest path",
    )
    args = parser.parse_args(argv)

    try:
        manifest = build_real_cohort_manifest()
        output_path = write_cohort_manifest(manifest, args.output)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"build_cohort_manifest.py: error: {error}", file=sys.stderr)
        return 1

    cohorts = manifest["cohorts"]
    assert isinstance(cohorts, dict)
    print(
        json.dumps(
            {
                "manifest": str(output_path),
                "retained_patient_counts": {
                    cohort: entry["retained_patient_count"]
                    for cohort, entry in cohorts.items()
                    if isinstance(entry, dict)
                },
                "roster_sha256": {
                    cohort: entry["roster_sha256"]
                    for cohort, entry in cohorts.items()
                    if isinstance(entry, dict)
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

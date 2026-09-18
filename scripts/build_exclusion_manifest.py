#!/usr/bin/env python3
"""Build the real Phase 03 exclusion manifest and UCSF scan-selection record."""

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

from glioma_selective.leakage.exclusions import (  # noqa: E402
    build_real_exclusion_manifest,
    build_real_followup_timepoint_selection_record,
    write_exclusion_manifest,
    write_followup_timepoint_selection_record,
)
from glioma_selective.utils import paths  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    """Build, write, and summarize both T03.10 operational artifacts."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "exclusion manifest path (default: "
            "paths.manifests_dir()/exclusion_manifest.json)"
        ),
    )
    parser.add_argument(
        "--followup-output",
        type=Path,
        help=(
            "follow-up selection path (default: "
            "paths.manifests_dir()/ucsf_pdgm_followup_timepoint_selections.json)"
        ),
    )
    args = parser.parse_args(argv)

    try:
        manifest = build_real_exclusion_manifest()
        followup_record = build_real_followup_timepoint_selection_record()
        manifest_path = write_exclusion_manifest(manifest, args.output)
        followup_path = write_followup_timepoint_selection_record(
            followup_record, args.followup_output
        )
    except (OSError, ValueError, RuntimeError, paths.PathResolutionError) as error:
        print(f"build_exclusion_manifest.py: error: {error}", file=sys.stderr)
        return 1

    cohorts = manifest.get("cohorts")
    if not isinstance(cohorts, dict):
        print("build_exclusion_manifest.py: error: malformed manifest", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "exclusion_manifest": str(manifest_path),
                "followup_selection_record": str(followup_path),
                "excluded_patient_count": manifest.get("excluded_patient_count"),
                "reason_counts": manifest.get("reason_counts"),
                "retained_patient_counts": {
                    cohort: report.get("retained_patient_count")
                    for cohort, report in cohorts.items()
                    if isinstance(report, dict)
                },
                "followup_selection_count": followup_record.get("selection_count"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

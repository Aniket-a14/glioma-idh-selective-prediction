#!/usr/bin/env python3
"""Write the T03.8 within-cohort duplicate-scan report.

The default destination is ``paths.manifests_dir() /
duplicate_scan_report.json`` on the external storage volume. The report is a
derived operational artifact and must not be committed. It may contain raw
patient directory names; stdout contains aggregate counts only.

The detector uses the complete T02.6 integrity report when it exists and
matches the adapter inventory. Otherwise it hashes the discovered files itself.
"""

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

from glioma_selective.leakage.duplicate_detection import (  # noqa: E402
    INTEGRITY_REPORT_NAME,
    build_report,
)
from glioma_selective.utils import paths  # noqa: E402


def _summary(report: dict[str, object]) -> dict[str, object]:
    """Return identifier-free aggregate output for the terminal."""

    cohorts = report["cohorts"]
    if not isinstance(cohorts, dict):
        raise ValueError("duplicate report has an invalid cohorts object")
    return {
        cohort: {
            key: cohort_report[key]
            for key in (
                "patient_count",
                "file_count",
                "hash_source",
                "duplicate_finding",
                "duplicate_group_count",
                "duplicate_patient_count",
                "shared_file_hash_group_count",
            )
        }
        for cohort, cohort_report in cohorts.items()
        if isinstance(cohort_report, dict)
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Build, write, and summarize the duplicate-scan report."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort",
        choices=("all", "utsw", "ucsf_pdgm"),
        default="all",
        help="cohort to scan (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="report path (default: paths.manifests_dir()/duplicate_scan_report.json)",
    )
    parser.add_argument(
        "--integrity-report",
        type=Path,
        help=(
            "optional T02.6 report path (default: "
            f"paths.manifests_dir()/{INTEGRITY_REPORT_NAME})"
        ),
    )
    parser.add_argument(
        "--no-integrity-report",
        action="store_true",
        help="force independent file hashing even when T02.6 output exists",
    )
    args = parser.parse_args(argv)
    cohort_names = ("utsw", "ucsf_pdgm") if args.cohort == "all" else (args.cohort,)
    try:
        output = args.output or paths.manifests_dir() / "duplicate_scan_report.json"
        report = build_report(
            cohorts=cohort_names,
            integrity_report_path=args.integrity_report,
            use_integrity_report=not args.no_integrity_report,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (OSError, ValueError, paths.PathResolutionError) as exc:
        print(f"detect_duplicate_scans.py: error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"output": str(output), "cohorts": _summary(report)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

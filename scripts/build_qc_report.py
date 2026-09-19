#!/usr/bin/env python3
"""Build the roster-free Phase 04 automated and visual QC report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.preprocessing.qc_report import (  # noqa: E402
    QCReportError,
    build_qc_report,
)
from glioma_selective.utils import paths  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status",
        type=Path,
        default=None,
        help="preprocessing status manifest",
    )
    parser.add_argument(
        "--verification",
        type=Path,
        default=None,
        help="private per-case verification manifest",
    )
    parser.add_argument(
        "--review-sheet",
        type=Path,
        default=None,
        help="visual QC review CSV",
    )
    parser.add_argument(
        "--overlay-index",
        type=Path,
        default=None,
        help="private QC overlay index",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT
        / "docs/research/manifests/preprocessing_qc_report.json",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Build the report and return one when its inputs are invalid."""

    arguments = _parser().parse_args(argv)
    try:
        report = build_qc_report(
            status_path=arguments.status
            or paths.manifests_dir() / "preprocessing_status.json",
            verification_path=(
                arguments.verification
                or paths.private_data_dir() / "preprocessing_verification_cases.json"
            ),
            review_path=(
                arguments.review_sheet
                or paths.figures_dir() / "qc" / "qc_review_sheet.csv"
            ),
            overlay_index_path=(
                arguments.overlay_index
                or paths.private_data_dir() / "qc_overlay_index.json"
            ),
            output_path=arguments.output,
        )
    except (OSError, RuntimeError, TypeError, ValueError, QCReportError):
        print("build_qc_report.py: report build failed", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

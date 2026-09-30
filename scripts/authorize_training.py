#!/usr/bin/env python3
"""Run the seven Phase 06 checks required before an expensive training run."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for import_root in (REPOSITORY_ROOT, SOURCE_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

_STEP_NAMES = (
    "CPU unit tests",
    "one-sample data test",
    "tiny-batch forward pass",
    "tiny overfit",
    "GPU memory test",
    "checkpoint save/resume equivalence",
    "deterministic/config logging",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--max-steps", type=int, default=150)
    parser.add_argument("--overfit-threshold", type=float, default=0.05)
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.max_steps < 1:
        parser.error("--max-steps must be at least one")
    if args.overfit_threshold <= 0:
        parser.error("--overfit-threshold must be positive")
    if args.dry_run:
        for index, name in enumerate(_STEP_NAMES, start=1):
            print(f"{index}. {name}: not_run")
        return 0

    from glioma_selective.training.authorization import (
        run_harness,
        write_harness_report,
    )
    from glioma_selective.utils import paths

    report = run_harness(
        device=args.device,
        max_steps=args.max_steps,
        overfit_threshold=args.overfit_threshold,
        synthetic=args.synthetic,
    )
    report_path = (
        paths.experiments_dir()
        / report.authorization_run_id
        / "authorization_report.json"
    )
    try:
        write_harness_report(report, report_path)
    except (OSError, ValueError) as exc:
        print(f"authorization report write failed: {exc}", file=sys.stderr)
        return 2

    for result in report.results:
        count_match = re.search(r"(\d+ passed)", result.detail)
        count = f"; {count_match.group(1)}" if count_match else ""
        print(f"{result.name}: {result.status}; {result.seconds:.2f}s{count}")
    return 0 if report.authorized else 1


if __name__ == "__main__":
    raise SystemExit(main())

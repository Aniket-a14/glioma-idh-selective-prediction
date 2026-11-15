#!/usr/bin/env python3
"""Run the seven Phase 06 checks required before an expensive training run."""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Sequence
from pathlib import Path

# Must be set before CUDA is first used so deterministic cuBLAS applies to every step.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

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


STAGE1_PROBE_STEPS = 600


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="step budget of the 4-patient probe; default 150, or 600 for "
        "stage1_seg (D-054: Dice loss on four patients needs about 410 steps to "
        "pass 0.5)",
    )
    parser.add_argument(
        "--overfit-threshold",
        type=float,
        default=None,
        help="loss the 4-patient probe must go below; default 0.05 (class-balanced "
        "BCE), or 0.5 for stage1_seg (Dice loss, a wiring check not a result)",
    )
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument(
        "--variant",
        choices=("base", "whole_brain", "stage1_seg", "stage2_cls"),
        default="base",
        help="model variant the report authorizes: R7 whole_brain, "
        "R8 stage1_seg or stage2_cls (D-051)",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.max_steps is None:
        args.max_steps = STAGE1_PROBE_STEPS if args.variant == "stage1_seg" else 150
    if args.max_steps < 1:
        parser.error("--max-steps must be at least one")
    if args.overfit_threshold is None:
        args.overfit_threshold = 0.5 if args.variant == "stage1_seg" else 0.05
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
        variant=args.variant,
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

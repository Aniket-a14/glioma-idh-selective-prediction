#!/usr/bin/env python3
"""Train one Phase 06 model on the frozen UTSW training split (pilot, R1, R2)."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

# Must be set before CUDA is first used so deterministic cuBLAS applies (D-040).
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for import_root in (REPOSITORY_ROOT, SOURCE_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True, help="run label, e.g. pilot, r1, r2")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--modality-dropout",
        action="store_true",
        help="train with the D-041 modality-dropout schedule (R2 and later)",
    )
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--authorization-report",
        type=Path,
        required=True,
        help="report from scripts/authorize_training.py on this machine and commit",
    )
    parser.add_argument("--resume", metavar="RUN_ID", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    import torch

    from glioma_selective.training.run import RunSpec, train_run

    device = torch.device(
        "cuda"
        if args.device == "auto" and torch.cuda.is_available()
        else ("cpu" if args.device == "auto" else args.device)
    )
    spec = RunSpec(
        label=args.label,
        seed=args.seed,
        modality_dropout=args.modality_dropout,
        max_epochs=args.max_epochs,
        num_workers=args.num_workers,
        resume_run_id=args.resume,
    )
    run_id, result = train_run(
        spec, authorization_report=args.authorization_report, device=device
    )
    print(
        f"run {run_id}: epochs={result.state.epoch} "
        f"best_epoch={result.state.best_epoch} "
        f"best_calibration_loss={result.state.best_value:.5f} "
        f"stopped_early={result.stopped_early}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Freeze head-only MC-dropout predictions for a completed run."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for import_root in (REPOSITORY_ROOT, SOURCE_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="completed run ULID")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cpu")
    parser.add_argument("--passes", type=int, default=30)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument(
        "--allow-sha-mismatch",
        action="store_true",
        help="score with this tree and record both code SHAs in artifact metadata",
    )
    args = parser.parse_args(argv)
    from glioma_selective.evaluation.freeze_mc_dropout import freeze_mc_dropout

    freeze_mc_dropout(
        args.run_id,
        device=args.device,
        passes=args.passes,
        seed=args.seed,
        batch_size=args.batch_size,
        allow_sha_mismatch=args.allow_sha_mismatch,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

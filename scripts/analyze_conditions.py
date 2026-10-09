#!/usr/bin/env python3
"""Analyze frozen internal predictions across the six modality conditions."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPOSITORY_ROOT, REPOSITORY_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="completed run ULID")
    args = parser.parse_args(argv)
    from glioma_selective.evaluation.condition_analysis import analyze_conditions

    analyze_conditions(args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

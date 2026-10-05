#!/usr/bin/env python3
"""Report Phase 06 internal-test metrics from a frozen prediction artifact."""

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
    args = parser.parse_args(argv)
    from glioma_selective.evaluation.phase06_report import report_phase06

    report_phase06(args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

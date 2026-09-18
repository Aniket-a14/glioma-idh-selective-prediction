#!/usr/bin/env python3
"""Inventory naturally missing core MRI sequences in the raw cohorts.

The default output is ``paths.manifests_dir() /
"naturally_missing_sequence_inventory.json"``. The output is derived from
the raw download and is not a committed manifest. It contains aggregate counts
only; no patient identifiers are written.

This is distinct from Phase 08 simulated missingness. Phase 08 deliberately
drops sequences from complete studies to construct controlled conditions. This
script only counts sequences that were absent from the raw download already.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

# Running this file directly does not put ``src/`` on sys.path.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.data import missing_sequences  # noqa: E402
from glioma_selective.data.adapters import ucsf_pdgm, utsw  # noqa: E402
from glioma_selective.data.adapters._common import (  # noqa: E402
    PatientFileInventory,
)
from glioma_selective.utils import paths  # noqa: E402

COHORT_NAMES: tuple[str, ...] = ("utsw", "ucsf_pdgm")
_DISCOVERERS: dict[str, Callable[[], tuple[PatientFileInventory, ...]]] = {
    "utsw": utsw.discover_files,
    "ucsf_pdgm": ucsf_pdgm.discover_files,
}


def discover_cohorts(
    cohorts: Sequence[str] = COHORT_NAMES,
) -> dict[str, tuple[PatientFileInventory, ...]]:
    """Discover selected cohorts through their existing Phase 02 adapters."""

    return {cohort: _DISCOVERERS[cohort]() for cohort in cohorts}


def main(argv: Sequence[str] | None = None) -> int:
    """Write the aggregate naturally-missingness report and print its summary."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort",
        choices=("all", *COHORT_NAMES),
        default="all",
        help="cohort to inventory (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "report path (default: "
            "paths.manifests_dir()/naturally_missing_sequence_inventory.json)"
        ),
    )
    args = parser.parse_args(argv)

    cohorts = COHORT_NAMES if args.cohort == "all" else (args.cohort,)
    output = args.output or (
        paths.manifests_dir() / "naturally_missing_sequence_inventory.json"
    )
    try:
        report = missing_sequences.build_report(discover_cohorts(cohorts))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (KeyError, FileNotFoundError, NotADirectoryError, OSError) as exc:
        print(f"inventory_missing_sequences.py: error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"output": str(output), "cohorts": report["cohorts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

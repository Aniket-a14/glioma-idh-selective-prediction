"""Phase 13: single BH pass over the 29-test family and the final claim table.

Reads aggregate files only. Pass the four frozen Phase 09/10 analysis files and
an output path (see --help).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from glioma_selective.evaluation.phase13_final import finalize


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("internal09", "internal10", "external09", "external10", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    print(
        finalize(
            args.internal09,
            args.internal10,
            args.external09,
            args.external10,
            args.output,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

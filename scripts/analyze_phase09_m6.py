"""CLI: write the M6 cells (D-056, M6 = R1) beside a run's Phase 09 file."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from glioma_selective.evaluation.phase09_analysis import analyze_phase09_m6


def main(argv: Sequence[str] | None = None) -> int:
    """Run the M6 cell analysis on frozen condition artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--m6-run-id", required=True)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    arguments = parser.parse_args(argv)
    print(
        analyze_phase09_m6(
            arguments.run_id,
            arguments.m6_run_id,
            iterations=arguments.iterations,
            permutations=arguments.permutations,
            seed=arguments.seed,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

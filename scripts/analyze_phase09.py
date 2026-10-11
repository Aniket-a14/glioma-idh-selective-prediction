"""CLI for assembling Phase 09 results from frozen prediction artifacts."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from glioma_selective.evaluation.phase09_analysis import analyze_phase09


def main(argv: Sequence[str] | None = None) -> int:
    """Run the internal Phase 09 frozen-artifact analysis."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--ensemble-run-id", action="append", dest="ensemble_run_ids")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--passes", type=int, default=30)
    arguments = parser.parse_args(argv)
    result_path = analyze_phase09(
        arguments.run_id,
        ensemble_run_ids=arguments.ensemble_run_ids,
        iterations=arguments.iterations,
        permutations=arguments.permutations,
        seed=arguments.seed,
        passes=arguments.passes,
    )
    print(result_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

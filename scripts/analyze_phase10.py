"""CLI for Phase 10 internal statistics from frozen prediction artifacts."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from glioma_selective.evaluation.phase10_analysis import analyze_phase10


def main(argv: Sequence[str] | None = None) -> int:
    """Assemble S4 without model inference or external data access."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--ensemble-run-id", action="append", dest="ensemble_run_ids", required=True
    )
    parser.add_argument("--r7-run-id")
    parser.add_argument("--r8-run-id")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    arguments = parser.parse_args(argv)
    result = analyze_phase10(
        arguments.run_id,
        ensemble_run_ids=arguments.ensemble_run_ids,
        r7_run_id=arguments.r7_run_id,
        r8_run_id=arguments.r8_run_id,
        iterations=arguments.iterations,
        seed=arguments.seed,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI: Phase 12 analysis of frozen external predictions, behind Gate E.

Needs ``GLIOMA_EXTERNAL_EVAL_AUTHORIZED=1`` and a signed freeze manifest; the
Research Lead sets the flag for this command only. Prints the two output paths
and nothing else: no metric and no patient value reaches the terminal.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from glioma_selective.evaluation.phase12_analysis import analyze_external


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="primary internal run (R2)")
    parser.add_argument("--external-run", required=True, help="frozen external run id")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--ablation-run", help="second frozen run with R7 and R8")
    parser.add_argument("--ablation-manifest", type=Path)
    parser.add_argument("--cohort", default="ucsf_pdgm", choices=("ucsf_pdgm",))
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--permutations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    arguments = parser.parse_args(argv)
    for path in analyze_external(
        arguments.run_id,
        arguments.external_run,
        arguments.manifest,
        ablation_run_id=arguments.ablation_run,
        ablation_manifest_path=arguments.ablation_manifest,
        cohort=arguments.cohort,
        iterations=arguments.iterations,
        permutations=arguments.permutations,
        seed=arguments.seed,
    ):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Phase 07 scientific validation 1: conformal coverage under exchangeability.

Two checks of the split-conformal code in ``calibration/conformal.py``:
1. synthetic exchangeable scores (28% positives), 124 calibration and 124 test
   patients;
2. random 124/124 re-splits of a run's pooled UTSW calibration and internal-test
   patients (temperature refitted on each calibration half), if ``--run-id`` is
   given. Internal data only.

Prints the mean and standard deviation of empirical coverage over the replications for
each alpha. No external cohort is read.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

import numpy as np

from glioma_selective.calibration.conformal import (
    conformal_quantile,
    empirical_coverage,
    nonconformity_scores,
    prediction_sets,
)
from glioma_selective.calibration.temperature import apply_temperature, fit_temperature

ALPHAS = (0.05, 0.1, 0.2)


def _coverage(
    cal_p: np.ndarray,
    cal_y: np.ndarray,
    test_p: np.ndarray,
    test_y: np.ndarray,
    alpha: float,
) -> float:
    quantile = conformal_quantile(
        nonconformity_scores(cal_p.tolist(), cal_y.tolist()), alpha
    )
    return empirical_coverage(
        prediction_sets(test_p.tolist(), quantile), test_y.tolist()
    )


def synthetic(reps: int, seed: int, n: int = 124) -> dict[float, tuple[float, float]]:
    """Mean and SD of coverage for exchangeable synthetic calibration/test draws."""
    rng = np.random.default_rng(seed)

    def draw() -> tuple[np.ndarray, np.ndarray]:
        y = (rng.random(n) < 0.28).astype(int)
        z = np.where(y == 1, 1.5, -1.5) + rng.normal(0, 1.6, n)
        return 1 / (1 + np.exp(-z)), y

    out: dict[float, list[float]] = {a: [] for a in ALPHAS}
    for _ in range(reps):
        cal_p, cal_y = draw()
        test_p, test_y = draw()
        for alpha in ALPHAS:
            out[alpha].append(_coverage(cal_p, cal_y, test_p, test_y, alpha))
    return {a: (float(np.mean(v)), float(np.std(v))) for a, v in out.items()}


def resplit(
    logit: np.ndarray, label: np.ndarray, reps: int, seed: int, half: int = 124
) -> dict[float, tuple[float, float]]:
    """Mean and SD of coverage over random re-splits of the pooled patients."""
    rng = np.random.default_rng(seed)
    out: dict[float, list[float]] = {a: [] for a in ALPHAS}
    for _ in range(reps):
        order = rng.permutation(len(label))
        cal, test = order[:half], order[half:]
        temperature = fit_temperature(logit[cal], label[cal])
        cal_p = apply_temperature(logit[cal], temperature)
        test_p = apply_temperature(logit[test], temperature)
        for alpha in ALPHAS:
            out[alpha].append(_coverage(cal_p, label[cal], test_p, label[test], alpha))
    return {a: (float(np.mean(v)), float(np.std(v))) for a, v in out.items()}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--run-id", help="also re-split this run's pooled internal predictions"
    )
    arguments = parser.parse_args(argv)
    print("synthetic, 124/124 (nominal: mean coverage, sd):")
    for alpha, (mean, sd) in synthetic(arguments.reps, arguments.seed).items():
        print(f"  {1 - alpha:.2f}: {mean:.3f}, {sd:.3f}")
    if arguments.run_id:
        import pandas as pd

        from glioma_selective.utils import paths

        frame = pd.read_parquet(
            paths.experiments_dir() / arguments.run_id / "predictions.parquet"
        )
        frame = frame[frame["modality_condition"] == "full"]
        logit = frame["logit"].to_numpy(float)
        label = frame["label"].to_numpy(int)
        print(
            f"{arguments.run_id} pooled re-splits, n={len(label)} (nominal: mean, sd):"
        )
        for alpha, (mean, sd) in resplit(
            logit, label, arguments.reps, arguments.seed
        ).items():
            print(f"  {1 - alpha:.2f}: {mean:.3f}, {sd:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

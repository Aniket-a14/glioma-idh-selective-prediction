"""Two-stage coverage-deviation bootstrap for conformal sets (D5, C4, T09.5).

Contract: ``docs/research/protocols/PHASE09_STATS_CONTRACTS.md``. Each draw
resamples the calibration patients, refits the split-conformal quantile, then
resamples the evaluation patients and measures the empirical coverage of the
sets at that quantile. The deviation is empirical minus nominal coverage
(SAP section 4). Randomness comes only from ``numpy.random.default_rng(seed)``,
in the fixed order calibration indices, then test indices, per iteration.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

from glioma_selective.calibration.conformal import (
    conformal_quantile,
    empirical_coverage,
    nonconformity_scores,
    prediction_sets,
)

__all__ = ["coverage_deviation_bootstrap"]


def coverage_deviation_bootstrap(
    cal_p: Sequence[float],
    cal_labels: Sequence[int],
    test_p: Sequence[float],
    test_labels: Sequence[int],
    alpha: float,
    iterations: int,
    seed: int,
) -> NDArray[np.float64]:
    """``iterations`` draws of ``coverage - (1 - alpha)`` under two-stage resampling.

    ``cal_p`` and ``test_p`` are P(mutant) after the calibration split's
    temperature. Each draw pairs one calibration resample with one test
    resample. An empty or infinite quantile is handled by the conformal module
    (``+inf`` puts every label in every set, coverage 1).
    """
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    n_cal = len(cal_p)
    n_test = len(test_p)
    if n_cal == 0 or n_test == 0:
        raise ValueError("calibration and test inputs must not be empty")
    if len(cal_labels) != n_cal or len(test_labels) != n_test:
        raise ValueError("probabilities and labels must have equal lengths")
    cal_p_arr = np.asarray(cal_p, dtype=np.float64)
    cal_y = np.asarray(cal_labels, dtype=np.int64)
    test_p_arr = np.asarray(test_p, dtype=np.float64)
    test_y = np.asarray(test_labels, dtype=np.int64)
    rng = np.random.default_rng(seed)
    nominal = 1.0 - alpha
    draws = np.empty(iterations, dtype=np.float64)
    for b in range(iterations):
        ci = rng.integers(0, n_cal, n_cal)
        quantile = conformal_quantile(
            nonconformity_scores(cal_p_arr[ci].tolist(), cal_y[ci].tolist()), alpha
        )
        ti = rng.integers(0, n_test, n_test)
        sets = prediction_sets(test_p_arr[ti].tolist(), quantile)
        draws[b] = empirical_coverage(sets, test_y[ti].tolist()) - nominal
    return draws

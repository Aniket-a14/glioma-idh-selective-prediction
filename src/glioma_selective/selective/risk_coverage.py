"""Risk-coverage points with tie blocks, and monotonicity violations (S1, S4).

Contract: ``docs/research/protocols/PHASE09_METRIC_CONTRACTS.md``. Scores are
"higher is more confident, accepted first". Equal scores form one block that is
never split, so the curve does not depend on the row order of the input
(D-033). Every comparison and mean is exact (``Fraction(repr(x))``) and the
result is rounded to a float once.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

__all__ = ["monotonicity_total_bootstrap", "monotonicity_violations", "rc_points"]


def _exact(value: float, what: str) -> Fraction:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{what} must be finite")
    return Fraction(repr(number))


def rc_points(
    scores: Sequence[float], losses: Sequence[float]
) -> list[tuple[float, float]]:
    """One ``(coverage, risk)`` point per tie block, at the block's end (S1).

    Coverage is the share of patients up to and including the block; risk is
    the mean loss of those patients. Coverage strictly increases and the last
    point has coverage 1 and risk equal to the mean loss.
    """
    if len(scores) == 0:
        raise ValueError("scores must not be empty")
    if len(scores) != len(losses):
        raise ValueError("scores and losses must have equal lengths")
    exact_scores = [_exact(score, "scores") for score in scores]
    exact_losses = [_exact(loss, "losses") for loss in losses]
    if any(loss < 0 for loss in exact_losses):
        raise ValueError("losses must be non-negative")
    n = len(exact_scores)
    order = sorted(range(n), key=lambda index: -exact_scores[index])
    points: list[tuple[float, float]] = []
    total = Fraction(0)
    position = 0
    while position < n:
        end = position
        while (
            end + 1 < n
            and exact_scores[order[end + 1]] == exact_scores[order[position]]
        ):
            end += 1
        for index in order[position : end + 1]:
            total += exact_losses[index]
        accepted = end + 1
        points.append((float(Fraction(accepted, n)), float(total / accepted)))
        position = end + 1
    return points


def monotonicity_violations(
    points: Sequence[tuple[float, float]],
) -> tuple[int, float]:
    """Count and total size of risk drops as coverage grows (S4, T09.6).

    Over every pair ``i < j`` of points with ``risk_i > risk_j`` (the point at
    lower coverage has the higher risk), returns the number of such pairs and
    the sum of ``risk_i - risk_j``. ``(0, 0.0)`` for a non-decreasing risk
    sequence. Every such pair works against C5.
    """
    if len(points) == 0:
        raise ValueError("points must not be empty")
    coverage = [_exact(point[0], "coverage") for point in points]
    risk = [_exact(point[1], "risk") for point in points]
    if any(
        later <= earlier for earlier, later in zip(coverage, coverage[1:], strict=False)
    ):
        raise ValueError("coverage must be strictly increasing")
    count = 0
    total = Fraction(0)
    for i in range(len(risk)):
        for j in range(i + 1, len(risk)):
            if risk[i] > risk[j]:
                count += 1
                total += risk[i] - risk[j]
    return count, float(total)


def monotonicity_total_bootstrap(
    scores: Sequence[float], losses: Sequence[float], iterations: int, seed: int
) -> NDArray[np.float64]:
    """Patient-level bootstrap of the S4 violation magnitude (D6, T09.6).

    Per iteration draw ``idx = rng.integers(0, n, n)`` from
    ``numpy.random.default_rng(seed)``, build the S1 points of the resampled
    ``scores`` and ``losses``, and take the S4 magnitude sum. Returns the array
    of ``iterations`` totals. A small total that the interval puts near zero is
    finite-sample noise; a total whose interval stays above zero is a
    systematic reversal.
    """
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if len(scores) == 0 or len(scores) != len(losses):
        raise ValueError("scores and losses must be non-empty and of equal length")
    score_arr = np.asarray(scores, dtype=np.float64)
    loss_arr = np.asarray(losses, dtype=np.float64)
    n = len(score_arr)
    rng = np.random.default_rng(seed)
    totals = np.empty(iterations, dtype=np.float64)
    for b in range(iterations):
        idx = rng.integers(0, n, n)
        _, magnitude = monotonicity_violations(
            rc_points(score_arr[idx].tolist(), loss_arr[idx].tolist())
        )
        totals[b] = magnitude
    return totals

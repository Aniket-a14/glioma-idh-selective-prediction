"""Split conformal prediction for a binary IDH label (M5, D-002, D-045).

Contract: ``docs/research/protocols/PHASE07_METRIC_CONTRACTS.md`` K1 to K3.
Everything that decides an index or a set membership uses exact rational
arithmetic on the decimal value of each float (``Fraction(repr(x))``), because
``1 - 0.7 > 0.3`` in floating point and a set built from that comparison would
lose a label it should keep. Scores are rounded once, correctly, to a double;
the calibration split and the test patients use the same function, so a
calibration point always sits inside its own set.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction

__all__ = [
    "conformal_quantile",
    "conformal_summary",
    "empirical_coverage",
    "nonconformity_score",
    "nonconformity_scores",
    "prediction_set",
    "prediction_sets",
]


def _exact(value: float) -> Fraction:
    return Fraction(repr(float(value)))


def _probability(value: float) -> Fraction:
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError("probability must be finite and in [0, 1]")
    return _exact(number)


def _label(value: int) -> int:
    if value not in (0, 1):
        raise ValueError("labels must be 0 or 1")
    return int(value)


def _alpha(alpha: float) -> Fraction:
    number = float(alpha)
    if not math.isfinite(number) or not 0.0 < number < 1.0:
        raise ValueError("alpha must be finite and in (0, 1)")
    return _exact(number)


def nonconformity_score(p_hat: float, label: int) -> float:
    """``1 - p(true class)``: ``1 - p_hat`` for label 1, ``p_hat`` for label 0 (K1)."""
    probability = _probability(p_hat)
    target = _label(label)
    return float(1 - probability if target == 1 else probability)


def nonconformity_scores(p_hat: Sequence[float], labels: Sequence[int]) -> list[float]:
    """``nonconformity_score`` for each patient."""
    if len(p_hat) != len(labels):
        raise ValueError("p_hat and labels must have equal lengths")
    return [nonconformity_score(p, y) for p, y in zip(p_hat, labels, strict=True)]


def conformal_quantile(scores: Sequence[float], alpha: float) -> float:
    """The ``ceil((n + 1) * (1 - alpha))``-th smallest score, or ``+inf`` (K2).

    With ``n`` calibration scores the finite-sample correction asks for the
    ``k``-th order statistic, ``k = ceil((n + 1)(1 - alpha))``. When ``k > n`` no
    finite threshold carries the guarantee, so the answer is ``+inf`` and every
    label stays in every set. The result is a member of ``scores`` or ``+inf``.
    """
    values = [float(score) for score in scores]
    if not values:
        raise ValueError("scores must not be empty")
    if any(not math.isfinite(score) for score in values):
        raise ValueError("scores must be finite")
    level = _alpha(alpha)
    n = len(values)
    k = math.ceil((n + 1) * (1 - level))
    if k > n:
        return math.inf
    return sorted(values)[k - 1]


def prediction_set(p_hat: float, quantile: float) -> tuple[int, ...]:
    """Labels whose nonconformity score is at most ``quantile`` (K3).

    Class 1 is in the set iff ``1 - p_hat <= quantile``, class 0 iff
    ``p_hat <= quantile``, both evaluated with the same scoring function the
    calibration split used. Returns ``()``, ``(0,)``, ``(1,)`` or ``(0, 1)``.
    """
    if math.isnan(quantile):
        raise ValueError("quantile must not be NaN")
    return tuple(
        label for label in (0, 1) if nonconformity_score(p_hat, label) <= quantile
    )


def prediction_sets(p_hat: Sequence[float], quantile: float) -> list[tuple[int, ...]]:
    """``prediction_set`` for each patient."""
    return [prediction_set(p, quantile) for p in p_hat]


def empirical_coverage(sets: Sequence[tuple[int, ...]], labels: Sequence[int]) -> float:
    """Fraction of patients whose true label is in their set."""
    if not labels:
        raise ValueError("labels must not be empty")
    if len(sets) != len(labels):
        raise ValueError("sets and labels must have equal lengths")
    covered = sum(_label(y) in s for s, y in zip(sets, labels, strict=True))
    return covered / len(labels)


def conformal_summary(
    sets: Sequence[tuple[int, ...]], labels: Sequence[int]
) -> dict[str, float]:
    """Coverage and abstention rates (abstain unless the set is a singleton, D-003)."""
    coverage = empirical_coverage(sets, labels)
    n = len(labels)
    return {
        "coverage": coverage,
        "abstention_rate": sum(len(s) != 1 for s in sets) / n,
        "empty_rate": sum(len(s) == 0 for s in sets) / n,
        "full_rate": sum(len(s) == 2 for s in sets) / n,
    }

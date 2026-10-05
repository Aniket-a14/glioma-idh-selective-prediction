"""Independent standard-library reference for split conformal prediction."""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction


def _probability(value: float) -> Fraction:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("probability must be numeric") from error
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
        raise ValueError("probability must be finite and in [0, 1]")
    return Fraction(repr(numeric))


def _label(value: int) -> int:
    if value not in (0, 1):
        raise ValueError("label must be 0 or 1")
    return int(value)


def _alpha(value: float) -> Fraction:
    try:
        exact = Fraction(repr(value))
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("alpha must be numeric and in (0, 1)") from error
    if not 0 < exact < 1:
        raise ValueError("alpha must be in (0, 1)")
    return exact


def nonconformity_score(p_hat: float, label: int) -> float:
    """Return ``1 - p(true class)`` using decimal-exact subtraction."""
    probability = _probability(p_hat)
    target = _label(label)
    score = 1 - probability if target == 1 else probability
    return float(score)


def conformal_quantile(scores: Sequence[float], alpha: float) -> float:
    """Return the corrected k-th order statistic or positive infinity."""
    values = list(scores)
    if not values:
        raise ValueError("scores must not be empty")
    exact_scores: list[tuple[Fraction, float]] = []
    for score in values:
        try:
            numeric = float(score)
        except (TypeError, ValueError) as error:
            raise ValueError("scores must be numeric") from error
        if not math.isfinite(numeric):
            raise ValueError("scores must be finite")
        exact_scores.append((Fraction(repr(numeric)), numeric))

    exact_alpha = _alpha(alpha)
    rank_fraction = (len(exact_scores) + 1) * (1 - exact_alpha)
    rank = (
        rank_fraction.numerator + rank_fraction.denominator - 1
    ) // rank_fraction.denominator
    if rank > len(exact_scores):
        return math.inf
    ordered = sorted(exact_scores, key=lambda item: item[0])
    return ordered[rank - 1][1]


def prediction_set(p_hat: float, q: float) -> tuple[int, ...]:
    """Return labels whose exact-decimal nonconformity score is at most q."""
    probability = _probability(p_hat)
    try:
        threshold = float(q)
    except (TypeError, ValueError) as error:
        raise ValueError("q must be numeric") from error
    if math.isnan(threshold) or threshold < 0.0:
        raise ValueError("q must be non-negative and not NaN")
    if math.isinf(threshold):
        if threshold > 0:
            return (0, 1)
        raise ValueError("q must be non-negative and not NaN")
    exact_threshold = Fraction(repr(threshold))
    included: list[int] = []
    if probability <= exact_threshold:
        included.append(0)
    if 1 - probability <= exact_threshold:
        included.append(1)
    return tuple(included)


def conformal_summary(
    prediction_sets: Sequence[Sequence[int]], labels: Sequence[int]
) -> dict[str, float]:
    """Return coverage, abstention, empty-set, and full-set rates."""
    sets = list(prediction_sets)
    targets = [_label(label) for label in labels]
    if not sets:
        raise ValueError("prediction sets and labels must not be empty")
    if len(sets) != len(targets):
        raise ValueError("prediction sets and labels must have equal lengths")
    normalized: list[tuple[int, ...]] = []
    for values in sets:
        current = tuple(values)
        if current not in ((), (0,), (1,), (0, 1)):
            raise ValueError("prediction sets must be sorted subsets of {0, 1}")
        normalized.append(current)
    count = len(normalized)
    return {
        "coverage": sum(
            target in prediction
            for target, prediction in zip(targets, normalized, strict=True)
        )
        / count,
        "abstention_rate": sum(len(prediction) != 1 for prediction in normalized)
        / count,
        "empty_rate": sum(not prediction for prediction in normalized) / count,
        "full_rate": sum(len(prediction) == 2 for prediction in normalized) / count,
    }


def empirical_coverage(
    prediction_sets: Sequence[Sequence[int]], labels: Sequence[int]
) -> float:
    """Return the fraction of labels included in their corresponding sets."""
    return conformal_summary(prediction_sets, labels)["coverage"]

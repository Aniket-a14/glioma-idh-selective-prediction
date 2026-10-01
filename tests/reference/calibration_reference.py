"""Independent standard-library reference metrics for calibration tests.

This module deliberately has no project imports.  It implements the contracts
in C-017 directly so that the later production metrics can be checked against
an independent calculation.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any


def _validated_inputs(
    probs: list[float], labels: list[int]
) -> tuple[list[float], list[int]]:
    probabilities = list(probs)
    targets = list(labels)
    if not probabilities:
        raise ValueError("inputs must not be empty")
    if len(probabilities) != len(targets):
        raise ValueError("probabilities and labels must have equal lengths")

    checked_probabilities: list[float] = []
    for probability in probabilities:
        try:
            numeric = float(probability)
        except (TypeError, ValueError) as error:
            raise ValueError("probability must be numeric") from error
        if not math.isfinite(numeric) or not 0.0 <= numeric <= 1.0:
            raise ValueError("probability must be finite and in [0, 1]")
        checked_probabilities.append(numeric)

    checked_labels: list[int] = []
    for label in targets:
        if label not in (0, 1):
            raise ValueError("labels must be 0 or 1")
        checked_labels.append(int(label))
    return checked_probabilities, checked_labels


def _validated_bins(n_bins: int, scheme: str) -> None:
    if isinstance(n_bins, bool) or not isinstance(n_bins, int) or n_bins < 1:
        raise ValueError("n_bins must be at least 1")
    if scheme not in {"equal_width", "equal_mass"}:
        raise ValueError(f"unknown binning scheme: {scheme}")


def brier_score(probs: list[float], labels: list[int]) -> float:
    """Return the mean squared probability error, ``mean((p - y) ** 2)``."""

    probabilities, targets = _validated_inputs(probs, labels)
    return sum(
        (probability - label) ** 2
        for probability, label in zip(probabilities, targets, strict=False)
    ) / len(targets)


def _score_and_observation(
    probability: float, label: int, variant: str
) -> tuple[float, int]:
    if variant == "positive_class":
        return probability, label
    if variant == "top_label":
        predicted = 1 if probability > 0.5 else 0
        return max(probability, 1.0 - probability), int(predicted == label)
    raise ValueError(f"unknown calibration variant: {variant}")


def _edge(value: float) -> Fraction:
    """Build an exact edge value from the input's decimal spelling."""

    return Fraction(str(value))


def _in_equal_width_bin(
    score: float, index: int, n_bins: int, right_closed: bool
) -> bool:
    value = _edge(score)
    lower = Fraction(index, n_bins)
    upper = Fraction(index + 1, n_bins)
    if right_closed:
        lower_ok = value >= lower if index == 0 else value > lower
        return lower_ok and value <= upper
    upper_ok = value <= upper if index == n_bins - 1 else value < upper
    return value >= lower and upper_ok


def _empty_bin(lower: float | None, upper: float | None) -> dict[str, Any]:
    return {
        "lower": lower,
        "upper": upper,
        "count": 0,
        "mean_confidence": None,
        "observed": None,
    }


def _filled_bin(
    scores: list[float], observations: list[int], lower: float, upper: float
) -> dict[str, Any]:
    return {
        "lower": lower,
        "upper": upper,
        "count": len(scores),
        "mean_confidence": sum(scores) / len(scores),
        "observed": sum(observations) / len(observations),
    }


def reliability_bins(
    probs: list[float],
    labels: list[int],
    n_bins: int,
    scheme: str = "equal_width",
    right_closed: bool = False,
    variant: str = "positive_class",
) -> list[dict[str, Any]]:
    """Return calibration bins for every named ECE convention."""

    probabilities, targets = _validated_inputs(probs, labels)
    _validated_bins(n_bins, scheme)
    if variant not in {"positive_class", "top_label"}:
        raise ValueError(f"unknown calibration variant: {variant}")

    scored = [
        _score_and_observation(probability, label, variant)
        for probability, label in zip(probabilities, targets, strict=False)
    ]

    if scheme == "equal_mass":
        ordered = sorted(enumerate(scored), key=lambda item: item[1][0])
        base, remainder = divmod(len(ordered), n_bins)
        result: list[dict[str, Any]] = []
        offset = 0
        for index in range(n_bins):
            group_size = base + int(index < remainder)
            group = [item[1] for item in ordered[offset : offset + group_size]]
            offset += group_size
            if not group:
                result.append(_empty_bin(None, None))
                continue
            group_scores = [item[0] for item in group]
            group_observations = [item[1] for item in group]
            result.append(
                _filled_bin(
                    group_scores,
                    group_observations,
                    min(group_scores),
                    max(group_scores),
                )
            )
        return result

    result = []
    for index in range(n_bins):
        lower = index / n_bins
        upper = (index + 1) / n_bins
        bin_items = [
            item
            for item in scored
            if _in_equal_width_bin(item[0], index, n_bins, right_closed)
        ]
        if not bin_items:
            result.append(_empty_bin(lower, upper))
            continue
        result.append(
            _filled_bin(
                [item[0] for item in bin_items],
                [item[1] for item in bin_items],
                lower,
                upper,
            )
        )
    return result


def ece(
    probs: list[float],
    labels: list[int],
    n_bins: int,
    scheme: str = "equal_width",
    right_closed: bool = False,
    variant: str = "positive_class",
) -> float:
    """Return count-weighted expected calibration error."""

    bins = reliability_bins(probs, labels, n_bins, scheme, right_closed, variant)
    total = len(probs)
    return sum(
        (entry["count"] / total) * abs(entry["observed"] - entry["mean_confidence"])
        for entry in bins
        if entry["count"]
    )


def mce(
    probs: list[float],
    labels: list[int],
    n_bins: int,
    scheme: str = "equal_width",
    right_closed: bool = False,
    variant: str = "positive_class",
) -> float:
    """Return the largest non-empty-bin calibration error."""

    bins = reliability_bins(probs, labels, n_bins, scheme, right_closed, variant)
    errors = [
        abs(entry["observed"] - entry["mean_confidence"])
        for entry in bins
        if entry["count"]
    ]
    return max(errors, default=0.0)


def _exact_alpha(alpha: int | str | float | Fraction) -> Fraction:
    try:
        exact = Fraction(str(alpha))
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("alpha must be an exact fraction") from error
    if not 0 < exact < 1:
        raise ValueError("alpha must be in (0, 1)")
    return exact


def conformal_rank(n: int, alpha: int | str | float | Fraction) -> int:
    """Return ``ceil((n + 1) * (1 - alpha))`` using exact arithmetic."""

    if isinstance(n, bool) or not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")
    exact_alpha = _exact_alpha(alpha)
    value = (n + 1) * (1 - exact_alpha)
    return (value.numerator + value.denominator - 1) // value.denominator


def conformal_quantile(
    scores: list[float], alpha: int | str | float | Fraction
) -> float:
    """Return the exact finite-sample order statistic or ``math.inf``."""

    values = list(scores)
    if not values:
        raise ValueError("scores must not be empty")
    checked: list[float] = []
    for score in values:
        try:
            numeric = float(score)
        except (TypeError, ValueError) as error:
            raise ValueError("scores must be numeric") from error
        if math.isnan(numeric):
            raise ValueError("scores must not contain NaN")
        checked.append(numeric)
    rank = conformal_rank(len(checked), alpha)
    if rank > len(checked):
        return math.inf
    return sorted(checked)[rank - 1]

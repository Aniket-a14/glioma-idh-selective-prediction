"""Paired AUROC comparison defined by the Phase 10 statistics contract."""

from __future__ import annotations

import math
from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from numbers import Real

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class DeLongResult:
    """Paired AUROCs, their difference, and the two-sided DeLong test."""

    auc_a: float
    auc_b: float
    difference: float
    variance: float
    z: float
    p_value: float
    n_positive: int
    n_negative: int


def _real_values(values: Sequence[Real] | NDArray[np.generic], name: str) -> list[Real]:
    """Validate finite one-dimensional inputs without rounding exact scores."""
    try:
        raw_values = list(values)
    except TypeError as error:
        raise ValueError(f"{name} must be a one-dimensional sequence") from error
    if not raw_values:
        raise ValueError(f"{name} must not be empty")
    result: list[Real] = []
    for value in raw_values:
        if isinstance(value, np.generic):
            value = value.item()
        if not isinstance(value, Real):
            raise ValueError(f"{name} must contain finite real numbers")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{name} must contain finite real numbers")
        result.append(value)
    return result


def _placements(
    scores: list[Real], labels: list[Real]
) -> tuple[Fraction, list[Fraction], list[Fraction]]:
    """Count half-credit wins using sorted opposite-class scores."""
    positives = [
        score for score, label in zip(scores, labels, strict=True) if label == 1
    ]
    negatives = [
        score for score, label in zip(scores, labels, strict=True) if label == 0
    ]
    sorted_positive, sorted_negative = sorted(positives), sorted(negatives)
    m, n = len(positives), len(negatives)
    v10 = [
        Fraction(
            bisect_left(sorted_negative, score) + bisect_right(sorted_negative, score),
            2 * n,
        )
        for score in positives
    ]
    v01 = [
        Fraction(
            2 * m
            - bisect_left(sorted_positive, score)
            - bisect_right(sorted_positive, score),
            2 * m,
        )
        for score in negatives
    ]
    return sum(v10, Fraction(0)) / m, v10, v01


def delong_paired_auroc(
    scores_a: Sequence[Real] | NDArray[np.generic],
    scores_b: Sequence[Real] | NDArray[np.generic],
    labels: Sequence[Real] | NDArray[np.generic],
) -> DeLongResult:
    """Compare paired AUROCs with half-credit ties and unbiased covariances.

    The variance contracts S10/m + S01/n with (1, -1). Equivalently it is
    the sum of the sample variances of paired placement differences divided
    by their class sizes. Placements, AUCs, and variance stay rational until
    conversion into the result; exact input scores are never rounded.
    """
    a = _real_values(scores_a, "scores_a")
    b = _real_values(scores_b, "scores_b")
    y = _real_values(labels, "labels")
    if len(a) != len(b) or len(a) != len(y):
        raise ValueError("scores_a, scores_b and labels must have equal lengths")
    if any(label not in (0, 1) for label in y):
        raise ValueError("labels values must be 0 or 1")
    m = sum(label == 1 for label in y)
    n = len(y) - m
    if m < 2 or n < 2:
        raise ValueError("at least two positive and two negative patients are required")
    auc_a, a10, a01 = _placements(a, y)
    auc_b, b10, b01 = _placements(b, y)
    difference = auc_a - auc_b
    variance = sum(
        (
            sum(
                ((u - v - difference) ** 2 for u, v in zip(left, right, strict=True)),
                Fraction(0),
            )
            / (size * (size - 1))
            for left, right, size in ((a10, b10, m), (a01, b01, n))
        ),
        Fraction(0),
    )
    if variance == 0:
        z = 0.0 if difference == 0 else math.copysign(math.inf, difference)
    else:
        z = float(difference) / math.sqrt(float(variance))
    return DeLongResult(
        float(auc_a),
        float(auc_b),
        float(difference),
        float(variance),
        z,
        math.erfc(abs(z) / math.sqrt(2)),
        m,
        n,
    )

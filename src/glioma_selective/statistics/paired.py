"""Paired patient bootstrap defined by the Phase 10 statistics contract."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray

from glioma_selective.statistics.resampling import (
    _finite_values,
    bootstrap_indices,
    percentile_interval,
)


@dataclass(frozen=True)
class PairedBootstrapResult:
    """Point estimate, paired draws, percentile interval, and exact p-value."""

    point: float
    values: NDArray[np.float64]
    lower: float
    upper: float
    p_value: Fraction
    iterations: int


def paired_bootstrap_p(
    differences: Sequence[Real] | NDArray[np.generic],
) -> Fraction:
    """Return min(1, 2 (1 + min(count <= 0, count >= 0)) / (B + 1)).

    Each finite floating-point value is compared with zero through its exact
    decimal Fraction(repr(value)); zeros contribute to both tail counts.
    """
    try:
        raw_values = list(differences)
    except TypeError as error:
        raise ValueError("differences must be a one-dimensional sequence") from error
    if not raw_values:
        raise ValueError("differences must not be empty")
    le = ge = 0
    for value in raw_values:
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("differences must contain finite real numbers")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("differences must contain finite real numbers")
        try:
            exact = value if isinstance(value, Fraction) else Fraction(repr(value))
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            raise ValueError("differences must contain finite real numbers") from error
        le += exact <= 0
        ge += exact >= 0
    return min(Fraction(1), Fraction(2 * (1 + min(le, ge)), len(raw_values) + 1))


def paired_bootstrap(
    statistic: Callable[..., float],
    arrays: Sequence[Sequence[Real] | NDArray[np.generic]],
    iterations: int,
    seed: int,
    level: float = 0.95,
    min_iterations: int = 1000,
) -> PairedBootstrapResult:
    """Resample patients with one shared index matrix for every input array.

    Evaluate statistic(*arrays) on the original patients and each paired draw.
    Return the linear percentile interval and S2 p-value of the draw values;
    the latter is intended for statistics that are differences.
    """
    if (
        isinstance(min_iterations, bool)
        or not isinstance(min_iterations, Integral)
        or min_iterations < 1
    ):
        raise ValueError("min_iterations must be an integer of at least 1")
    if (
        isinstance(iterations, bool)
        or not isinstance(iterations, Integral)
        or iterations < min_iterations
    ):
        raise ValueError("iterations must be an integer of at least min_iterations")
    if len(arrays) == 0:
        raise ValueError("arrays must not be empty")
    validated = []
    for array in arrays:
        values = np.asarray(array)
        if values.ndim != 1:
            raise ValueError("arrays must be one-dimensional")
        _finite_values(values)
        validated.append(values)
    n = len(validated[0])
    if any(len(array) != n for array in validated):
        raise ValueError("arrays must have equal lengths")
    # Validate level before evaluating a potentially expensive statistic.
    percentile_interval([0.0], level)
    indices = bootstrap_indices(n, iterations, seed)
    point = _finite_values([statistic(*validated)])[0]
    draws = np.empty(int(iterations), dtype=np.float64)
    for draw, row in enumerate(indices):
        draws[draw] = _finite_values([statistic(*(array[row] for array in validated))])[
            0
        ]
    lower, upper = percentile_interval(draws, level)
    return PairedBootstrapResult(
        point, draws, lower, upper, paired_bootstrap_p(draws), int(iterations)
    )

"""Resampling primitives defined by the Phase 09 statistics contract."""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray


def bootstrap_indices(n: int, iterations: int, seed: int) -> NDArray[np.int64]:
    """Return the seeded patient-index matrix for paired bootstrap draws."""
    if isinstance(n, bool) or not isinstance(n, Integral) or n < 1:
        raise ValueError("n must be an integer of at least 1")
    if (
        isinstance(iterations, bool)
        or not isinstance(iterations, Integral)
        or iterations < 1
    ):
        raise ValueError("iterations must be an integer of at least 1")
    return np.random.default_rng(seed).integers(
        0, int(n), size=(int(iterations), int(n)), dtype=np.int64
    )


def _finite_values(values: Sequence[Real] | NDArray[np.generic]) -> list[float]:
    """Convert a finite, one-dimensional sequence to Python floats."""
    try:
        raw_values = list(values)
    except TypeError as error:
        raise ValueError("values must be a one-dimensional sequence") from error
    if not raw_values:
        raise ValueError("values must not be empty")
    converted: list[float] = []
    for value in raw_values:
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError("values must be finite real numbers")
        converted_value = float(value)
        if not math.isfinite(converted_value):
            raise ValueError("values must be finite real numbers")
        converted.append(converted_value)
    return converted


def percentile_interval(
    values: Sequence[Real] | NDArray[np.generic], level: float = 0.95
) -> tuple[float, float]:
    """Return the two-sided linear percentile interval at the requested level."""
    if isinstance(level, np.generic):
        level = level.item()
    if isinstance(level, bool) or not isinstance(level, Real):
        raise ValueError("level must be a finite number in (0, 1)")
    exact_level = float(level)
    if not math.isfinite(exact_level) or not 0 < exact_level < 1:
        raise ValueError("level must be a finite number in (0, 1)")
    finite_values = _finite_values(values)
    exact_level = Fraction(repr(exact_level))
    low_percentile = float(50 * (1 - exact_level))
    high_percentile = float(50 * (1 + exact_level))
    low, high = np.percentile(
        finite_values,
        [low_percentile, high_percentile],
        method="linear",
    )
    return float(low), float(high)

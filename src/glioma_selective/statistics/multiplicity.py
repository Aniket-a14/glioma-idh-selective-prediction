"""Multiplicity adjustments defined by the Phase 09 statistics contract."""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from numbers import Real

import numpy as np


def _exact_probability(value: object, name: str) -> Fraction:
    """Convert a finite real probability to its exact decimal fraction."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite probability")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be a finite probability")
    try:
        exact = Fraction(repr(value))
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(f"{name} must be a finite probability") from error
    if exact < 0 or exact > 1:
        raise ValueError(f"{name} must be in [0, 1]")
    return exact


def benjamini_hochberg(
    p_values: Sequence[Real], q: float
) -> tuple[list[Fraction], list[bool]]:
    """Return exact BH-adjusted p-values and decisions in input order."""
    try:
        raw_values = list(p_values)
    except TypeError as error:
        raise ValueError("p_values must be a one-dimensional sequence") from error
    if not raw_values:
        raise ValueError("p_values must not be empty")
    exact_q = _exact_probability(q, "q")
    if exact_q <= 0 or exact_q >= 1:
        raise ValueError("q must be in (0, 1)")
    exact_values = [_exact_probability(value, "p_values") for value in raw_values]
    size = len(exact_values)
    ordered = sorted(enumerate(exact_values), key=lambda pair: pair[1])
    adjusted_sorted = [Fraction(0)] * size
    suffix_minimum = Fraction(1)
    for rank_index in range(size - 1, -1, -1):
        _, probability = ordered[rank_index]
        rank = rank_index + 1
        candidate = min(Fraction(1), probability * size / rank)
        suffix_minimum = min(suffix_minimum, candidate)
        adjusted_sorted[rank_index] = suffix_minimum
    adjusted = [Fraction(0)] * size
    for (original_index, _), value in zip(ordered, adjusted_sorted, strict=True):
        adjusted[original_index] = value
    reject = [value <= exact_q for value in adjusted]
    return adjusted, reject

"""Permutation tests for enrichment among rejected patients."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class EnrichmentResult:
    """Observed rejection enrichment and its one-sided Monte Carlo p-value."""

    observed: float | None
    p_value: float | None
    n_rejected: int


def _binary_values(
    values: Sequence[Real] | NDArray[np.generic], name: str
) -> list[int]:
    """Validate a non-empty one-dimensional sequence of finite binary numbers."""
    try:
        raw_values = list(values)
    except TypeError as error:
        raise ValueError(f"{name} must be a one-dimensional sequence") from error
    if not raw_values:
        raise ValueError("inputs must not be empty")
    binary: list[int] = []
    for value in raw_values:
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, bool):
            binary.append(int(value))
            continue
        if not isinstance(value, Real):
            raise ValueError(f"{name} values must be 0 or 1")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{name} values must be finite")
        try:
            exact = Fraction(repr(value))
        except (ValueError, ZeroDivisionError, OverflowError) as error:
            raise ValueError(f"{name} values must be finite 0 or 1") from error
        if exact not in (0, 1):
            raise ValueError(f"{name} values must be 0 or 1")
        binary.append(int(exact))
    return binary


def _validated_binary_pairs(
    rejected: Sequence[Real] | NDArray[np.generic],
    errors: Sequence[Real] | NDArray[np.generic],
) -> tuple[list[int], list[int]]:
    rejected_values = _binary_values(rejected, "rejected")
    error_values = _binary_values(errors, "errors")
    if len(rejected_values) != len(error_values):
        raise ValueError("rejected and errors must have equal lengths")
    return rejected_values, error_values


def enrichment_permutation_test(
    rejected: Sequence[Real] | NDArray[np.generic],
    errors: Sequence[Real] | NDArray[np.generic],
    permutations: int,
    seed: int,
) -> EnrichmentResult:
    """Estimate rejection enrichment and its one-sided permutation p-value."""
    rejected_values, error_values = _validated_binary_pairs(rejected, errors)
    if (
        isinstance(permutations, bool)
        or not isinstance(permutations, Integral)
        or permutations < 1
    ):
        raise ValueError("permutations must be an integer of at least 1")
    n = len(rejected_values)
    m = sum(rejected_values)
    if m == 0:
        return EnrichmentResult(observed=None, p_value=None, n_rejected=0)

    total_errors = sum(error_values)
    observed_count = sum(
        error
        for reject, error in zip(rejected_values, error_values, strict=True)
        if reject
    )
    observed = observed_count / m - total_errors / n
    rng = np.random.default_rng(seed)
    exceedances = 0
    for _ in range(int(permutations)):
        subset = rng.permutation(n)[:m]
        permuted_count = sum(error_values[int(index)] for index in subset)
        if permuted_count >= observed_count:
            exceedances += 1
    p_value = (1 + exceedances) / (int(permutations) + 1)
    return EnrichmentResult(observed, p_value, m)


def enrichment_exact_p(
    rejected: Sequence[Real] | NDArray[np.generic],
    errors: Sequence[Real] | NDArray[np.generic],
) -> Fraction | None:
    """Return the exact hypergeometric upper-tail p-value for enrichment."""
    rejected_values, error_values = _validated_binary_pairs(rejected, errors)
    n = len(rejected_values)
    m = sum(rejected_values)
    if m == 0:
        return None

    total_errors = sum(error_values)
    observed_count = sum(
        error
        for reject, error in zip(rejected_values, error_values, strict=True)
        if reject
    )
    denominator = math.comb(n, m)
    maximum = min(m, total_errors)
    minimum = max(0, m - (n - total_errors))
    tail = sum(
        math.comb(total_errors, count) * math.comb(n - total_errors, m - count)
        for count in range(max(observed_count, minimum), maximum + 1)
    )
    return Fraction(tail, denominator)

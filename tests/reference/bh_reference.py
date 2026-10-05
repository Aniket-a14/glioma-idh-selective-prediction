"""Independent standard-library reference for Benjamini-Hochberg correction."""

from __future__ import annotations

import math
from fractions import Fraction


def _as_fraction(
    value: object, *, name: str, lower: Fraction, upper: Fraction
) -> Fraction:
    try:
        numeric = float(value)
        exact = Fraction(str(value))
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"{name} must be numeric") from error
    if not math.isfinite(numeric) or not lower <= exact <= upper:
        raise ValueError(f"{name} is outside its permitted range")
    return exact


def _validated_p_values(p_values: list[float]) -> list[Fraction]:
    values = list(p_values)
    if not values:
        raise ValueError("p_values must not be empty")
    return [
        _as_fraction(value, name="p-value", lower=Fraction(0), upper=Fraction(1))
        for value in values
    ]


def _validated_q(q: float) -> Fraction:
    exact = _as_fraction(q, name="q", lower=Fraction(0), upper=Fraction(1))
    if exact <= 0:
        raise ValueError("q must be in (0, 1]")
    return exact


def _ranked(values: list[Fraction]) -> list[tuple[int, Fraction]]:
    # Python's stable sort preserves input order for equal p-values.
    return sorted(enumerate(values), key=lambda item: item[1])


def _to_input_order(
    ranked: list[tuple[int, Fraction]], ranked_values: list[Fraction]
) -> list[float]:
    output = [Fraction(0) for _ in ranked]
    for position, (original_index, _) in enumerate(ranked):
        output[original_index] = ranked_values[position]
    return [float(value) for value in output]


def bh_adjusted(p_values: list[float]) -> list[float]:
    """Return BH adjusted p-values in the original input order."""

    values = _validated_p_values(p_values)
    ranked = _ranked(values)
    count = len(ranked)
    adjusted = [Fraction(0) for _ in ranked]
    running_min = Fraction(1)
    for position in range(count - 1, -1, -1):
        rank = position + 1
        raw = ranked[position][1] * count / rank
        running_min = min(running_min, raw, Fraction(1))
        adjusted[position] = running_min
    return _to_input_order(ranked, adjusted)


def bh_reject(p_values: list[float], q: float) -> list[bool]:
    """Return the BH step-up rejection decision in input order."""

    values = _validated_p_values(p_values)
    exact_q = _validated_q(q)
    ranked = _ranked(values)
    count = len(ranked)
    largest_rank = 0
    for position, (_, p_value) in enumerate(ranked, start=1):
        if p_value * count <= position * exact_q:
            largest_rank = position

    ranks = [0 for _ in values]
    for position, (original_index, _) in enumerate(ranked, start=1):
        ranks[original_index] = position
    return [rank != 0 and rank <= largest_rank for rank in ranks]


def holm_adjusted(p_values: list[float]) -> list[float]:
    """Return Holm adjusted p-values in input order for catalogue checks."""

    values = _validated_p_values(p_values)
    ranked = _ranked(values)
    count = len(ranked)
    adjusted = [Fraction(0) for _ in ranked]
    running_max = Fraction(0)
    for position, (_, p_value) in enumerate(ranked):
        rank = position + 1
        raw = (count - rank + 1) * p_value
        running_max = max(running_max, raw)
        adjusted[position] = min(running_max, Fraction(1))
    return _to_input_order(ranked, adjusted)

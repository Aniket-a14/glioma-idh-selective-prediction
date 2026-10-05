"""Exact tie-block implementations of Phase 09 selective-prediction AURC."""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from numbers import Real

import numpy as np
from numpy.typing import NDArray

type NumericInput = Sequence[float] | NDArray[np.generic]
type _Block = tuple[int, Fraction, Fraction]

__all__ = ["aurc_mean_over_cutoffs", "aurc_trapezoid", "oracle_aurc"]


def _exact_number(value: object, name: str) -> Fraction:
    """Convert one real numeric value using its decimal representation."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} values must be real numbers")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} values must be finite")
    try:
        return Fraction(repr(value))
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError(f"{name} values must be finite real numbers") from error


def _exact_values(values: NumericInput, name: str) -> list[Fraction]:
    try:
        raw_values = list(values)
    except TypeError as error:
        raise ValueError(f"{name} must be a one-dimensional sequence") from error
    if not raw_values:
        raise ValueError("inputs must not be empty")
    return [_exact_number(value, name) for value in raw_values]


def _validated_pairs(
    scores: NumericInput, losses: NumericInput
) -> tuple[list[Fraction], list[Fraction]]:
    exact_scores = _exact_values(scores, "scores")
    exact_losses = _exact_values(losses, "losses")
    if len(exact_scores) != len(exact_losses):
        raise ValueError("scores and losses must have equal lengths")
    if any(loss < 0 for loss in exact_losses):
        raise ValueError("losses must be non-negative")
    return exact_scores, exact_losses


def _blocks(scores: list[Fraction], losses: list[Fraction]) -> list[_Block]:
    """Return (cumulative count, cumulative loss, block-end risk) summaries."""
    ordered = sorted(
        zip(scores, losses, strict=True), key=lambda pair: pair[0], reverse=True
    )
    blocks: list[_Block] = []
    count = 0
    cumulative_loss = Fraction(0)
    index = 0
    while index < len(ordered):
        score = ordered[index][0]
        block_loss = Fraction(0)
        block_size = 0
        while index < len(ordered) and ordered[index][0] == score:
            block_loss += ordered[index][1]
            block_size += 1
            index += 1
        count += block_size
        cumulative_loss += block_loss
        blocks.append((count, cumulative_loss, cumulative_loss / count))
    return blocks


def aurc_mean_over_cutoffs(scores: NumericInput, losses: NumericInput) -> float:
    """Return mean selective risk over all n cutoffs, assigning ties block-end risk."""
    exact_scores, exact_losses = _validated_pairs(scores, losses)
    blocks = _blocks(exact_scores, exact_losses)
    return _mean_block_end_risks(blocks, len(exact_scores))


def _mean_block_end_risks(blocks: list[_Block], n: int) -> float:
    """Average each block-end risk across the cutoffs in that block."""
    previous_count = 0
    total = Fraction(0)
    for count, _, risk in blocks:
        total += (count - previous_count) * risk
        previous_count = count
    return float(total / n)


def aurc_trapezoid(
    scores: NumericInput, losses: NumericInput, start_at_zero: bool = False
) -> float:
    """Return trapezoid area over tie-block points, optionally starting at 0."""
    exact_scores, exact_losses = _validated_pairs(scores, losses)
    blocks = _blocks(exact_scores, exact_losses)
    n = len(exact_scores)
    previous_coverage = Fraction(0) if start_at_zero else Fraction(blocks[0][0], n)
    previous_risk = blocks[0][2]
    area = Fraction(0)
    for count, _, risk in blocks:
        coverage = Fraction(count, n)
        if coverage == previous_coverage:
            continue
        area += (coverage - previous_coverage) * (previous_risk + risk) / 2
        previous_coverage = coverage
        previous_risk = risk
    return float(area)


def oracle_aurc(losses: NumericInput) -> float:
    """Return AURC for the optimal ordering that accepts smallest losses first."""
    exact_losses = _exact_values(losses, "losses")
    if any(loss < 0 for loss in exact_losses):
        raise ValueError("losses must be non-negative")
    ordered_losses = sorted(exact_losses)
    size = len(ordered_losses)
    oracle_scores = [Fraction(size - index) for index in range(size)]
    return _mean_block_end_risks(
        _blocks(oracle_scores, ordered_losses), len(ordered_losses)
    )

"""Selective-risk summaries that do not depend on prediction artifacts."""

from __future__ import annotations

from fractions import Fraction

from glioma_selective.selective.aurc import (
    NumericInput,
    _blocks,
    _exact_number,
    _exact_values,
    _validated_pairs,
)

__all__ = ["selective_risk_at_coverage", "rejected_but_correct_rate"]


def _target_fraction(target_coverage: float) -> Fraction:
    target = _exact_number(target_coverage, "target_coverage")
    if target <= 0 or target > 1:
        raise ValueError("target_coverage must be in (0, 1]")
    return target


def selective_risk_at_coverage(
    scores: NumericInput, losses: NumericInput, target_coverage: float
) -> tuple[float, float]:
    """Return (attained coverage, risk) at the first block end meeting target."""
    exact_target = _target_fraction(target_coverage)
    exact_scores, exact_losses = _validated_pairs(scores, losses)
    n = len(exact_scores)
    for count, _, risk in _blocks(exact_scores, exact_losses):
        coverage = Fraction(count, n)
        if coverage >= exact_target:
            return float(coverage), float(risk)
    raise RuntimeError("validated coverage target was not reached")


def rejected_but_correct_rate(
    scores: NumericInput,
    correct: NumericInput,
    target_coverage: float,
) -> tuple[float | None, int]:
    """Return correct fraction and count among cases rejected at target coverage."""
    exact_target = _target_fraction(target_coverage)
    exact_scores = _exact_values(scores, "scores")
    exact_correct = _exact_values(correct, "correct")
    if len(exact_scores) != len(exact_correct):
        raise ValueError("scores and correct must have equal lengths")
    if any(value not in (0, 1) for value in exact_correct):
        raise ValueError("correct values must be 0 or 1")

    n = len(exact_scores)
    accepted_count = n
    accepted_correct = Fraction(0)
    for count, cumulative_correct, _ in _blocks(exact_scores, exact_correct):
        if Fraction(count, n) >= exact_target:
            accepted_count = count
            accepted_correct = cumulative_correct
            break
    rejected_count = n - accepted_count
    if rejected_count == 0:
        return None, 0
    total_correct = sum(exact_correct, Fraction(0))
    rejected_correct = total_correct - accepted_correct
    return float(rejected_correct / rejected_count), rejected_count

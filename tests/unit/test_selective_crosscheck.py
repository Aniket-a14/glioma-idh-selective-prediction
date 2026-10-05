"""T09.8: Codex's AURC and selective-risk code against Claude's risk-coverage points.

``selective/aurc.py`` and ``evaluation/selective_metrics.py`` were written from
the contract alone; ``selective/risk_coverage.py`` was written separately. They
share no code, so agreement on random tied inputs is a real check.
"""

from __future__ import annotations

import random
from fractions import Fraction

import pytest

from glioma_selective.evaluation.selective_metrics import (
    rejected_but_correct_rate,
    selective_risk_at_coverage,
)
from glioma_selective.selective.aurc import (
    aurc_mean_over_cutoffs,
    aurc_trapezoid,
    oracle_aurc,
)
from glioma_selective.selective.risk_coverage import rc_points


def _cases(seed: int, count: int) -> list[tuple[list[float], list[int]]]:
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        n = rng.choice((1, 2, 3, 7, 20, 64, 150))
        grain = rng.choice((1, 2, 10, 100))  # coarse grain gives many ties
        scores = [round(rng.random(), len(str(grain)) - 1) for _ in range(n)]
        losses = [rng.randint(0, 1) for _ in range(n)]
        cases.append((scores, losses))
    return cases


def _aurc_from_points(points: list[tuple[float, float]], n: int) -> float:
    total = Fraction(0)
    previous = 0
    for coverage, risk in points:
        count = round(coverage * n)
        total += (count - previous) * Fraction(repr(risk))
        previous = count
    return float(total / n)


def _trapezoid_from_points(points: list[tuple[float, float]], zero: bool) -> float:
    pts = [(Fraction(repr(c)), Fraction(repr(r))) for c, r in points]
    if zero:
        pts = [(Fraction(0), pts[0][1]), *pts]
    area = sum(
        (b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(pts, pts[1:], strict=False)
    )
    return float(area)


@pytest.mark.parametrize("seed", [21, 22, 23])
def test_aurc_agrees_with_risk_coverage_points(seed: int) -> None:
    for scores, losses in _cases(seed, 150):
        points = rc_points(scores, losses)
        n = len(scores)
        assert aurc_mean_over_cutoffs(scores, losses) == pytest.approx(
            _aurc_from_points(points, n), abs=1e-12
        )
        assert aurc_trapezoid(scores, losses) == pytest.approx(
            _trapezoid_from_points(points, False), abs=1e-12
        )
        assert aurc_trapezoid(scores, losses, start_at_zero=True) == pytest.approx(
            _trapezoid_from_points(points, True), abs=1e-12
        )
        assert aurc_mean_over_cutoffs(scores, losses) >= oracle_aurc(losses) - 1e-12


@pytest.mark.parametrize("seed", [31, 32])
def test_selective_risk_is_a_point_of_the_curve(seed: int) -> None:
    for scores, losses in _cases(seed, 150):
        points = rc_points(scores, losses)
        for target in (0.1, 0.5, 0.6, 0.9, 1.0):
            coverage, risk = selective_risk_at_coverage(scores, losses, target)
            assert (coverage, risk) in points
            assert coverage >= target
            earlier = [c for c, _ in points if c < coverage]
            assert all(c < target for c in earlier)


def test_rejected_but_correct_matches_the_accepted_prefix() -> None:
    for scores, losses in _cases(41, 150):
        correct = [1 - loss for loss in losses]
        n = len(scores)
        coverage, _ = selective_risk_at_coverage(scores, losses, 0.6)
        rate, rejected = rejected_but_correct_rate(scores, correct, 0.6)
        assert rejected == n - round(coverage * n)
        if rejected == 0:
            assert rate is None
        else:
            assert rate is not None and 0.0 <= rate <= 1.0

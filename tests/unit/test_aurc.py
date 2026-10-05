"""Contract and independent brute-force checks for Phase 09 AURC."""

from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from glioma_selective.selective.aurc import (
    aurc_mean_over_cutoffs,
    aurc_trapezoid,
    oracle_aurc,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "phase09_selective.json"


def _cases() -> list[dict[str, Any]]:
    return json.loads(FIXTURE.read_text())["cases"]


def _fraction(value: str) -> float:
    return float(Fraction(value))


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["name"])
def test_fixture_aurc_fields(case: dict[str, Any]) -> None:
    scores = case["scores"]
    losses = case["losses"]
    assert aurc_mean_over_cutoffs(scores, losses) == pytest.approx(
        _fraction(case["aurc_mean_block"]), abs=1e-15
    )
    assert aurc_trapezoid(scores, losses) == pytest.approx(
        _fraction(case["aurc_trapezoid"]), abs=1e-15
    )
    assert aurc_trapezoid(scores, losses, start_at_zero=True) == pytest.approx(
        _fraction(case["aurc_trapezoid_from_zero"]), abs=1e-15
    )
    assert oracle_aurc(losses) == pytest.approx(
        _fraction(case["oracle_aurc"]), abs=1e-15
    )


def test_accepts_numpy_arrays_without_mutating_them() -> None:
    scores = np.array([0.9, 0.9, 0.5], dtype=np.float64)
    losses = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    original_scores = scores.copy()
    original_losses = losses.copy()
    assert aurc_mean_over_cutoffs(scores, losses) == pytest.approx(4 / 9)
    assert aurc_trapezoid(scores, losses) == pytest.approx(5 / 36)
    assert np.array_equal(scores, original_scores)
    assert np.array_equal(losses, original_losses)


def _brute_aurc(scores: list[float], losses: list[float]) -> Fraction:
    exact_scores = [Fraction(repr(value)) for value in scores]
    exact_losses = [Fraction(repr(value)) for value in losses]
    total = Fraction(0)
    for cutoff in range(1, len(scores) + 1):
        cutoff_score = sorted(exact_scores, reverse=True)[cutoff - 1]
        included = [
            loss
            for score, loss in zip(exact_scores, exact_losses, strict=True)
            if score >= cutoff_score
        ]
        total += sum(included, Fraction(0)) / len(included)
    return total / len(scores)


def _brute_selective_risk(
    scores: list[float], losses: list[float], target: float
) -> tuple[Fraction, Fraction]:
    exact_scores = [Fraction(repr(value)) for value in scores]
    exact_losses = [Fraction(repr(value)) for value in losses]
    exact_target = Fraction(repr(target))
    for score in sorted(set(exact_scores), reverse=True):
        included = [
            loss
            for observed_score, loss in zip(exact_scores, exact_losses, strict=True)
            if observed_score >= score
        ]
        coverage = Fraction(len(included), len(scores))
        if coverage >= exact_target:
            return coverage, sum(included, Fraction(0)) / len(included)
    raise AssertionError("positive target did not select any patients")


def test_randomized_brute_force_cross_check() -> None:
    from glioma_selective.evaluation.selective_metrics import (
        selective_risk_at_coverage,
    )

    rng = random.Random(90210)
    score_pool = [0.0, 0.2, 0.2, 0.5, 0.8, 0.8, 1.0]
    targets = [0.1, 0.25, 0.5, 0.7, 0.9, 1.0]
    for _ in range(300):
        size = rng.randint(1, 14)
        scores = [rng.choice(score_pool) for _ in range(size)]
        losses = [float(rng.randint(0, 3)) for _ in range(size)]
        target = rng.choice(targets)
        expected_aurc = float(_brute_aurc(scores, losses))
        expected_coverage, expected_risk = _brute_selective_risk(scores, losses, target)
        actual_coverage, actual_risk = selective_risk_at_coverage(
            scores, losses, target
        )
        assert aurc_mean_over_cutoffs(scores, losses) == pytest.approx(
            expected_aurc, abs=1e-12
        )
        assert actual_coverage == pytest.approx(float(expected_coverage), abs=1e-12)
        assert actual_risk == pytest.approx(float(expected_risk), abs=1e-12)


def test_randomized_properties_with_ties_and_permutations() -> None:
    rng = random.Random(51009)
    for _ in range(35):
        size = rng.randint(1, 24)
        scores = [float(rng.randrange(4)) for _ in range(size)]
        losses = [float(rng.randrange(2)) for _ in range(size)]
        expected = aurc_mean_over_cutoffs(scores, losses)
        assert expected >= oracle_aurc(losses) - 1e-15
        for _ in range(50):
            order = list(range(size))
            rng.shuffle(order)
            assert aurc_mean_over_cutoffs(
                [scores[i] for i in order], [losses[i] for i in order]
            ) == pytest.approx(expected, abs=1e-15)


def test_boundary_and_perfect_ranking_properties() -> None:
    assert aurc_mean_over_cutoffs([0.5, 0.5, 0.1], [0, 0, 0]) == 0
    assert aurc_mean_over_cutoffs([0.5, 0.5, 0.1], [1, 1, 1]) == 1
    losses = [0, 0, 0, 1, 1, 1]
    scores = [0.95, 0.85, 0.65, 0.55, 0.35, 0.25]
    assert aurc_mean_over_cutoffs(scores, losses) == pytest.approx(
        oracle_aurc(losses), abs=1e-15
    )


def test_aurc_rejects_invalid_inputs() -> None:
    invalid_cases = [
        ([], []),
        ([0.2], []),
        ([float("nan")], [0]),
        ([float("inf")], [0]),
        ([0.2], [-1]),
        ([0.2], [float("nan")]),
        ([0.2], [float("-inf")]),
    ]
    for scores, losses in invalid_cases:
        with pytest.raises(ValueError):
            aurc_mean_over_cutoffs(scores, losses)
        with pytest.raises(ValueError):
            aurc_trapezoid(scores, losses)
    for losses in ([], [-1], [float("nan")], [float("inf")]):
        with pytest.raises(ValueError):
            oracle_aurc(losses)


def test_wrong_aurc_variants_disagree_with_a_fixture() -> None:
    cases = _cases()
    distinct = cases[0]
    tied = next(case for case in cases if case["name"] == "tie_block_top_10_0")

    ascending_losses = list(reversed(distinct["losses"]))
    ascending = sum(
        sum(ascending_losses[:cutoff]) / cutoff
        for cutoff in range(1, len(ascending_losses) + 1)
    ) / len(ascending_losses)
    assert abs(ascending - _fraction(distinct["aurc_mean_block"])) > 1e-15

    ordered_tie_risks = [1.0, 0.5, 1 / 3]
    input_order_tie = sum(ordered_tie_risks) / len(ordered_tie_risks)
    assert input_order_tie != _fraction(tied["aurc_mean_block"])

    n_minus_one = sum([0.0, 0.0, 1 / 3, 1 / 4]) / (len(distinct["losses"]) - 1)
    assert n_minus_one != _fraction(distinct["aurc_mean_block"])

"""Contract and property checks for target coverage and rejected cases."""

from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from glioma_selective.evaluation.selective_metrics import (
    rejected_but_correct_rate,
    selective_risk_at_coverage,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "phase09_selective.json"


def _cases() -> list[dict[str, Any]]:
    return json.loads(FIXTURE.read_text())["cases"]


def _fraction(value: str) -> float:
    return float(Fraction(value))


@pytest.mark.parametrize("case", _cases(), ids=lambda case: case["name"])
def test_fixture_selective_metric_fields(case: dict[str, Any]) -> None:
    target_coverage, target_risk = selective_risk_at_coverage(
        case["scores"], case["losses"], case["target_coverage"]
    )
    expected_target = case["selective_risk_at_target"]
    assert target_coverage == pytest.approx(_fraction(expected_target[0]), abs=1e-15)
    assert target_risk == pytest.approx(_fraction(expected_target[1]), abs=1e-15)

    full_coverage, full_risk = selective_risk_at_coverage(
        case["scores"], case["losses"], 1.0
    )
    expected_full = case["selective_risk_at_1"]
    assert full_coverage == pytest.approx(_fraction(expected_full[0]), abs=1e-15)
    assert full_risk == pytest.approx(_fraction(expected_full[1]), abs=1e-15)

    correct_rate, rejected_count = rejected_but_correct_rate(
        case["scores"], case["correct"], case["target_coverage"]
    )
    expected_rate, expected_count = case["rejected_but_correct"]
    if expected_rate is None:
        assert correct_rate is None
    else:
        assert correct_rate == pytest.approx(_fraction(expected_rate), abs=1e-15)
    assert rejected_count == expected_count


def test_last_point_is_full_mean_loss() -> None:
    for case in _cases():
        _, risk = selective_risk_at_coverage(case["scores"], case["losses"], 1.0)
        expected = sum(Fraction(repr(loss)) for loss in case["losses"]) / len(
            case["losses"]
        )
        assert risk == pytest.approx(float(expected), abs=1e-15)


def test_randomized_coverage_and_rejection_properties() -> None:
    rng = random.Random(29074)
    for _ in range(300):
        size = rng.randint(1, 20)
        scores = [float(rng.randrange(5)) for _ in range(size)]
        losses = [float(rng.randrange(2)) for _ in range(size)]
        correct = [rng.randrange(2) for _ in range(size)]
        target = rng.choice([0.1, 0.25, 0.5, 0.75, 0.9, 1.0])
        attained, risk = selective_risk_at_coverage(scores, losses, target)
        assert attained >= target
        assert (attained * size).is_integer()
        block_counts = {
            sum(score >= threshold for score in scores) for threshold in set(scores)
        }
        accepted_count = round(attained * size)
        assert accepted_count in block_counts
        selected_threshold = next(
            threshold
            for threshold in sorted(set(scores), reverse=True)
            if sum(score >= threshold for score in scores) == accepted_count
        )
        expected_losses = [
            Fraction(repr(loss))
            for score, loss in zip(scores, losses, strict=True)
            if score >= selected_threshold
        ]
        assert risk == pytest.approx(
            float(sum(expected_losses, Fraction(0)) / len(expected_losses)),
            abs=1e-15,
        )

        rate, rejected = rejected_but_correct_rate(scores, correct, target)
        assert rejected == size - accepted_count
        assert (rate is None) == (rejected == 0)
        if rejected:
            rejected_correct = sum(
                value
                for score, value in zip(scores, correct, strict=True)
                if score < selected_threshold
            )
            assert rate == pytest.approx(rejected_correct / rejected, abs=1e-15)


def test_wrong_selective_risk_variants_disagree_with_fixtures() -> None:
    cases = _cases()
    exact_target = cases[0]
    between = next(case for case in cases if case["name"] == "target_between_points")

    strict_coverage = selective_risk_at_coverage(
        exact_target["scores"], exact_target["losses"], 0.5
    )
    wrong_strict = (0.75, 1 / 3)
    assert strict_coverage != wrong_strict

    rejected = exact_target["losses"][2:]
    rejected_set_risk = sum(rejected) / len(rejected)
    assert rejected_set_risk != _fraction(exact_target["selective_risk_at_target"][1])

    first_below_target_risk = _fraction(between["points"][0][1])
    assert first_below_target_risk != _fraction(between["selective_risk_at_target"][1])


def test_selective_functions_reject_invalid_inputs() -> None:
    invalid_data = [
        ([], []),
        ([0.5], []),
        ([float("nan")], [0]),
        ([float("inf")], [0]),
        ([0.5], [-1]),
        ([0.5], [float("nan")]),
        ([0.5], [float("inf")]),
    ]
    for scores, losses in invalid_data:
        with pytest.raises(ValueError):
            selective_risk_at_coverage(scores, losses, 0.5)
    for target in (0.0, -0.1, 1.1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            selective_risk_at_coverage([0.5], [0], target)

    invalid_correct = [
        ([], []),
        ([0.5], []),
        ([float("nan")], [0]),
        ([float("inf")], [0]),
        ([0.5], [-1]),
        ([0.5], [2]),
    ]
    for scores, correct in invalid_correct:
        with pytest.raises(ValueError):
            rejected_but_correct_rate(scores, correct, 0.5)
    for target in (0.0, -0.1, 1.1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            rejected_but_correct_rate([0.5], [1], target)

"""Tests for positive-class Brier score, ECE, and reliability bins."""

from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path

import pytest
from tests.reference import calibration_reference

from glioma_selective.evaluation.calibration_metrics import (
    _bin_index,
    brier_score,
    expected_calibration_error,
    reliability_bins,
)

FIXTURES = json.loads(
    Path(__file__)
    .parents[1]
    .joinpath("fixtures", "phase07_contracts.json")
    .read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", FIXTURES["brier"], ids=lambda case: case["name"])
def test_brier_hand_calculated_fixtures(case: dict[str, object]) -> None:
    assert brier_score(case["p_hat"], case["labels"]) == pytest.approx(case["expected"])


@pytest.mark.parametrize("case", FIXTURES["ece"], ids=lambda case: case["name"])
def test_ece_and_reliability_bin_fixtures(case: dict[str, object]) -> None:
    probabilities = case["p_hat"]
    labels = case["labels"]
    assert expected_calibration_error(probabilities, labels) == pytest.approx(
        case["expected"], abs=1e-15
    )
    bins = reliability_bins(probabilities, labels)
    for index, expected in case["bins"].items():
        entry = bins[int(index)]
        assert entry["count"] == expected[0]
        assert entry["mean_p"] == pytest.approx(expected[1], abs=1e-15)
        assert entry["frac_pos"] == pytest.approx(expected[2], abs=1e-15)
    for index, entry in enumerate(bins):
        if str(index) not in case["bins"]:
            assert entry == {"count": 0, "mean_p": None, "frac_pos": None}


def _exact_index(probability: float, n_bins: int) -> int:
    scaled = Fraction(repr(float(probability))) * n_bins
    return min(scaled.numerator // scaled.denominator, n_bins - 1)


def test_bin_assignment_matches_exact_arithmetic_on_grid_and_random_floats() -> None:
    rng = random.Random(702)
    probabilities = [index / 1000 for index in range(1001)]
    probabilities.extend(rng.random() for _ in range(1000))
    assert [_bin_index(probability, 10) for probability in probabilities] == [
        _exact_index(probability, 10) for probability in probabilities
    ]
    labels = [0] * len(probabilities)
    bins = reliability_bins(probabilities, labels)
    observed = [
        index for index, entry in enumerate(bins) for _ in range(entry["count"])
    ]
    exact = sorted(_exact_index(probability, 10) for probability in probabilities)
    assert sorted(observed) == exact
    assert bins[9]["count"] >= 1
    assert _exact_index(1.0, 10) == 9


def test_metrics_match_independent_reference_on_200_random_cases() -> None:
    rng = random.Random(1707)
    for _ in range(200):
        size = rng.randint(1, 100)
        probabilities = [rng.random() for _ in range(size)]
        labels = [rng.randrange(2) for _ in range(size)]
        assert brier_score(probabilities, labels) == pytest.approx(
            calibration_reference.brier_score(probabilities, labels), abs=1e-12
        )
        assert expected_calibration_error(probabilities, labels) == pytest.approx(
            calibration_reference.ece(probabilities, labels, 10), abs=1e-12
        )


@pytest.mark.parametrize(
    ("probabilities", "labels"),
    [
        ([], []),
        ([0.1], []),
        ([float("nan")], [0]),
        ([-0.1], [0]),
        ([1.1], [1]),
        ([[0.2]], [0]),
        ([0.1], [2]),
    ],
)
def test_calibration_metrics_reject_invalid_inputs(
    probabilities: object, labels: object
) -> None:
    with pytest.raises(ValueError):
        brier_score(probabilities, labels)  # type: ignore[arg-type]


@pytest.mark.parametrize("n_bins", [0, -1, True, 1.5])
def test_calibration_metrics_reject_invalid_bin_count(n_bins: object) -> None:
    with pytest.raises(ValueError):
        reliability_bins([0.2], [0], n_bins)  # type: ignore[arg-type]


def test_reliability_reports_empty_bins_as_none_and_one_in_last_bin() -> None:
    bins = reliability_bins([1.0], [1], n_bins=4)
    assert bins == [
        {"count": 0, "mean_p": None, "frac_pos": None},
        {"count": 0, "mean_p": None, "frac_pos": None},
        {"count": 0, "mean_p": None, "frac_pos": None},
        {"count": 1, "mean_p": 1.0, "frac_pos": 1.0},
    ]

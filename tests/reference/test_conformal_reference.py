"""Independent checks for the standard-library conformal reference."""

from __future__ import annotations

import json
import math
import random
from fractions import Fraction
from pathlib import Path

import conformal_reference
import pytest

FIXTURES = json.loads(
    Path(__file__)
    .parents[1]
    .joinpath("fixtures", "phase07_contracts.json")
    .read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    "case", FIXTURES["conformal_quantile"], ids=lambda case: case["name"]
)
def test_conformal_quantile_fixtures(case: dict[str, object]) -> None:
    result = conformal_reference.conformal_quantile(case["scores"], case["alpha"])
    expected = case["expected"]
    if expected == "inf":
        assert result == math.inf
    else:
        assert result == expected


@pytest.mark.parametrize(
    "case", FIXTURES["quantile_errors"], ids=lambda case: case["name"]
)
def test_conformal_quantile_rejects_fixture_errors(case: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        conformal_reference.conformal_quantile(case["scores"], case["alpha"])


@pytest.mark.parametrize("case", FIXTURES["nonconformity_score"])
def test_nonconformity_score_fixtures(case: dict[str, object]) -> None:
    result = conformal_reference.nonconformity_score(case["p_hat"], case["label"])
    assert result == pytest.approx(case["expected"], abs=1e-15)


def test_end_to_end_conformal_fixture_including_decimal_comparison_trap() -> None:
    case = FIXTURES["conformal_end_to_end"]
    scores = [
        conformal_reference.nonconformity_score(probability, label)
        for probability, label in zip(
            case["cal_p_hat"], case["cal_labels"], strict=True
        )
    ]
    assert sorted(scores) == case["cal_scores_sorted"]
    for entry in case["cases"]:
        quantile = conformal_reference.conformal_quantile(scores, entry["alpha"])
        expected_q = math.inf if entry["q"] == "inf" else entry["q"]
        assert quantile == expected_q
        actual_sets = [
            conformal_reference.prediction_set(probability, quantile)
            for probability in case["test_p_hat"]
        ]
        assert [list(prediction) for prediction in actual_sets] == entry["sets"]
        summary = conformal_reference.conformal_summary(
            actual_sets, case["test_labels"]
        )
        for key in ("coverage", "abstention_rate", "empty_rate", "full_rate"):
            assert summary[key] == pytest.approx(entry[key], abs=1e-15)
        if entry["alpha"] == 0.2:
            assert actual_sets[1] == (1,)


def test_both_labels_in_set_fixture() -> None:
    case = FIXTURES["conformal_both_labels_in_set"]
    actual_sets = [
        conformal_reference.prediction_set(probability, case["q"])
        for probability in case["test_p_hat"]
    ]
    assert [list(prediction) for prediction in actual_sets] == case["sets"]
    summary = conformal_reference.conformal_summary(actual_sets, case["test_labels"])
    for key in ("coverage", "abstention_rate", "empty_rate", "full_rate"):
        assert summary[key] == pytest.approx(case[key], abs=1e-15)


def test_quantile_finite_sample_coverage_property_and_brute_force_order_statistic() -> (
    None
):
    rng = random.Random(707)
    alpha_grid = (0.05, 0.1, 0.2)
    for _ in range(200):
        scores = [round(rng.random(), 5) for _ in range(rng.randint(1, 80))]
        for alpha in alpha_grid:
            quantile = conformal_reference.conformal_quantile(scores, alpha)
            exact_alpha = Fraction(repr(alpha))
            rank_fraction = (len(scores) + 1) * (1 - exact_alpha)
            rank = (
                rank_fraction.numerator + rank_fraction.denominator - 1
            ) // rank_fraction.denominator
            if rank > len(scores):
                assert math.isinf(quantile)
                continue
            assert quantile == sorted(scores)[rank - 1]
            at_or_below = sum(score <= quantile for score in scores) / len(scores)
            assert at_or_below >= 1.0 - alpha


def test_exact_decimal_membership_for_p_point_seven() -> None:
    assert 1.0 - 0.7 > 0.3
    assert conformal_reference.prediction_set(0.7, 0.3) == (1,)

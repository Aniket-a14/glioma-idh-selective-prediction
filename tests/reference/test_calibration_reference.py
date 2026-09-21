"""Independent tests for the C-017 calibration reference implementation."""

from __future__ import annotations

import json
import math
import random
from fractions import Fraction
from pathlib import Path

import calibration_reference
import pytest

FIXTURES = json.loads(
    Path(__file__)
    .with_name("fixtures")
    .joinpath("calibration_cases.json")
    .read_text(encoding="utf-8")
)
BY_NAME = {case["name"]: case for case in FIXTURES}


def _fixture(name: str) -> dict[str, object]:
    return BY_NAME[name]


def test_brier_hand_worked_fixture_and_independent_fraction_route() -> None:
    case = _fixture("brier_four_points")
    probs = case["probs"]
    labels = case["labels"]
    expected = sum(
        (Fraction(str(probability)) - label) ** 2
        for probability, label in zip(probs, labels, strict=False)
    ) / len(probs)
    assert expected == Fraction(9, 200)
    assert calibration_reference.brier_score(probs, labels) == pytest.approx(
        float(expected)
    )
    assert calibration_reference.brier_score(probs, labels) == pytest.approx(
        case["expected"]
    )


@pytest.mark.parametrize(
    "name", ["ece_positive_class_eight_points", "ece_top_label_eight_points"]
)
def test_ece_hand_worked_variants_and_independent_route(name: str) -> None:
    case = _fixture(name)
    result = calibration_reference.ece(
        case["probs"],
        case["labels"],
        case["n_bins"],
        variant=case["variant"],
    )
    if case["variant"] == "positive_class":
        expected = (
            Fraction(15, 100)
            + Fraction(125, 1000)
            + Fraction(375, 1000)
            + Fraction(35, 100)
        ) / 4
    else:
        expected = Fraction(1, 2) * Fraction(125, 1000) + Fraction(1, 2) * Fraction(
            1, 10
        )
    assert float(expected) == case["expected"]
    assert result == pytest.approx(float(expected))


def test_uneven_ece_uses_count_weighting_and_mce() -> None:
    case = _fixture("ece_uneven_bin_counts")
    expected = (
        Fraction(2, 4) * Fraction(35, 100)
        + Fraction(1, 4) * Fraction(7, 10)
        + Fraction(1, 4) * Fraction(9, 10)
    )
    assert calibration_reference.ece(case["probs"], case["labels"], 4) == float(
        expected
    )
    assert calibration_reference.mce(case["probs"], case["labels"], 4) == 0.9


def test_edge_values_switch_bins_with_right_closed() -> None:
    case = _fixture("edge_assignment")
    left = calibration_reference.reliability_bins(
        case["probs"], case["labels"], case["n_bins"], right_closed=False
    )
    right = calibration_reference.reliability_bins(
        case["probs"], case["labels"], case["n_bins"], right_closed=True
    )
    assert left[case["expected_false_bin"]]["count"] == 1
    assert right[case["expected_true_bin"]]["count"] == 1

    edge_ece = _fixture("edge_ece_right_closed")
    independent_false = abs(Fraction(1, 2) - (Fraction(1, 2) + Fraction(3, 4)) / 2)
    independent_true = Fraction(1, 2) * abs(Fraction(1) - Fraction(1, 2)) + Fraction(
        1, 2
    ) * abs(Fraction(0) - Fraction(3, 4))
    assert float(independent_false) == edge_ece["expected_false"]
    assert float(independent_true) == edge_ece["expected_true"]
    assert (
        calibration_reference.ece(
            edge_ece["probs"], edge_ece["labels"], 2, right_closed=False
        )
        == edge_ece["expected_false"]
    )
    assert (
        calibration_reference.ece(
            edge_ece["probs"], edge_ece["labels"], 2, right_closed=True
        )
        == edge_ece["expected_true"]
    )


def test_equal_mass_remainder_and_empty_bins() -> None:
    case = _fixture("equal_mass_remainder")
    bins = calibration_reference.reliability_bins(
        case["probs"], case["labels"], case["n_bins"], scheme="equal_mass"
    )
    ordered = sorted(zip(case["probs"], case["labels"], strict=False))
    expected_groups = [ordered[:2], ordered[2:4], ordered[4:]]
    assert [len(group) for group in expected_groups] == case["expected_counts"]
    assert [group[0][0] for group in expected_groups] == case["expected_lower"]
    assert [group[-1][0] for group in expected_groups] == case["expected_upper"]
    assert [entry["count"] for entry in bins] == case["expected_counts"]
    assert [entry["lower"] for entry in bins] == case["expected_lower"]
    assert [entry["upper"] for entry in bins] == case["expected_upper"]

    empty_bins = calibration_reference.reliability_bins(
        [0.2], [0], 3, scheme="equal_mass"
    )
    assert [entry["count"] for entry in empty_bins] == [1, 0, 0]
    assert empty_bins[1]["mean_confidence"] is None
    assert empty_bins[2]["observed"] is None


def test_equal_mass_ties_are_stable() -> None:
    case = _fixture("equal_mass_stable_ties")
    bins = calibration_reference.reliability_bins(
        case["probs"], case["labels"], case["n_bins"], scheme="equal_mass"
    )
    assert [entry["count"] for entry in bins] == case["expected_counts"]
    assert [entry["observed"] for entry in bins] == case["expected_observed"]
    assert bins[0]["mean_confidence"] == pytest.approx(0.3)
    assert bins[1]["mean_confidence"] == pytest.approx(0.65)


@pytest.mark.parametrize("name", ["conformal_ten_alpha_01", "conformal_ten_alpha_02"])
def test_conformal_hand_worked_fixtures(name: str) -> None:
    case = _fixture(name)
    scores = case["scores"]
    expected_rank = int(case["expected_rank"])
    expected_quantile = float(case["expected_quantile"])
    assert (
        calibration_reference.conformal_rank(len(scores), case["alpha"])
        == expected_rank
    )
    assert (
        calibration_reference.conformal_quantile(scores, case["alpha"])
        == expected_quantile
    )
    exact_alpha = Fraction(str(case["alpha"]))
    exact_value = len(scores) + 1
    exact_value *= 1 - exact_alpha
    independent_rank = (
        exact_value.numerator + exact_value.denominator - 1
    ) // exact_value.denominator
    assert independent_rank == expected_rank
    assert sorted(scores)[expected_rank - 1] == expected_quantile


def test_conformal_rank_avoids_float_rounding_failure() -> None:
    case = _fixture("conformal_exact_float_failure")
    assert (
        calibration_reference.conformal_rank(case["n"], case["alpha"])
        == case["expected_rank"]
    )
    naive = math.ceil((case["n"] + 1) * (1 - float(case["alpha"])))
    assert naive != case["expected_rank"]


def test_brier_wrong_variants_are_caught() -> None:
    case = _fixture("brier_four_points")
    probs, labels = case["probs"], case["labels"]
    wrong = [
        lambda: sum(
            probability - label
            for probability, label in zip(probs, labels, strict=False)
        )
        / len(labels),
        lambda: sum(
            (probability - label) ** 2
            for probability, label in zip(probs, labels, strict=False)
        ),
        lambda: sum(
            (probability - (1 - label)) ** 2
            for probability, label in zip(probs, labels, strict=False)
        )
        / len(labels),
    ]
    assert all(function() != case["expected"] for function in wrong)


def test_ece_wrong_variants_are_caught() -> None:
    uneven = _fixture("ece_uneven_bin_counts")
    edge = _fixture("edge_ece_right_closed")
    top = _fixture("ece_top_label_eight_points")
    bins = calibration_reference.reliability_bins(uneven["probs"], uneven["labels"], 4)

    def equal_bin_weight_ece() -> float:
        return (
            sum(
                abs(entry["observed"] - entry["mean_confidence"])
                for entry in bins
                if entry["count"]
            )
            / 3
        )

    def always_zero_ece() -> float:
        return 0.0

    def swapped_edge_rule_ece() -> float:
        return calibration_reference.ece(
            edge["probs"], edge["labels"], 2, right_closed=False
        )

    wrong = [equal_bin_weight_ece, always_zero_ece, swapped_edge_rule_ece]
    assert wrong[0]() != uneven["expected"]
    assert wrong[1]() != uneven["expected"]
    assert wrong[2]() != edge["expected_true"]
    assert (
        calibration_reference.ece(
            top["probs"], top["labels"], 4, variant="positive_class"
        )
        != top["expected"]
    )


def test_conformal_wrong_variants_are_caught() -> None:
    case = _fixture("conformal_ten_alpha_01")
    scores, alpha = case["scores"], case["alpha"]
    exact_failure = _fixture("conformal_exact_float_failure")
    exact_scores = [index / 10 for index in range(1, 10)]

    def omitted_plus_one_quantile() -> float:
        rank = math.ceil(len(scores) * (1 - float(alpha)))
        return sorted(scores)[rank - 1]

    def floor_quantile() -> float:
        rank = math.floor((len(scores) + 1) * (1 - float(alpha)))
        return sorted(scores)[rank - 1]

    def naive_float_quantile() -> float:
        rank = math.ceil((exact_failure["n"] + 1) * (1 - float(exact_failure["alpha"])))
        return sorted(exact_scores)[rank - 1]

    wrong = [omitted_plus_one_quantile, floor_quantile, naive_float_quantile]
    assert wrong[0]() != calibration_reference.conformal_quantile(scores, alpha)
    assert wrong[1]() != calibration_reference.conformal_quantile(scores, alpha)
    assert wrong[2]() != calibration_reference.conformal_quantile(
        exact_scores, exact_failure["alpha"]
    )


def test_brier_properties() -> None:
    randomizer = random.Random(17)
    for _ in range(40):
        probs = [randomizer.random() for _ in range(12)]
        labels = [randomizer.randrange(2) for _ in range(12)]
        assert 0.0 <= calibration_reference.brier_score(probs, labels) <= 1.0
    assert calibration_reference.brier_score([0.0, 1.0], [0, 1]) == 0.0
    assert calibration_reference.brier_score([0.5] * 4, [0, 1, 0, 1]) == 0.25


def test_ece_mce_and_bin_count_properties() -> None:
    probs = [0.05, 0.15, 0.25, 0.35, 0.55, 0.75, 0.95]
    labels = [0, 0, 1, 0, 1, 1, 1]
    bins = calibration_reference.reliability_bins(probs, labels, 5)
    assert sum(entry["count"] for entry in bins) == len(probs)
    assert 0.0 <= calibration_reference.ece(probs, labels, 5) <= 1.0
    assert 0.0 <= calibration_reference.mce(probs, labels, 5) <= 1.0
    shuffled = list(zip(probs, labels, strict=False))
    random.Random(3).shuffle(shuffled)
    shuffled_probs, shuffled_labels = zip(*shuffled, strict=False)
    assert calibration_reference.ece(
        list(shuffled_probs), list(shuffled_labels), 5
    ) == calibration_reference.ece(probs, labels, 5)
    assert calibration_reference.ece([0.0, 0.0, 1.0, 1.0], [0, 0, 1, 1], 2) == 0.0


def test_conformal_properties() -> None:
    scores = [0.1, 0.4, 0.2, 0.9]
    for n in range(1, 30):
        for alpha in ("0.1", "0.2", "0.7"):
            assert calibration_reference.conformal_rank(n, alpha) <= n + 1
    for alpha in ("0.1", "0.2", "0.9"):
        quantile = calibration_reference.conformal_quantile(scores, alpha)
        assert quantile in scores or math.isinf(quantile)


@pytest.mark.parametrize(
    "call",
    [
        lambda: calibration_reference.brier_score([], []),
        lambda: calibration_reference.brier_score([0.1], []),
        lambda: calibration_reference.brier_score([1.1], [0]),
        lambda: calibration_reference.brier_score([float("nan")], [0]),
        lambda: calibration_reference.brier_score([0.1], [2]),
        lambda: calibration_reference.reliability_bins([0.1], [0], 0),
        lambda: calibration_reference.reliability_bins([0.1], [0], 2, scheme="unknown"),
        lambda: calibration_reference.reliability_bins(
            [0.1], [0], 2, variant="unknown"
        ),
        lambda: calibration_reference.conformal_quantile([], "0.1"),
        lambda: calibration_reference.conformal_quantile([float("nan")], "0.1"),
        lambda: calibration_reference.conformal_quantile([0.1], "0"),
        lambda: calibration_reference.conformal_quantile([0.1], "1"),
    ],
)
def test_invalid_inputs_raise_value_error(call) -> None:
    with pytest.raises(ValueError):
        call()

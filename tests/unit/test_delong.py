"""Independent checks against the Phase 10 contract and exact fixtures."""

import json
from dataclasses import FrozenInstanceError
from fractions import Fraction
from math import erfc, inf, sqrt
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.statistics.delong import delong_paired_auroc

FIXTURES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "phase10_stats.json").read_text()
)


def _brute_force(a, b, labels):
    """O(m n) reference using all four covariance entries from S1."""
    positives = [i for i, label in enumerate(labels) if label == 1]
    negatives = [i for i, label in enumerate(labels) if label == 0]
    m, n = len(positives), len(negatives)
    aucs, rows, columns = [], [], []
    for scores in (a, b):
        kernel = [
            [
                Fraction(int(scores[i] > scores[j]))
                + Fraction(int(scores[i] == scores[j]), 2)
                for j in negatives
            ]
            for i in positives
        ]
        rows.append([sum(row, Fraction(0)) / n for row in kernel])
        columns.append(
            [sum((row[j] for row in kernel), Fraction(0)) / m for j in range(n)]
        )
        aucs.append(sum(rows[-1], Fraction(0)) / m)
    variance = Fraction(0)
    for placements, size in ((rows, m), (columns, n)):
        covariance = [
            [
                sum(
                    (
                        (x - aucs[k]) * (y - aucs[column])
                        for x, y in zip(placements[k], placements[column], strict=True)
                    ),
                    Fraction(0),
                )
                / (size - 1)
                for column in range(2)
            ]
            for k in range(2)
        ]
        variance += (covariance[0][0] + covariance[1][1] - 2 * covariance[0][1]) / size
    return *aucs, aucs[0] - aucs[1], variance


@pytest.mark.parametrize("case", FIXTURES["delong"], ids=lambda case: case["name"])
def test_exact_fixtures(case):
    result = delong_paired_auroc(case["scores_a"], case["scores_b"], case["labels"])
    for field in ("auc_a", "auc_b", "difference", "variance"):
        assert getattr(result, field) == pytest.approx(
            float(Fraction(case[field])), abs=1e-15, rel=0
        )
    for field in ("z", "p_value"):
        assert getattr(result, field) == pytest.approx(
            float(case[field]), abs=1e-12, rel=0
        )
    assert result.n_positive == case["n_positive"]
    assert result.n_negative == case["n_negative"]


def test_swap_fixture_and_z_symmetry():
    swap = FIXTURES["delong_swap_check"]
    case = next(case for case in FIXTURES["delong"] if case["name"] == swap["case"])
    forward = delong_paired_auroc(case["scores_a"], case["scores_b"], case["labels"])
    reverse = delong_paired_auroc(case["scores_b"], case["scores_a"], case["labels"])
    assert reverse.difference == float(Fraction(swap["swapped_difference"]))
    assert reverse.p_value == pytest.approx(swap["swapped_p_value"], abs=1e-12, rel=0)
    assert reverse.z == -forward.z
    assert reverse.variance == forward.variance
    assert reverse.p_value == forward.p_value


@pytest.mark.parametrize("case", FIXTURES["delong"], ids=lambda case: case["name"])
def test_swap_all_fixtures_including_zero_variance(case):
    forward = delong_paired_auroc(case["scores_a"], case["scores_b"], case["labels"])
    reverse = delong_paired_auroc(case["scores_b"], case["scores_a"], case["labels"])
    assert reverse.auc_a == forward.auc_b
    assert reverse.auc_b == forward.auc_a
    assert reverse.difference == -forward.difference
    assert reverse.z == -forward.z
    assert reverse.variance == forward.variance
    assert reverse.p_value == forward.p_value


def test_all_scores_tied():
    result = delong_paired_auroc([1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 1, 1])
    assert result.auc_a == result.auc_b == 0.5
    assert result.difference == result.variance == result.z == 0
    assert result.p_value == 1


def test_brute_force_reference_with_ties_and_patient_reordering():
    rng = np.random.default_rng(101)
    for _ in range(40):
        labels = rng.permutation([1] * 7 + [0] * 9)
        a, b = rng.integers(-3, 4, size=(2, len(labels)))
        expected = _brute_force(a, b, labels)
        result = delong_paired_auroc(a, b, labels)
        for field, value in zip(
            ("auc_a", "auc_b", "difference", "variance"), expected, strict=True
        ):
            assert getattr(result, field) == pytest.approx(
                float(value), abs=1e-15, rel=0
            )
        if result.variance:
            z = float(expected[2]) / sqrt(float(expected[3]))
            assert result.z == pytest.approx(z, abs=1e-12, rel=0)
            assert result.p_value == pytest.approx(
                erfc(abs(z) / sqrt(2)), abs=1e-12, rel=0
            )


def test_fraction_scores_are_not_rounded_to_float():
    tiny = Fraction(1, 10**100)
    a = [Fraction(1) + tiny, Fraction(1) + 2 * tiny, Fraction(1), Fraction(1)]
    result = delong_paired_auroc(a, list(reversed(a)), [1, 1, 0, 0])
    assert result.auc_a == 1
    assert result.auc_b == 0
    assert result.variance == 0
    assert result.z == inf
    assert result.p_value == 0


def test_identical_predictors_and_frozen_result():
    result = delong_paired_auroc([0, 1, 0, 1], [0, 1, 0, 1], [0, 0, 1, 1])
    assert result.difference == result.variance == result.z == 0
    assert result.p_value == 1
    with pytest.raises(FrozenInstanceError):
        result.p_value = 0


@pytest.mark.parametrize(
    "a,b,labels",
    [
        ([], [], []),
        ([1, 2], [1], [0, 1]),
        ([1, 2, 3, 4], [1, 2, 3, 4], [0, 1, 1, 1]),
        ([1, 2, 3, 4], [1, 2, 3, 4], [0, 0, 0, 1]),
        ([1, 2, 3, 4], [1, 2, 3, 4], [0, 0, 1, 2]),
        ([1, 2, 3, 4], [1, 2, 3, 4], [0, 0, 0, 0]),
        ([[1], [2]], [1, 2], [0, 1]),
    ],
)
def test_invalid_inputs(a, b, labels):
    with pytest.raises(ValueError):
        delong_paired_auroc(a, b, labels)


@pytest.mark.parametrize("invalid", [float("nan"), inf, -inf])
@pytest.mark.parametrize("argument", [0, 1, 2])
def test_nonfinite_inputs(invalid, argument):
    args = [[0, 1, 2, 3], [0, 1, 2, 3], [0, 0, 1, 1]]
    args[argument][0] = invalid
    with pytest.raises(ValueError):
        delong_paired_auroc(*args)

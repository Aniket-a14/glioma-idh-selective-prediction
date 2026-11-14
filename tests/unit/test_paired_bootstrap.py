"""Phase 10 paired-bootstrap fixtures, pairing, and coverage checks."""

import json
from dataclasses import FrozenInstanceError
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.statistics.paired import paired_bootstrap, paired_bootstrap_p
from glioma_selective.statistics.resampling import (
    bootstrap_indices,
    percentile_interval,
)

FIXTURES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "phase10_stats.json").read_text()
)


def _mean_difference(a, b):
    return float(np.mean(a) - np.mean(b))


@pytest.mark.parametrize("case", FIXTURES["paired_p_value"])
def test_p_value_exact_fixtures(case):
    p = paired_bootstrap_p(case["differences"])
    assert isinstance(p, Fraction)
    assert p == Fraction(case["p_value"])


def test_paired_bootstrap_fixture():
    case = FIXTURES["paired_bootstrap"]
    indices = bootstrap_indices(case["n"], case["iterations"], case["seed"])
    np.testing.assert_array_equal(indices, case["bootstrap_indices"])
    result = paired_bootstrap(
        _mean_difference,
        [case["array_a"], case["array_b"]],
        case["iterations"],
        case["seed"],
        min_iterations=2,
    )
    # S3 permits absolute 1e-12 rounding error for the unchanged float callback.
    assert result.point == pytest.approx(
        float(Fraction(case["point"])), abs=1e-12, rel=0
    )
    np.testing.assert_allclose(
        result.values, [float(Fraction(v)) for v in case["values"]], atol=1e-12, rtol=0
    )
    # Linear 2.5th/97.5th percentiles of [4/5, 6/5] are 81/100, 119/100.
    assert result.lower == pytest.approx(float(Fraction(81, 100)), abs=1e-12, rel=0)
    assert result.upper == pytest.approx(float(Fraction(119, 100)), abs=1e-12, rel=0)
    assert (result.lower, result.upper) == percentile_interval(result.values)
    assert result.p_value == Fraction(2, 3)
    assert result.iterations == case["iterations"]
    with pytest.raises(FrozenInstanceError):
        result.point = 0


def test_reproducible_without_changing_global_random_state():
    before = np.random.get_state()
    first = paired_bootstrap(_mean_difference, [[1, 3, 5], [2, 2, 3]], 1000, 31)
    second = paired_bootstrap(_mean_difference, [[1, 3, 5], [2, 2, 3]], 1000, 31)
    np.testing.assert_array_equal(first.values, second.values)
    assert first.point == second.point
    assert (first.lower, first.upper, first.p_value) == (
        second.lower,
        second.upper,
        second.p_value,
    )
    after = np.random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_patient_resampled_as_a_unit_across_all_arrays():
    ids = np.array([10, 20, 30, 40, 50])
    a, b, labels = ids * 2, ids * 3, np.array([0, 1, 0, 1, 1])
    seen = []

    def statistic(patient_ids, scores_a, scores_b, y):
        np.testing.assert_array_equal(scores_a, 2 * patient_ids)
        np.testing.assert_array_equal(scores_b, 3 * patient_ids)
        np.testing.assert_array_equal(y, labels[np.searchsorted(ids, patient_ids)])
        seen.append(patient_ids.copy())
        return float(np.mean(scores_a - scores_b))

    result = paired_bootstrap(statistic, [ids, a, b, labels], 7, 0, min_iterations=7)
    np.testing.assert_array_equal(seen[0], ids)
    indices = bootstrap_indices(len(ids), 7, 0)
    np.testing.assert_array_equal(seen[1:], ids[indices])
    assert result.point == -30


def test_custom_interval_level():
    result = paired_bootstrap(
        _mean_difference,
        [[1, 2, 3, 4, 5], [0, 1, 1, 2, 5]],
        2,
        0,
        level=0.5,
        min_iterations=2,
    )
    # Linear 25th/75th percentiles of [4/5, 6/5] are 9/10, 11/10.
    assert (result.lower, result.upper) == pytest.approx(
        (float(Fraction(9, 10)), float(Fraction(11, 10))), abs=1e-12, rel=0
    )
    assert result.p_value == paired_bootstrap_p(result.values)


def test_exact_fraction_p_values_preserve_sign_below_float_range():
    tiny = Fraction(1, 10**400)
    assert paired_bootstrap_p([tiny] * 10) == Fraction(2, 11)
    assert paired_bootstrap_p([-tiny] * 10) == Fraction(2, 11)
    assert paired_bootstrap_p([Fraction(0), tiny, -tiny]) == 1


def test_interval_coverage_on_100_simulations_of_known_difference():
    rng = np.random.default_rng(20261114)
    covered = 0
    truth = 0.4
    for simulation in range(100):
        shared = rng.normal(size=120)
        a = shared + truth + rng.normal(size=120)
        b = shared + rng.normal(size=120)
        result = paired_bootstrap(_mean_difference, [a, b], 1000, simulation)
        covered += result.lower <= truth <= result.upper
    coverage = covered / 100
    assert 0.90 <= coverage <= 1.00, coverage


def test_p_value_monotone_as_differences_move_away_from_zero():
    base = np.arange(-10, 11, dtype=float)
    probabilities = [paired_bootstrap_p(base + shift) for shift in range(21)]
    assert all(0 < p <= 1 for p in probabilities)
    assert all(
        left >= right
        for left, right in zip(probabilities, probabilities[1:], strict=False)
    )
    for shift in range(21):
        assert paired_bootstrap_p(-(base + shift)) == probabilities[shift]
    assert paired_bootstrap_p([0.0] * 10) == 1
    assert paired_bootstrap_p([1e-320] * 10) == Fraction(2, 11)
    assert paired_bootstrap_p([-0.0, 0.0]) == 1


@pytest.mark.parametrize("iterations", [0, 1, 999, -1, 1.5, True])
def test_default_min_iterations_enforced(iterations):
    with pytest.raises(ValueError, match="iterations"):
        paired_bootstrap(_mean_difference, [[1, 2], [0, 1]], iterations, 0)


@pytest.mark.parametrize("minimum", [0, -1, 1.5, True])
def test_invalid_min_iterations(minimum):
    with pytest.raises(ValueError, match="min_iterations"):
        paired_bootstrap(
            _mean_difference, [[1, 2], [0, 1]], 1000, 0, min_iterations=minimum
        )


@pytest.mark.parametrize(
    "arrays", [[], [[]], [[1, 2], [1]], [[[1, 2]]], [[float("nan")]], [[float("inf")]]]
)
def test_invalid_arrays(arrays):
    with pytest.raises(ValueError):
        paired_bootstrap(lambda *args: 0.0, arrays, 1000, 0)


@pytest.mark.parametrize("level", [0, 1, -0.1, 1.1, float("nan"), float("inf")])
def test_invalid_level(level):
    with pytest.raises(ValueError, match="level"):
        paired_bootstrap(lambda x: 0.0, [[1, 2]], 1000, 0, level=level)


@pytest.mark.parametrize(
    "differences", [[], [[1, 2]], [float("nan")], [float("inf")], [-float("inf")]]
)
def test_invalid_p_value_input(differences):
    with pytest.raises(ValueError):
        paired_bootstrap_p(differences)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("bad_draw", [False, True])
def test_nonfinite_statistic_rejected(invalid, bad_draw):
    calls = 0

    def statistic(x):
        nonlocal calls
        calls += 1
        return invalid if calls == (2 if bad_draw else 1) else 0.0

    with pytest.raises(ValueError, match="finite"):
        paired_bootstrap(statistic, [[1, 2]], 1000, 0)

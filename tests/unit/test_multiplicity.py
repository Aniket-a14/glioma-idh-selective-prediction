"""Tests for the exact Phase 09 Benjamini-Hochberg adjustment."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from glioma_selective.statistics.multiplicity import benjamini_hochberg


@pytest.fixture(scope="module")
def cases() -> dict[str, list[dict[str, object]]]:
    """Load the shared Phase 09 hand-calculated fixtures."""
    path = Path(__file__).parents[1] / "fixtures" / "phase09_stats.json"
    return json.loads(path.read_text())


def test_benjamini_hochberg_fixtures(
    cases: dict[str, list[dict[str, object]]],
) -> None:
    for case in cases["bh"]:
        adjusted, reject = benjamini_hochberg(case["p"], float(case["q"]))
        expected = [Fraction(value) for value in case["adjusted"]]
        assert adjusted == expected
        assert reject == case["reject"]
        assert all(isinstance(value, Fraction) for value in adjusted)
        assert all(type(value) is bool for value in reject)


def test_benjamini_hochberg_monotonicity_and_raw_lower_bound() -> None:
    p_values = [0.06, 0.001, 0.4, 0.2, 0.001, 0.9]
    adjusted, _ = benjamini_hochberg(p_values, 0.05)
    sorted_pairs = sorted(zip(p_values, adjusted, strict=True))
    sorted_adjusted = [value for _, value in sorted_pairs]
    assert sorted_adjusted == sorted(sorted_adjusted)
    assert all(
        Fraction(repr(raw)) <= value
        for raw, value in zip(p_values, adjusted, strict=True)
    )


def test_benjamini_hochberg_ties_share_adjustment_and_all_ones_stay_one() -> None:
    adjusted, _ = benjamini_hochberg([0.02, 0.01, 0.02, 0.02], 0.05)
    assert adjusted[0] == adjusted[2] == adjusted[3]
    all_one_adjusted, all_one_reject = benjamini_hochberg([1.0] * 5, 0.05)
    assert all_one_adjusted == [Fraction(1)] * 5
    assert all_one_reject == [False] * 5


@pytest.mark.parametrize(
    "p_values,q",
    [
        ([], 0.05),
        ([0.1, float("nan")], 0.05),
        ([0.1, float("inf")], 0.05),
        ([0.1], 0.0),
        ([0.1], 1.0),
        ([0.1], float("nan")),
        ([1.1], 0.05),
    ],
)
def test_benjamini_hochberg_rejects_invalid_inputs(
    p_values: list[float], q: float
) -> None:
    with pytest.raises(ValueError):
        benjamini_hochberg(p_values, q)

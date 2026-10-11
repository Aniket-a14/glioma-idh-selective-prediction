"""Tests for the Phase 09 resampling primitives."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.statistics.resampling import (
    bootstrap_indices,
    percentile_interval,
)


@pytest.fixture(scope="module")
def cases() -> dict[str, list[dict[str, object]]]:
    """Load the shared Phase 09 hand-calculated fixtures."""
    path = Path(__file__).parents[1] / "fixtures" / "phase09_stats.json"
    return json.loads(path.read_text())


def test_bootstrap_indices_fixtures(
    cases: dict[str, list[dict[str, object]]],
) -> None:
    for case in cases["bootstrap_indices"]:
        actual = bootstrap_indices(
            int(case["n"]), int(case["iterations"]), int(case["seed"])
        )
        np.testing.assert_array_equal(actual, case["indices"])
        assert actual.dtype == np.int64


def test_bootstrap_indices_seed_behavior() -> None:
    first = bootstrap_indices(17, 8, 41)
    np.testing.assert_array_equal(first, bootstrap_indices(17, 8, 41))
    assert not np.array_equal(first, bootstrap_indices(17, 8, 42))


@pytest.mark.parametrize("n,iterations", [(0, 1), (3, 0), (-1, 2)])
def test_bootstrap_indices_rejects_nonpositive_dimensions(
    n: int, iterations: int
) -> None:
    with pytest.raises(ValueError):
        bootstrap_indices(n, iterations, 0)


def test_percentile_interval_fixtures(
    cases: dict[str, list[dict[str, object]]],
) -> None:
    for case in cases["percentile_interval"]:
        raw_values = case["values"]
        values = list(range(101)) if raw_values == "range(0, 101)" else raw_values
        actual = percentile_interval(values, float(case["level"]))
        assert actual == tuple(case["interval"])
        assert all(type(bound) is float for bound in actual)


@pytest.mark.parametrize(
    "values,level",
    [([], 0.95), ([1.0, float("nan")], 0.95), ([1.0, float("inf")], 0.95)],
)
def test_percentile_interval_rejects_empty_or_nonfinite_values(
    values: list[float], level: float
) -> None:
    with pytest.raises(ValueError):
        percentile_interval(values, level)


@pytest.mark.parametrize("level", [0.0, 1.0, float("nan"), float("inf")])
def test_percentile_interval_rejects_invalid_level(level: float) -> None:
    with pytest.raises(ValueError):
        percentile_interval([1.0], level)

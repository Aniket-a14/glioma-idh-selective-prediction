"""Tests for Phase 09 enrichment permutation calculations."""

from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.statistics.permutation import (
    EnrichmentResult,
    enrichment_exact_p,
    enrichment_permutation_test,
)


@pytest.fixture(scope="module")
def cases() -> dict[str, list[dict[str, object]]]:
    """Load the shared Phase 09 hand-calculated fixtures."""
    path = Path(__file__).parents[1] / "fixtures" / "phase09_stats.json"
    return json.loads(path.read_text())


def test_enrichment_fixtures_and_monte_carlo_crosscheck(
    cases: dict[str, list[dict[str, object]]],
) -> None:
    for case in cases["enrichment"]:
        rejected = case["rejected"]
        errors = case["errors"]
        exact = None if case["exact_p"] is None else Fraction(str(case["exact_p"]))
        assert enrichment_exact_p(rejected, errors) == exact
        result = enrichment_permutation_test(rejected, errors, 10_000, 0)
        assert result.n_rejected == case["n_rejected"]
        if exact is None:
            assert result == EnrichmentResult(None, None, 0)
            continue
        assert result.observed == pytest.approx(
            float(Fraction(str(case["observed_difference"])))
        )
        assert result.p_value is not None
        tolerance = (
            4 * math.sqrt(float(exact) * (1 - float(exact)) / 10_000) + 1 / 10_001
        )
        assert abs(result.p_value - float(exact)) <= tolerance


@pytest.mark.parametrize("seed", [1, 73])
def test_monte_carlo_enrichment_matches_exact_with_additional_seeds(
    cases: dict[str, list[dict[str, object]]], seed: int
) -> None:
    for case in cases["enrichment"]:
        exact = enrichment_exact_p(case["rejected"], case["errors"])
        if exact is None:
            continue
        result = enrichment_permutation_test(
            case["rejected"], case["errors"], 10_000, seed
        )
        assert result.p_value is not None
        tolerance = (
            4 * math.sqrt(float(exact) * (1 - float(exact)) / 10_000) + 1 / 10_001
        )
        assert abs(result.p_value - float(exact)) <= tolerance


def test_permutation_seed_behavior() -> None:
    rejected = [1, 1, 1, 0, 0, 0, 0, 0, 0, 0]
    errors = [1, 1, 0, 1, 1, 0, 0, 0, 0, 0]
    first = enrichment_permutation_test(rejected, errors, 200, 2)
    assert first == enrichment_permutation_test(rejected, errors, 200, 2)
    assert first != enrichment_permutation_test(rejected, errors, 200, 3)


def test_exact_enrichment_is_invariant_to_consistent_patient_reordering() -> None:
    rejected = np.array([1, 0, 1, 0, 0, 1, 0])
    errors = np.array([1, 1, 0, 1, 0, 0, 1])
    order = np.array([6, 2, 5, 0, 4, 1, 3])
    assert enrichment_exact_p(rejected, errors) == enrichment_exact_p(
        rejected[order], errors[order]
    )


def test_permutation_all_rejected_has_zero_difference_and_unit_p() -> None:
    result = enrichment_permutation_test([1, 1, 1], [1, 0, 1], 10, 0)
    assert result == EnrichmentResult(observed=0.0, p_value=1.0, n_rejected=3)


@pytest.mark.parametrize(
    "rejected,errors,permutations",
    [
        ([], [], 5),
        ([1], [], 5),
        ([1], [0.5], 5),
        ([1], [float("nan")], 5),
        ([1], [float("inf")], 5),
        ([1], [0], 0),
    ],
)
def test_permutation_rejects_invalid_inputs(
    rejected: list[float | int], errors: list[float | int], permutations: int
) -> None:
    with pytest.raises(ValueError):
        enrichment_permutation_test(rejected, errors, permutations, 0)


@pytest.mark.parametrize(
    "rejected,errors",
    [([], []), ([1], []), ([1], [0.5]), ([1], [float("nan")]), ([1], [float("inf")])],
)
def test_exact_permutation_rejects_invalid_inputs(
    rejected: list[float | int], errors: list[float | int]
) -> None:
    with pytest.raises(ValueError):
        enrichment_exact_p(rejected, errors)

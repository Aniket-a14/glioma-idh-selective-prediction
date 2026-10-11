"""Claim decision rules D1-D4 against ``tests/fixtures/phase09_stats.json``."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import pytest

from glioma_selective.selective.claims import (
    deviation_label,
    status_c4,
    status_c5,
    status_c6,
    status_risk_difference,
    worst_status,
)

FIXTURES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "phase09_stats.json").read_text()
)


@pytest.mark.parametrize(
    "case", FIXTURES["status_risk_difference"], ids=lambda c: c["name"]
)
def test_risk_difference_status(case: dict) -> None:
    assert status_risk_difference(case["points"], case["uppers"]) == case["status"]


@pytest.mark.parametrize("case", FIXTURES["status_c5"], ids=lambda c: c["name"])
def test_c5_status(case: dict) -> None:
    assert status_c5(case["points"], case["lowers"]) == case["status"]


@pytest.mark.parametrize("case", FIXTURES["status_c6"], ids=lambda c: c["name"])
def test_c6_status(case: dict) -> None:
    assert status_c6(case["observed"], case["adjusted_p"]) == case["status"]


@pytest.mark.parametrize("case", FIXTURES["c4"], ids=lambda c: c["name"])
def test_c4_label(case: dict) -> None:
    result = deviation_label(case["lo"], case["hi"], case["band"])
    assert result.label == case["label"]
    assert result.characterized is case["characterized"]
    assert result.half_width == pytest.approx(case["half_width"], abs=1e-12)


@pytest.mark.parametrize("case", FIXTURES["worst_status"])
def test_worst_status(case: dict) -> None:
    assert worst_status(case["statuses"]) == case["worst"]


def test_c4_claim_is_refuted_when_any_condition_is_too_wide() -> None:
    narrow = (-0.02, 0.03)
    wide = (-0.09, 0.08)
    assert status_c4([narrow, narrow], 0.07) == "supported"
    assert status_c4([narrow, wide], 0.07) == "refuted"


def test_c4_half_width_exactly_at_the_band_is_characterized() -> None:
    assert deviation_label(-0.07, 0.07, 0.07).characterized is True
    assert status_c4([(-0.07, 0.07)], 0.07) == "supported"


def test_c4_interval_touching_the_band_edge_is_preserved_not_degraded() -> None:
    assert deviation_label(0.0, 0.07, 0.07).label == "preserved"
    assert deviation_label(0.07, 0.09, 0.07).label == "indeterminate"


def test_c6_accepts_fractions_from_benjamini_hochberg() -> None:
    assert status_c6([0.1, 0.1], [Fraction(1, 25), Fraction(1, 20)]) == "inconclusive"
    assert status_c6([0.1, 0.1], [Fraction(1, 25), Fraction(1, 21)]) == "supported"


def test_upper_limit_exactly_zero_is_not_below_zero() -> None:
    assert status_risk_difference([-0.1], [0.0]) == "inconclusive"
    assert status_risk_difference([-0.1], [-1e-12]) == "supported"


@pytest.mark.parametrize(
    "call",
    [
        lambda: status_risk_difference([], []),
        lambda: status_risk_difference([0.1], [0.1, 0.2]),
        lambda: status_risk_difference([float("nan")], [0.0]),
        lambda: status_c5([0.0], []),
        lambda: status_c6([0.1], [0.1, 0.2]),
        lambda: status_c4([], 0.07),
        lambda: deviation_label(0.1, -0.1, 0.07),
        lambda: deviation_label(-0.1, 0.1, 0.0),
        lambda: worst_status([]),
        lambda: worst_status(["maybe"]),  # type: ignore[list-item]
    ],
)
def test_bad_input_raises(call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError):
        call()

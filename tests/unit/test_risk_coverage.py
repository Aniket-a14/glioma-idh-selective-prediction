"""S1 and S4 of the Phase 09 contract against the hand-derived fixtures."""

from __future__ import annotations

import json
import math
import random
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.calibration.temperature import apply_temperature
from glioma_selective.selective.abstention import (
    binary_entropy,
    confidence_scores,
    ensemble_variance_scores,
    mc_dropout_scores,
)
from glioma_selective.selective.risk_coverage import (
    monotonicity_violations,
    rc_points,
)

CASES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "phase09_selective.json").read_text(
        encoding="utf-8"
    )
)["cases"]


def _f(text: str) -> float:
    return float(Fraction(text))


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_points_and_monotonicity_match_fixtures(case: dict[str, object]) -> None:
    points = rc_points(case["scores"], case["losses"])  # type: ignore[arg-type]
    expected = [(_f(c), _f(r)) for c, r in case["points"]]  # type: ignore[attr-defined]
    assert points == expected
    count, size = monotonicity_violations(points)
    assert count == case["monotonicity"][0]  # type: ignore[index]
    assert size == pytest.approx(_f(case["monotonicity"][1]), abs=1e-15)  # type: ignore[index]


def test_points_do_not_depend_on_row_order() -> None:
    rng = random.Random(7)
    scores = [round(rng.random(), 1) for _ in range(40)]
    losses = [rng.randint(0, 1) for _ in range(40)]
    reference = rc_points(scores, losses)
    for _ in range(50):
        order = list(range(40))
        rng.shuffle(order)
        shuffled = rc_points([scores[i] for i in order], [losses[i] for i in order])
        assert shuffled == reference


def test_points_properties() -> None:
    rng = random.Random(8)
    for _ in range(100):
        n = rng.randint(1, 60)
        scores = [round(rng.random(), 2) for _ in range(n)]
        losses = [rng.randint(0, 1) for _ in range(n)]
        points = rc_points(scores, losses)
        coverage = [c for c, _ in points]
        assert all(a < b for a, b in zip(coverage, coverage[1:], strict=False))
        assert points[-1][0] == 1.0
        assert points[-1][1] == pytest.approx(sum(losses) / n, abs=1e-15)
        assert all(0.0 <= r <= 1.0 for _, r in points)


def test_errors() -> None:
    with pytest.raises(ValueError):
        rc_points([], [])
    with pytest.raises(ValueError):
        rc_points([0.5], [1, 0])
    with pytest.raises(ValueError):
        rc_points([float("nan")], [1])
    with pytest.raises(ValueError):
        rc_points([0.5], [-1])
    with pytest.raises(ValueError):
        rc_points([0.5], [float("nan")])
    with pytest.raises(ValueError):
        monotonicity_violations([])
    with pytest.raises(ValueError):
        monotonicity_violations([(0.5, 0.1), (0.5, 0.2)])


def test_monotone_curve_has_no_violations() -> None:
    assert monotonicity_violations([(0.25, 0.0), (0.5, 0.1), (1.0, 0.1)]) == (0, 0.0)


def test_confidence_scores_are_exact_about_ties() -> None:
    # 0.7 and 0.3 are the same confidence, compared exactly.
    scores = confidence_scores([0.7, 0.3, 0.9, 0.1, 0.5])
    assert scores == [0.7, 0.7, 0.9, 0.9, 0.5]
    with pytest.raises(ValueError):
        confidence_scores([1.5])
    with pytest.raises(ValueError):
        confidence_scores([])


def test_entropy_and_mc_dropout_scores() -> None:
    assert binary_entropy(0.5) == pytest.approx(math.log(2), abs=1e-15)
    assert binary_entropy(0.0) == 0.0
    assert binary_entropy(1.0) == 0.0
    assert binary_entropy(0.9) == pytest.approx(
        -(0.9 * math.log(0.9) + 0.1 * math.log(0.1)), abs=1e-15
    )
    scores = mc_dropout_scores([[0.5, 0.5, 0.5], [0.9, 0.9, 0.9], [0.0, 1.0, 0.0]])
    assert scores[0] == pytest.approx(-math.log(2), abs=1e-15)
    assert scores[1] == pytest.approx(-binary_entropy(0.9), abs=1e-15)
    # Mean probability 1/3 uses the mean over passes, not the mean entropy.
    assert scores[2] == pytest.approx(-binary_entropy(1 / 3), abs=1e-15)
    assert scores[0] < scores[1]
    with pytest.raises(ValueError):
        mc_dropout_scores([0.5, 0.5])


def test_ensemble_variance_uses_population_variance() -> None:
    scores = ensemble_variance_scores([[0.2, 0.4, 0.6], [0.5, 0.5, 0.5]])
    assert scores[0] == pytest.approx(-0.08 / 3, abs=1e-15)  # divide by N = 3
    assert scores[1] == 0.0
    assert scores[1] > scores[0]


def test_m1_m2_m5_rank_identically() -> None:
    # Temperature scaling is monotone in the logit and max(p, 1 - p) = sigmoid(|z| / T),
    # so the block-tie risk-coverage points of M1, M2 and M5 coincide (D-047).
    rng = np.random.default_rng(5)
    logits = rng.normal(0, 2.0, 120)
    labels = (rng.random(120) < 1 / (1 + np.exp(-logits))).astype(int)
    losses = [
        int(round(1 / (1 + np.exp(-z))) != y)
        for z, y in zip(logits, labels, strict=True)
    ]
    raw = (1 / (1 + np.exp(-logits))).tolist()
    scaled = apply_temperature(logits, 1.7).tolist()
    assert rc_points(confidence_scores(raw), losses) == rc_points(
        confidence_scores(scaled), losses
    )

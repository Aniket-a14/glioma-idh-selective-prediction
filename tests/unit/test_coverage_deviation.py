"""Two-stage coverage-deviation bootstrap (D5) and monotonicity bootstrap (D6)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.selective.coverage import coverage_deviation_bootstrap
from glioma_selective.selective.risk_coverage import (
    monotonicity_total_bootstrap,
    monotonicity_violations,
    rc_points,
)

FIXTURES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "phase09_stats.json").read_text()
)


def test_degenerate_case_gives_alpha_in_every_draw() -> None:
    case = FIXTURES["coverage_deviation"][0]
    draws = coverage_deviation_bootstrap(
        case["cal_p"],
        case["cal_labels"],
        case["test_p"],
        case["test_labels"],
        case["alpha"],
        case["iterations"],
        case["seed"],
    )
    assert draws.shape == (case["iterations"],)
    assert np.allclose(draws, 0.2, atol=1e-12)


def _exchangeable(n: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    p = rng.uniform(0.02, 0.98, n)
    y = (rng.uniform(size=n) < p).astype(int)  # p is calibrated by construction
    return p, y


def test_exchangeable_data_centres_the_deviation_near_zero() -> None:
    cal_p, cal_y = _exchangeable(400, 1)
    test_p, test_y = _exchangeable(400, 2)
    draws = coverage_deviation_bootstrap(cal_p, cal_y, test_p, test_y, 0.1, 400, 7)
    assert abs(float(draws.mean())) < 0.03
    # the 95% interval is wide enough to contain zero, as it must under exchangeability
    lo, hi = np.percentile(draws, [2.5, 97.5])
    assert lo < 0.0 < hi


def test_same_seed_repeats_and_a_different_seed_changes_the_draws() -> None:
    cal_p, cal_y = _exchangeable(60, 3)
    test_p, test_y = _exchangeable(60, 4)
    a = coverage_deviation_bootstrap(cal_p, cal_y, test_p, test_y, 0.2, 30, 11)
    b = coverage_deviation_bootstrap(cal_p, cal_y, test_p, test_y, 0.2, 30, 11)
    c = coverage_deviation_bootstrap(cal_p, cal_y, test_p, test_y, 0.2, 30, 12)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)


def test_tiny_calibration_set_with_infinite_quantile_covers_everything() -> None:
    # n = 3, alpha = 0.05: k = ceil(4 * 0.95) = 4 > n, so the quantile is +inf
    draws = coverage_deviation_bootstrap(
        [0.9, 0.2, 0.7], [1, 0, 1], [0.6, 0.4], [1, 0], 0.05, 20, 0
    )
    assert np.allclose(draws, 0.05, atol=1e-12)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"iterations": 0},
        {"cal_p": [], "cal_labels": []},
        {"test_p": [0.5], "test_labels": [1, 0]},
    ],
)
def test_coverage_deviation_bad_input(kwargs: dict) -> None:
    args = {
        "cal_p": [0.9, 0.2],
        "cal_labels": [1, 0],
        "test_p": [0.6],
        "test_labels": [1],
        "alpha": 0.2,
        "iterations": 5,
        "seed": 0,
    }
    args.update(kwargs)
    with pytest.raises(ValueError):
        coverage_deviation_bootstrap(**args)


def test_monotonicity_bootstrap_is_zero_for_a_perfect_ranker() -> None:
    scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    losses = [0, 0, 0, 1, 1, 1]  # errors only at the least confident end
    totals = monotonicity_total_bootstrap(scores, losses, 200, 5)
    assert totals.shape == (200,)
    assert float(totals.max()) == 0.0


def test_monotonicity_bootstrap_sees_a_reversal_and_repeats_with_the_seed() -> None:
    scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    losses = [1, 1, 0, 0, 0, 0]  # the most confident cases are the wrong ones
    original = monotonicity_violations(rc_points(scores, losses))[1]
    assert original > 0.0
    a = monotonicity_total_bootstrap(scores, losses, 300, 9)
    b = monotonicity_total_bootstrap(scores, losses, 300, 9)
    assert np.array_equal(a, b)
    assert float(np.percentile(a, 2.5)) > 0.0 or float(a.mean()) > 0.0


def test_monotonicity_bootstrap_bad_input() -> None:
    with pytest.raises(ValueError):
        monotonicity_total_bootstrap([0.5], [1], 0, 0)
    with pytest.raises(ValueError):
        monotonicity_total_bootstrap([], [], 5, 0)
    with pytest.raises(ValueError):
        monotonicity_total_bootstrap([0.5, 0.4], [1], 5, 0)

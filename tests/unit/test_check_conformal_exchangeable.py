"""Smoke test for the exchangeability coverage check (few replications, CPU)."""

from __future__ import annotations

import numpy as np
from scripts import check_conformal_exchangeable as check


def test_synthetic_mean_coverage_is_near_nominal_and_reproducible() -> None:
    first = check.synthetic(reps=200, seed=1)
    second = check.synthetic(reps=200, seed=1)
    assert first == second
    for alpha, (mean, sd) in first.items():
        assert abs(mean - (1 - alpha)) < 0.03
        assert 0 < sd < 0.08


def test_resplit_uses_both_halves() -> None:
    rng = np.random.default_rng(3)
    label = (rng.random(60) < 0.3).astype(int)
    logit = np.where(label == 1, 1.0, -1.0) + rng.normal(0, 1.5, 60)
    result = check.resplit(logit, label, reps=20, seed=0, half=30)
    assert set(result) == set(check.ALPHAS)
    assert all(0.5 < mean <= 1.0 for mean, _ in result.values())

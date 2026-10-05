"""T07.10: the production conformal code against the independent reference.

``src/glioma_selective/calibration/conformal.py`` (Claude) and
``tests/reference/conformal_reference.py`` (Codex, written from the contract
text alone) must agree on randomized inputs.
"""

from __future__ import annotations

import random

import conformal_reference as reference
import pytest

from glioma_selective.calibration import conformal

ALPHAS = (0.05, 0.1, 0.2)


def _cases(seed: int, count: int) -> list[tuple[list[float], list[int]]]:
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        n = rng.choice((1, 2, 5, 9, 19, 20, 50, 123))
        # Mix coarse decimals (boundary-prone) with full-precision doubles.
        if rng.random() < 0.5:
            p = [round(rng.random(), 2) for _ in range(n)]
        else:
            p = [rng.random() for _ in range(n)]
        y = [1 if rng.random() < value else 0 for value in p]
        cases.append((p, y))
    return cases


@pytest.mark.parametrize("alpha", ALPHAS)
def test_scores_and_quantiles_agree(alpha: float) -> None:
    for p, y in _cases(11, 300):
        ours = conformal.nonconformity_scores(p, y)
        theirs = [
            reference.nonconformity_score(a, b) for a, b in zip(p, y, strict=True)
        ]
        assert ours == theirs
        assert conformal.conformal_quantile(
            ours, alpha
        ) == reference.conformal_quantile(theirs, alpha)


@pytest.mark.parametrize("alpha", ALPHAS)
def test_sets_and_summaries_agree(alpha: float) -> None:
    for index, (p, y) in enumerate(_cases(12, 200)):
        scores = conformal.nonconformity_scores(p, y)
        quantile = conformal.conformal_quantile(scores, alpha)
        rng = random.Random(index)
        grid = [round(rng.random(), 2) for _ in range(40)] + [
            rng.random() for _ in range(40)
        ]
        labels = [rng.randint(0, 1) for _ in grid]
        ours = conformal.prediction_sets(grid, quantile)
        theirs = [reference.prediction_set(value, quantile) for value in grid]
        assert ours == theirs
        assert conformal.conformal_summary(ours, labels) == reference.conformal_summary(
            theirs, labels
        )
        assert conformal.empirical_coverage(
            ours, labels
        ) == reference.empirical_coverage(theirs, labels)


def test_decimal_grid_boundaries_agree() -> None:
    values = [k / 100 for k in range(101)]
    for quantile in values:
        for p in values:
            assert conformal.prediction_set(p, quantile) == reference.prediction_set(
                p, quantile
            )

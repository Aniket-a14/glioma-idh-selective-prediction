"""T10.8: Codex's DeLong against Claude's midrank reference (Sun and Xu 2014).

Codex implemented the contract's pairwise placement values; Claude wrote the midrank
algorithm. Two different algorithms, written without seeing each other.
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from tests.reference.delong_reference import delong_reference

from glioma_selective.statistics.delong import delong_paired_auroc

FIXTURES = json.loads(
    (
        Path(__file__).resolve().parents[1] / "fixtures" / "phase10_stats.json"
    ).read_text()
)["delong"]


@pytest.mark.parametrize("case", FIXTURES, ids=lambda c: c["name"])
def test_reference_matches_the_exact_fixtures(case: dict[str, object]) -> None:
    result = delong_reference(case["scores_a"], case["scores_b"], case["labels"])
    assert result["auc_a"] == pytest.approx(
        float(Fraction(str(case["auc_a"]))), abs=1e-12
    )
    assert result["auc_b"] == pytest.approx(
        float(Fraction(str(case["auc_b"]))), abs=1e-12
    )
    assert result["variance"] == pytest.approx(
        float(Fraction(str(case["variance"]))), abs=1e-12
    )
    assert result["p_value"] == pytest.approx(float(str(case["p_value"])), abs=1e-9)


def test_two_implementations_agree_on_random_data_with_and_without_ties() -> None:
    rng = np.random.default_rng(12345)
    for trial in range(300):
        n = int(rng.integers(8, 60))
        m = int(rng.integers(2, n - 1))
        labels = np.zeros(n, dtype=int)
        labels[rng.choice(n, m, replace=False)] = 1
        base = rng.normal(size=n) + labels * rng.uniform(0, 2)
        a = np.round(base, 1) if trial % 2 else base
        b = (
            np.round(base + rng.normal(size=n), 1)
            if trial % 3
            else base + rng.normal(size=n)
        )
        reference = delong_reference(a, b, labels)
        result = delong_paired_auroc(a, b, labels)
        assert result.auc_a == pytest.approx(reference["auc_a"], abs=1e-12)
        assert result.auc_b == pytest.approx(reference["auc_b"], abs=1e-12)
        assert result.variance == pytest.approx(reference["variance"], abs=1e-12)
        assert result.p_value == pytest.approx(reference["p_value"], abs=1e-9)
        if math.isfinite(reference["z"]) and math.isfinite(result.z):
            assert result.z == pytest.approx(reference["z"], abs=1e-9)

from __future__ import annotations

import math

import numpy as np
import scripts.power_check_phase05 as pc


def test_auroc_rows_matches_hand_count() -> None:
    y = np.array([[0, 0, 1, 1]])
    s = np.array([[0.1, 0.4, 0.35, 0.8]])
    # positives .35 and .8 vs negatives .1 and .4: three of four pairs ordered correctly
    assert pc.auroc_rows(y, s)[0] == 0.75


def test_auroc_rows_ties_count_half_and_single_class_is_nan() -> None:
    assert pc.auroc_rows(np.array([[0, 1]]), np.array([[0.5, 0.5]]))[0] == 0.5
    assert math.isnan(
        pc.auroc_rows(np.array([[1, 1, 1]]), np.array([[0.1, 0.2, 0.3]]))[0]
    )


def test_selective_risk_rows_matches_hand_values() -> None:
    err = np.array([[1.0, 0.0, 0.0, 1.0]])
    conf = np.array([[0.9, 0.8, 0.7, 0.6]])
    out = pc.selective_risk_rows(err, conf, (1.0, 0.75, 0.5))[0]
    # top 4: 2 errors of 4; top 3: 1 of 3; top 2: 1 of 2
    assert out.tolist() == [0.5, 1 / 3, 0.5]


def test_split_conformal_coverage_mean_is_exact_rank_ratio() -> None:
    # n=9, alpha=0.1: l = floor(10 * 0.1) = 1, mean coverage (9 + 1 - 1) / (9 + 1) = 0.9
    assert math.isclose(pc.split_conformal_coverage(9, 0.1)["mean"], 0.9)
    # 100 * 0.29 is 28.999999999999996 in floats; the exact product is 29
    assert math.isclose(pc.split_conformal_coverage(99, 0.29)["mean"], 71 / 100)


def test_one_config_is_deterministic_for_a_seed() -> None:
    def run() -> dict[str, object]:
        return pc.one_config(
            np.random.default_rng(7), 10, 20, 0.85, 1 / 3, reps=3, boot=50
        )

    assert run() == run()


def test_binomial_half_width_matches_formula() -> None:
    assert math.isclose(pc.binomial_half_width(450, 0.9), 1.96 * math.sqrt(0.09 / 450))

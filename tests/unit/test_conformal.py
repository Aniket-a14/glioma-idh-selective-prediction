"""K1 to K4 of the Phase 07 contract against the hand-calculated fixtures."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.calibration.conformal import (
    conformal_quantile,
    conformal_summary,
    empirical_coverage,
    nonconformity_score,
    nonconformity_scores,
    prediction_set,
    prediction_sets,
)
from glioma_selective.calibration.crc import accept, confidence, crc_threshold

FIXTURES = json.loads(
    (Path(__file__).parents[1] / "fixtures" / "phase07_contracts.json").read_text(
        encoding="utf-8"
    )
)


def _value(raw: object) -> float:
    return math.inf if raw == "inf" else float(raw)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "case", FIXTURES["conformal_quantile"], ids=lambda c: c["name"]
)
def test_quantile_fixtures(case: dict[str, object]) -> None:
    result = conformal_quantile(case["scores"], case["alpha"])  # type: ignore[arg-type]
    assert result == _value(case["expected"])


@pytest.mark.parametrize("case", FIXTURES["quantile_errors"], ids=lambda c: c["name"])
def test_quantile_errors(case: dict[str, object]) -> None:
    scores = [float(s) for s in case["scores"]]  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        conformal_quantile(scores, case["alpha"])  # type: ignore[arg-type]


def test_quantile_is_member_of_scores_or_inf() -> None:
    rng = np.random.default_rng(0)
    for n in (1, 2, 7, 19, 50):
        scores = rng.random(n).tolist()
        for alpha in (0.05, 0.1, 0.2):
            result = conformal_quantile(scores, alpha)
            assert result == math.inf or result in scores


def test_nonconformity_fixtures() -> None:
    for case in FIXTURES["nonconformity_score"]:
        assert nonconformity_score(case["p_hat"], case["label"]) == pytest.approx(
            case["expected"], abs=1e-15
        )


def test_nonconformity_rejects_bad_inputs() -> None:
    for p, y in [(1.2, 1), (-0.1, 0), (float("nan"), 1), (0.5, 2)]:
        with pytest.raises(ValueError):
            nonconformity_score(p, y)
    with pytest.raises(ValueError):
        nonconformity_scores([0.5, 0.5], [1])


def test_end_to_end_fixture() -> None:
    case = FIXTURES["conformal_end_to_end"]
    scores = nonconformity_scores(case["cal_p_hat"], case["cal_labels"])
    assert sorted(scores) == case["cal_scores_sorted"]
    for sub in case["cases"]:
        quantile = conformal_quantile(scores, sub["alpha"])
        assert quantile == _value(sub["q"])
        sets = prediction_sets(case["test_p_hat"], quantile)
        assert [list(s) for s in sets] == sub["sets"]
        summary = conformal_summary(sets, case["test_labels"])
        for key in ("coverage", "abstention_rate", "empty_rate", "full_rate"):
            assert summary[key] == pytest.approx(sub[key], abs=1e-12)


def test_decimal_boundary_stays_in_the_set() -> None:
    # 1 - 0.7 is 0.30000000000000004 in floating point but exactly 0.3 as a decimal.
    assert 1 - 0.7 > 0.3
    assert prediction_set(0.7, 0.3) == (1,)


def test_full_set_fixture() -> None:
    case = FIXTURES["conformal_both_labels_in_set"]
    scores = case["cal_scores"]
    assert conformal_quantile(scores, case["alpha"]) == case["q"]
    sets = prediction_sets(case["test_p_hat"], case["q"])
    assert [list(s) for s in sets] == case["sets"]
    summary = conformal_summary(sets, case["test_labels"])
    assert summary["coverage"] == case["coverage"]
    assert summary["abstention_rate"] == case["abstention_rate"]
    assert summary["full_rate"] == case["full_rate"]


def test_calibration_points_sit_inside_their_own_set() -> None:
    rng = np.random.default_rng(1)
    p = rng.random(300)
    y = (rng.random(300) < p).astype(int)
    scores = nonconformity_scores(p.tolist(), y.tolist())
    quantile = conformal_quantile(scores, 0.1)
    sets = prediction_sets(p.tolist(), quantile)
    covered = empirical_coverage(sets, y.tolist())
    assert covered >= 0.9
    assert all(
        int(label) in s
        for s, label, sc in zip(sets, y, scores, strict=True)
        if sc <= quantile
    )


def test_marginal_coverage_holds_over_exchangeable_draws() -> None:
    rng = np.random.default_rng(2)
    n_cal, n_test, trials = 99, 200, 200
    hits = []
    for _ in range(trials):
        p = rng.random(n_cal + n_test)
        y = (rng.random(n_cal + n_test) < p).astype(int)
        scores = nonconformity_scores(p[:n_cal].tolist(), y[:n_cal].tolist())
        quantile = conformal_quantile(scores, 0.1)
        sets = prediction_sets(p[n_cal:].tolist(), quantile)
        hits.append(empirical_coverage(sets, y[n_cal:].tolist()))
    assert float(np.mean(hits)) >= 0.9 - 0.01


def test_summary_rejects_mismatch() -> None:
    with pytest.raises(ValueError):
        empirical_coverage([(1,)], [1, 0])
    with pytest.raises(ValueError):
        empirical_coverage([], [])


def test_prediction_set_shapes() -> None:
    assert prediction_set(0.5, 0.0) == ()
    assert prediction_set(0.5, 0.5) == (0, 1)
    assert prediction_set(0.5, math.inf) == (0, 1)
    assert prediction_set(0.0, 0.0) == (0,)
    assert prediction_set(1.0, 0.0) == (1,)
    with pytest.raises(ValueError):
        prediction_set(0.5, float("nan"))


def test_crc_fixtures() -> None:
    case = FIXTURES["crc"]
    assert [confidence(p) for p in case["p_hat"]] == case["confidence"]
    for sub in case["cases"]:
        tau = crc_threshold(case["p_hat"], case["labels"], sub["alpha"])
        assert tau == _value(sub["tau_hat"])
        accepted = sum(accept(p, tau) for p in case["p_hat"])
        assert accepted == sub["n_accepted"]


def test_crc_threshold_is_monotone_in_alpha() -> None:
    rng = np.random.default_rng(3)
    p = rng.random(200)
    y = (rng.random(200) < p).astype(int)
    taus = [crc_threshold(p.tolist(), y.tolist(), a) for a in (0.05, 0.1, 0.2, 0.4)]
    assert all(later <= earlier for earlier, later in zip(taus, taus[1:], strict=False))


def test_crc_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        crc_threshold([], [], 0.1)
    with pytest.raises(ValueError):
        crc_threshold([0.5], [1, 0], 0.1)
    with pytest.raises(ValueError):
        crc_threshold([0.5], [1], 1.0)
    with pytest.raises(ValueError):
        crc_threshold([0.5], [3], 0.1)

"""RQ4 probe (D-007): fitting, scoring, descriptive analysis and feature extraction."""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch

from glioma_selective.evaluation.probe_1p19q import (
    analyze_probe,
    class_counts,
    extract_features,
    fit_logistic_probe,
    hanley_mcneil_half_width,
    probe_scores,
)
from glioma_selective.models.segresnet import IDHNet, ModelConfig


def _data(n: int, seed: int, signal: float) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    y = np.array([0, 1] * (n // 2))
    x = rng.normal(size=(n, 6))
    x[:, 0] += signal * (2 * y - 1)
    return x, y


def _newton_solution(x: np.ndarray, y: np.ndarray, c: float) -> np.ndarray:
    """Independent numpy Newton solve of the same objective (weights then bias)."""
    mean, scale = x.mean(axis=0), x.std(axis=0)
    z = np.hstack([(x - mean) / scale, np.ones((len(y), 1))])
    n, n1 = len(y), int(y.sum())
    w = np.where(y == 1, n / (2 * n1), n / (2 * (n - n1)))
    reg = np.eye(z.shape[1])
    reg[-1, -1] = 0.0
    theta = np.zeros(z.shape[1])
    for _ in range(100):
        p = 1 / (1 + np.exp(-(z @ theta)))
        grad = reg @ theta + c * z.T @ (w * (p - y))
        hess = reg + c * (z.T * (w * p * (1 - p))) @ z
        step = np.linalg.solve(hess, grad)
        theta -= step
        if np.abs(step).max() < 1e-12:
            break
    return theta


def test_fit_matches_an_independent_newton_solve() -> None:
    x, y = _data(80, 0, 1.0)
    fit = fit_logistic_probe(x, y)
    theta = _newton_solution(x, y, 1.0)
    assert fit.converged
    np.testing.assert_allclose(fit.weights, theta[:-1], atol=1e-6)
    assert fit.bias == pytest.approx(theta[-1], abs=1e-6)


def test_standardization_uses_only_the_train_features() -> None:
    x, y = _data(60, 1, 1.0)
    fit = fit_logistic_probe(x, y)
    np.testing.assert_allclose(fit.mean, x.mean(axis=0))
    np.testing.assert_allclose(fit.scale, x.std(axis=0))
    test = x[:5] + 100.0
    np.testing.assert_allclose(
        probe_scores(fit, test),
        ((test - fit.mean) / fit.scale) @ fit.weights + fit.bias,
    )


def test_separable_signal_scores_high_and_noise_scores_near_chance() -> None:
    train_x, train_y = _data(200, 2, 3.0)
    test_x, test_y = _data(100, 3, 3.0)
    strong = analyze_probe(
        train_x,
        train_y,
        test_x,
        test_y,
        np.zeros(100),
        np.ones(100, dtype=int),
        iterations=200,
    )
    assert strong["internal_test"]["probe"]["auroc"] > 0.95
    train_x, train_y = _data(200, 4, 0.0)
    test_x, test_y = _data(400, 5, 0.0)
    weak = analyze_probe(
        train_x,
        train_y,
        test_x,
        test_y,
        np.zeros(400),
        np.ones(400, dtype=int),
        iterations=200,
    )
    assert 0.35 < weak["internal_test"]["probe"]["auroc"] < 0.65


def test_report_is_labelled_exploratory_and_carries_class_counts() -> None:
    train_x, train_y = _data(60, 6, 1.0)
    test_x, test_y = _data(30, 7, 1.0)
    idh_logit = np.linspace(-1, 1, 30)
    idh = np.array([1] * 20 + [0] * 10)
    report = analyze_probe(
        train_x, train_y, test_x, test_y, idh_logit, idh, iterations=100
    )
    assert "no inferential claim" in report["label"]
    assert report["train"] == {"n": 60, "n_codeleted": 30}
    assert report["internal_test"]["probe"]["n"] == 30
    assert report["internal_test"]["probe"]["n_codeleted"] == int(test_y.sum())
    subgroup = report["internal_test"]["idh_mutant_only"]["probe"]
    assert subgroup["n"] == 20
    assert "comparator_idh_probability" in report["internal_test"]


def test_single_class_subgroup_reports_no_auroc_instead_of_failing() -> None:
    train_x, train_y = _data(60, 8, 1.0)
    test_x = train_x[:10]
    test_y = np.zeros(10, dtype=int)
    test_y[0] = 1
    idh = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    report = analyze_probe(
        train_x, train_y, test_x, test_y, np.zeros(10), idh, iterations=50
    )
    assert report["internal_test"]["idh_mutant_only"]["probe"]["auroc"] is None
    assert report["internal_test"]["probe_bootstrap"]["skipped_single_class"] >= 0


def test_hanley_mcneil_hand_value() -> None:
    # q1 = 2/3, q2 = 32/45; var = (0.16 + 49 (q1 - 0.64) + 49 (q2 - 0.64)) / 2500
    q1, q2 = 0.8 / 1.2, 2 * 0.64 / 1.8
    variance = (0.16 + 49 * (q1 - 0.64) + 49 * (q2 - 0.64)) / 2500
    assert hanley_mcneil_half_width(0.8, 50, 50) == pytest.approx(
        1.96 * math.sqrt(variance)
    )
    assert hanley_mcneil_half_width(0.8, 50, 50) == pytest.approx(0.0872, abs=5e-4)


def test_fit_rejects_bad_input() -> None:
    x, y = _data(20, 9, 1.0)
    with pytest.raises(ValueError, match="both classes"):
        fit_logistic_probe(x, np.zeros(20, dtype=int))
    with pytest.raises(ValueError, match="equal N"):
        fit_logistic_probe(x, y[:-1])
    bad = x.copy()
    bad[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        fit_logistic_probe(bad, y)
    with pytest.raises(ValueError, match="c must be positive"):
        fit_logistic_probe(x, y, c=0.0)


def test_class_counts() -> None:
    assert class_counts([1, 0, 0, 1, 0]) == {"codeleted": 2, "non_codeleted": 3}


class _Dataset:
    def __init__(self) -> None:
        generator = torch.Generator().manual_seed(0)
        self.images = torch.randn(4, 4, 16, 16, 16, generator=generator)

    def __len__(self) -> int:
        return 4

    def __getitem__(self, index: int) -> dict[str, object]:
        return {
            "image": self.images[index],
            "patient_id": f"P{index}",
            "label": torch.tensor(float(index % 2)),
        }


def test_extract_features_matches_the_model_forward() -> None:
    torch.manual_seed(0)
    model = IDHNet(ModelConfig(init_filters=8, head_hidden=8, head_dropout=0.0))
    data = _Dataset()
    out = extract_features(model, data, device="cpu", batch_size=2)
    assert out["patient_ids"] == ["P0", "P1", "P2", "P3"]
    assert out["features"].shape == (4, 64)
    assert out["idh_label"].tolist() == [0, 1, 0, 1]
    model.eval()
    with torch.no_grad():
        expected = model(data.images).logit.numpy()
    np.testing.assert_allclose(out["idh_logit"], expected, atol=1e-5)
    assert not any(p.grad is not None for p in model.parameters())

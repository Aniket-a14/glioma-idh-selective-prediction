"""Tests for binary temperature scaling."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.calibration.temperature import (
    _mean_binary_cross_entropy,
    apply_temperature,
    fit_temperature,
)

FIXTURES = json.loads(
    Path(__file__)
    .parents[1]
    .joinpath("fixtures", "phase07_contracts.json")
    .read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", FIXTURES["temperature"], ids=lambda case: case["name"])
def test_temperature_hand_calculated_fixtures(case: dict[str, object]) -> None:
    result = fit_temperature(case["logits"], case["labels"])
    assert result == pytest.approx(case["expected_T"], abs=1e-6)
    assert 0.05 <= result <= 20.0


@pytest.mark.parametrize("case", FIXTURES["apply_temperature"])
def test_apply_temperature_fixtures(case: dict[str, object]) -> None:
    result = apply_temperature(case["logits"], case["T"])
    np.testing.assert_allclose(result, case["expected"], rtol=0.0, atol=1e-15)


def test_temperature_one_preserves_probabilities_and_fit_reduces_nll() -> None:
    logits = np.array([2.0, 1.0, -0.5, -1.5])
    labels = np.array([1, 0, 1, 0])
    np.testing.assert_allclose(
        apply_temperature(logits, 1.0), 1.0 / (1.0 + np.exp(-logits))
    )

    temperature = fit_temperature(logits, labels)
    before = _mean_binary_cross_entropy(logits, labels)
    scaled_logits = logits / temperature
    after = _mean_binary_cross_entropy(scaled_logits, labels)
    assert after < before


def test_log_loss_stays_finite_for_extreme_logits() -> None:
    assert _mean_binary_cross_entropy(np.array([1000.0]), np.array([0])) == 1000.0
    assert _mean_binary_cross_entropy(np.array([-1000.0]), np.array([1])) == 1000.0


@pytest.mark.parametrize(
    ("logits", "labels"),
    [([], []), ([1.0], []), ([float("nan")], [0]), ([[1.0]], [0]), ([1.0], [2])],
)
def test_fit_temperature_rejects_invalid_inputs(logits: object, labels: object) -> None:
    with pytest.raises(ValueError):
        fit_temperature(logits, labels)  # type: ignore[arg-type]


@pytest.mark.parametrize("temperature", [0.0, -1.0, float("inf"), float("nan")])
def test_apply_temperature_rejects_invalid_temperature(temperature: float) -> None:
    with pytest.raises(ValueError):
        apply_temperature([1.0], temperature)


@pytest.mark.parametrize("logits", [[], [float("inf")], [[1.0]]])
def test_apply_temperature_rejects_invalid_logits(logits: object) -> None:
    with pytest.raises(ValueError):
        apply_temperature(logits, 1.0)  # type: ignore[arg-type]

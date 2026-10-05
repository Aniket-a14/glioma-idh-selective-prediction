"""Binary temperature scaling for calibration-split logits."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from numpy.typing import NDArray

_MIN_TEMPERATURE = 0.05
_MAX_TEMPERATURE = 20.0
_W_TOLERANCE = 1e-8


def _validated_inputs(
    logits: Sequence[float] | NDArray[np.floating],
    labels: Sequence[int] | NDArray[np.integer],
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    try:
        values = np.asarray(logits, dtype=np.float64)
        targets_raw = np.asarray(labels)
    except (TypeError, ValueError) as error:
        raise ValueError(
            "logits and labels must be numeric one-dimensional inputs"
        ) from error
    if values.ndim != 1 or targets_raw.ndim != 1:
        raise ValueError("logits and labels must be one-dimensional")
    if values.size == 0:
        raise ValueError("inputs must not be empty")
    if values.size != targets_raw.size:
        raise ValueError("logits and labels must have equal lengths")
    if not np.all(np.isfinite(values)):
        raise ValueError("logits must be finite")
    if not np.all(np.isin(targets_raw, (0, 1))):
        raise ValueError("labels must be 0 or 1")
    return values, targets_raw.astype(np.int64, copy=False)


def _sigmoid(values: NDArray[np.float64]) -> NDArray[np.float64]:
    exponentials = np.exp(-np.abs(values))
    return np.where(
        values >= 0, 1.0 / (1.0 + exponentials), exponentials / (1.0 + exponentials)
    )


def _mean_binary_cross_entropy(
    scaled_logits: NDArray[np.float64], targets: NDArray[np.int64]
) -> float:
    """Evaluate mean binary cross-entropy without taking probabilities' logs."""
    return float(np.mean(np.logaddexp(0.0, scaled_logits) - targets * scaled_logits))


def fit_temperature(
    logits: Sequence[float] | NDArray[np.floating],
    labels: Sequence[int] | NDArray[np.integer],
) -> float:
    """Minimize mean binary cross-entropy over ``T`` in ``[0.05, 20]``.

    Bisection solves the monotone derivative in ``w = 1 / T``. If the
    constrained optimum is at a boundary, that boundary temperature is used.
    """
    values, targets = _validated_inputs(logits, labels)
    lower_w = 1.0 / _MAX_TEMPERATURE
    upper_w = 1.0 / _MIN_TEMPERATURE

    def gradient(w: float) -> float:
        scaled = w * values
        return float(np.mean(values * (_sigmoid(scaled) - targets)))

    lower_gradient = gradient(lower_w)
    upper_gradient = gradient(upper_w)
    if lower_gradient >= 0.0:
        return _MAX_TEMPERATURE
    if upper_gradient <= 0.0:
        return _MIN_TEMPERATURE

    while upper_w - lower_w > _W_TOLERANCE:
        midpoint = (lower_w + upper_w) / 2.0
        if gradient(midpoint) > 0.0:
            upper_w = midpoint
        else:
            lower_w = midpoint
    return 1.0 / ((lower_w + upper_w) / 2.0)


def apply_temperature(
    logits: Sequence[float] | NDArray[np.floating], temperature: float
) -> NDArray[np.float64]:
    """Return ``sigmoid(logits / temperature)`` after input validation."""
    try:
        temperature_value = float(temperature)
    except (TypeError, ValueError) as error:
        raise ValueError("temperature must be a positive finite scalar") from error
    if not np.isfinite(temperature_value) or temperature_value <= 0.0:
        raise ValueError("temperature must be a positive finite scalar")
    try:
        values = np.asarray(logits, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise ValueError("logits must be numeric") from error
    if values.ndim != 1 or values.size == 0:
        raise ValueError("logits must be a non-empty one-dimensional input")
    if not np.all(np.isfinite(values)):
        raise ValueError("logits must be finite")
    return _sigmoid(values / temperature_value)

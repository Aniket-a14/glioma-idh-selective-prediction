"""Brier score and positive-class expected calibration error."""

from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
from typing import TypedDict

import numpy as np
from numpy.typing import NDArray


class ReliabilityBin(TypedDict):
    """Summary for one equal-width probability bin."""

    count: int
    mean_p: float | None
    frac_pos: float | None


def _validated_inputs(
    p_hat: Sequence[float] | NDArray[np.floating],
    labels: Sequence[int] | NDArray[np.integer],
) -> tuple[NDArray[np.float64], NDArray[np.int64]]:
    try:
        probabilities = np.asarray(p_hat, dtype=np.float64)
        labels_raw = np.asarray(labels)
    except (TypeError, ValueError) as error:
        raise ValueError("probabilities and labels must be numeric") from error
    if probabilities.ndim != 1 or labels_raw.ndim != 1:
        raise ValueError("probabilities and labels must be one-dimensional")
    if probabilities.size == 0:
        raise ValueError("inputs must not be empty")
    if probabilities.size != labels_raw.size:
        raise ValueError("probabilities and labels must have equal lengths")
    if not np.all(np.isfinite(probabilities)) or np.any(
        (probabilities < 0.0) | (probabilities > 1.0)
    ):
        raise ValueError("probabilities must be finite and in [0, 1]")
    if not np.all(np.isin(labels_raw, (0, 1))):
        raise ValueError("labels must be 0 or 1")
    return probabilities, labels_raw.astype(np.int64, copy=False)


def _validated_n_bins(n_bins: int) -> int:
    if isinstance(n_bins, bool) or not isinstance(n_bins, int) or n_bins < 1:
        raise ValueError("n_bins must be a positive integer")
    return n_bins


def _bin_index(probability: float, n_bins: int) -> int:
    """Compute floor(n_bins * p) from the decimal spelling exactly."""
    scaled = Fraction(repr(float(probability))) * n_bins
    return min(scaled.numerator // scaled.denominator, n_bins - 1)


def brier_score(
    p_hat: Sequence[float] | NDArray[np.floating],
    labels: Sequence[int] | NDArray[np.integer],
) -> float:
    """Return ``mean((p_hat - labels) ** 2)`` for the positive class."""
    probabilities, targets = _validated_inputs(p_hat, labels)
    return float(np.mean(np.square(probabilities - targets)))


def reliability_bins(
    p_hat: Sequence[float] | NDArray[np.floating],
    labels: Sequence[int] | NDArray[np.integer],
    n_bins: int = 10,
) -> list[ReliabilityBin]:
    """Return every equal-width bin, including empty bins with ``None`` means."""
    probabilities, targets = _validated_inputs(p_hat, labels)
    count_bins = _validated_n_bins(n_bins)
    indices = [
        _bin_index(float(probability), count_bins) for probability in probabilities
    ]
    result: list[ReliabilityBin] = []
    for index in range(count_bins):
        members = [position for position, value in enumerate(indices) if value == index]
        if not members:
            result.append({"count": 0, "mean_p": None, "frac_pos": None})
            continue
        result.append(
            {
                "count": len(members),
                "mean_p": float(np.mean(probabilities[members])),
                "frac_pos": float(np.mean(targets[members])),
            }
        )
    return result


def expected_calibration_error(
    p_hat: Sequence[float] | NDArray[np.floating],
    labels: Sequence[int] | NDArray[np.integer],
    n_bins: int = 10,
) -> float:
    """Return count-weighted positive-class ECE over equal-width bins."""
    probabilities, _ = _validated_inputs(p_hat, labels)
    bins = reliability_bins(probabilities, labels, n_bins)
    total = len(probabilities)
    return float(
        sum(
            (entry["count"] / total) * abs(entry["frac_pos"] - entry["mean_p"])
            for entry in bins
            if entry["count"] > 0
            and entry["frac_pos"] is not None
            and entry["mean_p"] is not None
        )
    )

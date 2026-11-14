"""Phase 10 S5: surface HD95 in mm and both frozen empty-mask conventions."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.ndimage import (  # type: ignore[import-untyped]
    binary_erosion,
    distance_transform_edt,
    generate_binary_structure,
)


def surface_voxels(mask: NDArray[np.bool_]) -> NDArray[np.bool_]:
    """Foreground with a background face neighbour; outside counts as background."""
    if mask.ndim != 3 or mask.dtype != np.bool_:
        raise ValueError("mask must be a 3-D boolean array")
    eroded = binary_erosion(
        mask, structure=generate_binary_structure(3, 1), border_value=0
    )
    return np.asarray(mask & ~eroded, dtype=np.bool_)


def classify_case(pred: NDArray[np.bool_], truth: NDArray[np.bool_]) -> str:
    """Classify a patient-channel by presence of predicted and true foreground."""
    if pred.any():
        return "evaluable" if truth.any() else "false"
    return "missed" if truth.any() else "both_empty"


def hd95(
    pred: NDArray[np.bool_],
    truth: NDArray[np.bool_],
    spacing: Sequence[float] = (2.0, 2.0, 2.0),
) -> float | None:
    """Max of directed surface-distance linear 95th percentiles, or undefined.

    Each directed distance is the nearest surface-voxel distance in mm, computed
    with a Euclidean distance transform sampled at the supplied axis spacings.
    Either empty foreground makes HD95 undefined, including two empty masks.
    """
    if pred.shape != truth.shape:
        raise ValueError("pred and truth must have the same shape")
    a, b = surface_voxels(pred), surface_voxels(truth)
    if classify_case(pred, truth) != "evaluable":
        return None
    a_to_b = distance_transform_edt(~b, sampling=spacing)[a]
    b_to_a = distance_transform_edt(~a, sampling=spacing)[b]
    return float(
        max(
            np.percentile(a_to_b, 95, method="linear"),
            np.percentile(b_to_a, 95, method="linear"),
        )
    )


def grid_diagonal_penalty(shape: Sequence[int], spacing: Sequence[float]) -> float:
    """Return sqrt(sum((n_i * s_i)**2)), using grid extent, not centre distance."""
    return float(
        np.sqrt(sum((n * s) ** 2 for n, s in zip(shape, spacing, strict=True)))
    )


def _statistics(values: list[float]) -> dict[str, float | None]:
    if not values:
        return dict.fromkeys(("mean", "median", "q25", "q75"))
    q25, median, q75 = np.percentile(values, [25, 50, 75], method="linear")
    return {
        "mean": float(np.mean(values)),
        "median": float(median),
        "q25": float(q25),
        "q75": float(q75),
    }


def summarize_hd95(
    outcomes: list[tuple[str, float | None]], penalty: float
) -> dict[str, Any]:
    """Report evaluable-only HD95 and the labelled arbitrary BraTS-style penalty.

    Primary distances exclude all empty-mask cases. The second table includes
    every patient: both-empty contributes zero, missed/false contributes penalty.
    Counts alongside the tables preserve the undefined primary cases.
    """
    evaluable: list[float] = []
    penalized: list[float] = []
    counts = dict.fromkeys(("missed", "false", "both_empty"), 0)
    for case, value in outcomes:
        if case == "evaluable":
            if value is None or not np.isfinite(value) or value < 0:
                raise ValueError("evaluable HD95 must be finite and non-negative")
            evaluable.append(value)
            penalized.append(value)
        else:
            if case not in counts or value is not None:
                raise ValueError("non-evaluable HD95 requires a known case and None")
            counts[case] += 1
            penalized.append(0.0 if case == "both_empty" else penalty)
    return {
        "primary": {"n_evaluable": len(evaluable), **_statistics(evaluable)},
        **counts,
        "n_patients": len(outcomes),
        "brats_penalty": {
            "n": len(outcomes),
            **_statistics(penalized),
            "penalty": penalty,
            "label": (
                "BraTS-style penalty convention; the penalty is an arbitrary constant"
            ),
        },
    }

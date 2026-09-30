"""Report brain-voxel z-score ranges against the UTSW training cohort."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from glioma_selective.data.adapters._common import CanonicalSequence
from glioma_selective.preprocessing.normalize import (
    NormalizationStats,
    normalize_volume,
)

__all__ = ["ZSummary", "flag_summary", "reference_ranges", "summarize_volume"]

_REFERENCE_QUANTITIES = ("mean", "std", "p99_9")


@dataclass(frozen=True)
class ZSummary:
    """Summary statistics for one modality's non-zero (brain) z-scores."""

    n: int
    mean: float
    std: float
    minimum: float
    maximum: float
    p0_1: float
    p99_9: float
    finite: bool


def summarize_volume(
    volume: np.ndarray,
    sequence: CanonicalSequence | str,
    stats: NormalizationStats,
) -> ZSummary:
    """Normalize with frozen statistics and summarize non-zero brain voxels."""

    brain_mask = np.asarray(volume) != 0
    if not np.any(brain_mask):
        raise ValueError("volume has no non-zero brain voxels")
    zscores = normalize_volume(volume, sequence, stats)
    brain = np.asarray(zscores[brain_mask], dtype=np.float64)
    return ZSummary(
        n=int(brain.size),
        mean=float(np.mean(brain, dtype=np.float64)),
        std=float(np.std(brain, dtype=np.float64, ddof=0)),
        minimum=float(np.min(brain)),
        maximum=float(np.max(brain)),
        p0_1=float(np.percentile(brain, 0.1)),
        p99_9=float(np.percentile(brain, 99.9)),
        finite=bool(np.all(np.isfinite(brain))),
    )


def reference_ranges(
    train_summaries: Mapping[str, Mapping[str, ZSummary]],
) -> dict[str, dict[str, tuple[float, float]]]:
    """Return per-modality min/max reference ranges from UTSW train patients."""

    if not train_summaries:
        raise ValueError("UTSW train summaries are empty")
    modalities = set(next(iter(train_summaries.values())))
    if not modalities:
        raise ValueError("UTSW train summaries contain no modalities")
    for patient_summaries in train_summaries.values():
        if set(patient_summaries) != modalities:
            raise ValueError("UTSW train summaries have inconsistent modalities")

    ranges: dict[str, dict[str, tuple[float, float]]] = {}
    for modality in sorted(modalities):
        modality_summaries = [
            patient_summaries[modality]
            for patient_summaries in train_summaries.values()
        ]
        ranges[modality] = {
            quantity: (
                min(getattr(summary, quantity) for summary in modality_summaries),
                max(getattr(summary, quantity) for summary in modality_summaries),
            )
            for quantity in _REFERENCE_QUANTITIES
        }
    return ranges


def flag_summary(
    summary: ZSummary,
    reference: Mapping[str, tuple[float, float]],
) -> list[str]:
    """List out-of-reference quantities; flags prompt review and never exclude."""

    flags = [
        quantity
        for quantity in _REFERENCE_QUANTITIES
        if getattr(summary, quantity) < reference[quantity][0]
        or getattr(summary, quantity) > reference[quantity][1]
    ]
    if not summary.finite:
        flags.append("non_finite")
    return flags

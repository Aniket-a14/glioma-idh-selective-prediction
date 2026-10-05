"""Modality dropout: zero whole input channels during training (SPEC §4.4, D-041).

A dropped modality is zeroed, never imputed. The schedule is fixed for every epoch:
with probability ``keep_all_probability`` a patient keeps all four sequences,
otherwise one of the 14 non-empty proper subsets of sequences is kept, chosen
uniformly, and the other channels are zeroed. At least one sequence always stays.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import torch

__all__ = ["KEPT_SUBSETS", "apply_modality_dropout", "sample_dropped_channels"]

_CHANNELS = (0, 1, 2, 3)  # T1, T1ce, T2, FLAIR
KEPT_SUBSETS: tuple[tuple[int, ...], ...] = tuple(
    subset for size in (1, 2, 3) for subset in combinations(_CHANNELS, size)
)


def sample_dropped_channels(
    rng: np.random.Generator, keep_all_probability: float
) -> tuple[int, ...]:
    """Channels to zero for one patient (empty when all four are kept)."""
    if not 0.0 <= keep_all_probability <= 1.0:
        raise ValueError("keep_all_probability must be in [0, 1]")
    if rng.random() < keep_all_probability:
        return ()
    kept = KEPT_SUBSETS[int(rng.integers(len(KEPT_SUBSETS)))]
    return tuple(channel for channel in _CHANNELS if channel not in kept)


def apply_modality_dropout(
    image: torch.Tensor, rng: np.random.Generator, keep_all_probability: float
) -> torch.Tensor:
    """Return a copy of ``[B, 4, ...]`` with each patient's dropped channels zeroed."""
    if image.ndim < 3 or image.shape[1] != len(_CHANNELS):
        raise ValueError("image must be [batch, 4, ...]")
    output = image.clone()
    for patient in range(output.shape[0]):
        for channel in sample_dropped_channels(rng, keep_all_probability):
            output[patient, channel].zero_()
    return output

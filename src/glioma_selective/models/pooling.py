"""Tumour-aware pooling of encoder features (SPEC §4.3, confirmatory component)."""

from __future__ import annotations

import torch
import torch.nn.functional as functional

__all__ = ["tumour_aware_pool"]


def tumour_aware_pool(
    features: torch.Tensor, tumour_probability: torch.Tensor, *, min_mass: float
) -> torch.Tensor:
    """Average features weighted by the tumour probability of each cell.

    ``features`` is ``[B, C, D, H, W]``; ``tumour_probability`` is ``[B, 1, d, h, w]``
    in ``[0, 1]`` on any grid, and is averaged down to the feature grid first, so
    each feature cell is weighted by the mean tumour probability it covers. For
    sample b the result is ``sum(w * f) / sum(w)``. When the total weight of a
    sample is below ``min_mass`` (in feature cells) the sample falls back to plain
    global average pooling, so an empty prediction never divides by ~0. An all-ones
    probability map therefore gives exactly global average pooling.
    """
    if features.ndim != 5 or tumour_probability.ndim != 5:
        raise ValueError("features and tumour_probability must be 5-dimensional")
    if tumour_probability.shape[1] != 1:
        raise ValueError("tumour_probability must have a single channel")
    grid = (features.shape[2], features.shape[3], features.shape[4])
    weights = functional.adaptive_avg_pool3d(tumour_probability, grid)
    mass = weights.sum(dim=(2, 3, 4), keepdim=True)
    weights = torch.where(mass < min_mass, torch.ones_like(weights), weights)
    mass = weights.sum(dim=(2, 3, 4))
    pooled: torch.Tensor = (features * weights).sum(dim=(2, 3, 4)) / mass
    return pooled

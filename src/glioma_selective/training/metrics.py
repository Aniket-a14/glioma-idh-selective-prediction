"""Small metrics used by the training loop: AUROC and hard Dice."""

from __future__ import annotations

import numpy as np
import torch
from scipy.stats import rankdata  # type: ignore[import-untyped]

__all__ = ["binary_auroc", "hard_dice"]


def binary_auroc(score: np.ndarray, label: np.ndarray) -> float:
    """Area under the ROC curve by the rank-sum identity; ties get average ranks.

    ``AUROC = (sum of positive ranks - n_pos (n_pos + 1) / 2) / (n_pos n_neg)``.
    Returns NaN when one class is absent.
    """
    positive = np.asarray(label) == 1
    n_positive = int(positive.sum())
    n_negative = int(positive.size - n_positive)
    if n_positive == 0 or n_negative == 0:
        return float("nan")
    ranks = rankdata(np.asarray(score, dtype=np.float64))
    rank_sum = float(ranks[positive].sum())
    return (rank_sum - n_positive * (n_positive + 1) / 2) / (n_positive * n_negative)


def hard_dice(
    seg_logits: torch.Tensor, target: torch.Tensor, has_seg: torch.Tensor
) -> torch.Tensor:
    """Dice of ``sigmoid(logit) > 0.5`` per channel, averaged over patients with a mask.

    A patient-channel where both the prediction and the target are empty scores 1.
    Returns a ``[channels]`` tensor, or NaNs when no patient has a segmentation.
    """
    channels = seg_logits.shape[1]
    if not bool(has_seg.any()):
        return torch.full((channels,), float("nan"))
    predicted = (torch.sigmoid(seg_logits[has_seg]) > 0.5).to(torch.float64)
    truth = (target[has_seg] > 0.5).to(torch.float64)
    dims = tuple(range(2, predicted.ndim))
    intersection = (predicted * truth).sum(dim=dims)
    total = predicted.sum(dim=dims) + truth.sum(dim=dims)
    dice = torch.where(
        total == 0, torch.ones_like(total), 2.0 * intersection / total.clamp_min(1.0)
    )
    return dice.mean(dim=0)

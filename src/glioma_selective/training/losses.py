"""Class-balanced classification loss and auxiliary soft-Dice loss (T06.4)."""

from __future__ import annotations

from typing import NamedTuple

import torch
import torch.nn.functional as functional

__all__ = [
    "JointLoss",
    "class_balanced_bce",
    "joint_loss",
    "pos_weight_from_counts",
    "soft_dice_loss",
]


class JointLoss(NamedTuple):
    """``total`` is optimised; ``classification`` and ``segmentation`` are for logs."""

    total: torch.Tensor
    classification: torch.Tensor
    segmentation: torch.Tensor


def pos_weight_from_counts(n_negative: int, n_positive: int) -> float:
    """Weight of the positive (IDH-mutant) class: negatives divided by positives."""
    if n_negative <= 0 or n_positive <= 0:
        raise ValueError("both classes need at least one patient to weight them")
    return n_negative / n_positive


def class_balanced_bce(
    logits: torch.Tensor, labels: torch.Tensor, *, pos_weight: float
) -> torch.Tensor:
    """Mean over the batch of ``-[pos_weight * y log p + (1 - y) log(1 - p)]``."""
    weight = torch.tensor(pos_weight, dtype=logits.dtype, device=logits.device)
    loss: torch.Tensor = functional.binary_cross_entropy_with_logits(
        logits, labels.to(logits.dtype), pos_weight=weight
    )
    return loss


def soft_dice_loss(
    seg_logits: torch.Tensor,
    target: torch.Tensor,
    has_seg: torch.Tensor,
    *,
    smooth: float,
) -> torch.Tensor:
    """One minus the mean soft Dice over channels, averaged over patients with a mask.

    Per patient and channel, ``dice = (2 * sum(p * t) + smooth) / (sum(p) + sum(t) +
    smooth)`` with ``p = sigmoid(logit)``. A patient with no segmentation
    (``has_seg`` False) contributes nothing; if no patient in the batch has one, the
    loss is a zero that still carries a gradient path.
    """
    if not bool(has_seg.any()):
        return seg_logits.sum() * 0.0
    probability = torch.sigmoid(seg_logits[has_seg])
    truth = target[has_seg].to(probability.dtype)
    dims = tuple(range(2, probability.ndim))
    intersection = (probability * truth).sum(dim=dims)
    denominator = probability.sum(dim=dims) + truth.sum(dim=dims)
    dice = (2.0 * intersection + smooth) / (denominator + smooth)
    loss: torch.Tensor = 1.0 - dice.mean()
    return loss


def joint_loss(
    logit: torch.Tensor,
    seg_logits: torch.Tensor | None,
    label: torch.Tensor,
    seg_target: torch.Tensor,
    has_seg: torch.Tensor,
    *,
    pos_weight: float,
    seg_weight: float,
    dice_smooth: float,
) -> JointLoss:
    """Classification loss plus ``seg_weight`` times the Dice loss (0 without aux)."""
    classification = class_balanced_bce(logit, label, pos_weight=pos_weight)
    if seg_logits is None:
        segmentation = torch.zeros_like(classification)
    else:
        segmentation = soft_dice_loss(
            seg_logits, seg_target, has_seg, smooth=dice_smooth
        )
    return JointLoss(
        total=classification + seg_weight * segmentation,
        classification=classification,
        segmentation=segmentation,
    )

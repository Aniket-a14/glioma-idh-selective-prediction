"""Score a fixed dataset in order for Phase 06 prediction freezing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

import numpy as np
import torch
from torch import nn

from glioma_selective.training.determinism import deterministic_mode
from glioma_selective.training.metrics import hard_dice

__all__ = ["predict_split", "predict_split_with_dice"]

_SEGMENTATION_CHANNELS = ("enhancing", "necrotic_core", "oedema")


def _scalar_logit(output: Any) -> torch.Tensor:
    logits = output.logit
    if not isinstance(logits, torch.Tensor):
        raise ValueError("model output logit must be a tensor")
    if logits.ndim == 1:
        return logits
    if logits.ndim == 2 and logits.shape[1] == 1:
        return logits[:, 0]
    raise ValueError("model output logit must have shape (B,) or (B, 1)")


def _predict_split(
    model: nn.Module,
    dataset: Sequence[Mapping[str, Any]] | Any,
    *,
    device: torch.device | str,
    batch_size: int,
    collect_dice: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Score one split, optionally aggregating auxiliary segmentation Dice."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    model.to(device)
    model.eval()
    results: list[dict[str, Any]] = []
    dice_sum: torch.Tensor | None = None
    n_with_segmentation = 0
    n_without_segmentation = 0
    with deterministic_mode(), torch.no_grad():
        for offset in range(0, len(dataset), batch_size):
            samples = [
                dataset[index]
                for index in range(offset, min(offset + batch_size, len(dataset)))
            ]
            image = torch.stack(
                [cast(torch.Tensor, sample["image"]) for sample in samples]
            ).to(device)
            if image.ndim != 5 or image.shape[1] != 4:
                raise ValueError("prediction dataset must provide four MRI sequences")
            output = model(image)
            batch_logits = (
                _scalar_logit(output).detach().to(device="cpu", dtype=torch.float32)
            )
            logit64 = batch_logits.to(torch.float64)
            probabilities = torch.sigmoid(logit64).to(torch.float32)
            labels = [
                int(cast(torch.Tensor, sample["label"]).item()) for sample in samples
            ]
            patient_ids = [cast(str, sample["patient_id"]) for sample in samples]
            for patient_id, label, logit, probability in zip(
                patient_ids,
                labels,
                batch_logits.tolist(),
                probabilities.tolist(),
                strict=True,
            ):
                results.append(
                    {
                        "patient_id": patient_id,
                        "logit": np.float32(logit),
                        "p_hat": np.float32(probability),
                        "label": label,
                    }
                )
            if not collect_dice:
                continue
            has_seg = torch.stack(
                [cast(torch.Tensor, sample["has_seg"]).bool() for sample in samples]
            )
            present = int(has_seg.sum())
            n_with_segmentation += present
            n_without_segmentation += len(samples) - present
            seg_logits = getattr(output, "seg_logits", None)
            if seg_logits is None:
                raise ValueError(
                    "model output seg_logits is None; segmentation Dice unavailable"
                )
            if present:
                target = torch.stack(
                    [cast(torch.Tensor, sample["seg"]) for sample in samples]
                )
                per_channel = hard_dice(
                    seg_logits.float().cpu(), target.cpu(), has_seg.cpu()
                )
                dice_sum = (
                    per_channel * present
                    if dice_sum is None
                    else dice_sum + per_channel * present
                )
    if dice_sum is None:
        per_channel_values: list[float | None] = [None] * len(_SEGMENTATION_CHANNELS)
    else:
        per_channel_values = [
            float(value) for value in (dice_sum / n_with_segmentation).tolist()
        ]
    dice_by_channel = dict(zip(_SEGMENTATION_CHANNELS, per_channel_values, strict=True))
    available = [value for value in per_channel_values if value is not None]
    dice_block: dict[str, Any] = {
        "per_channel": dice_by_channel,
        "mean": float(np.mean(available)) if available else None,
        "n_with_segmentation": n_with_segmentation,
        "n_without_segmentation": n_without_segmentation,
    }
    return results, dice_block


def predict_split(
    model: nn.Module,
    dataset: Sequence[Mapping[str, Any]] | Any,
    *,
    device: torch.device | str,
    batch_size: int,
) -> list[dict[str, Any]]:
    """Return ordered patient predictions from full four-sequence inputs.

    The supplied dataset must be built with augmentation disabled and no zeroed
    channels. Each output logit is stored as float32; its sigmoid is evaluated
    in float64 and then stored as float32.
    """
    results, _ = _predict_split(
        model, dataset, device=device, batch_size=batch_size, collect_dice=False
    )
    return results


def predict_split_with_dice(
    model: nn.Module,
    dataset: Sequence[Mapping[str, Any]] | Any,
    *,
    device: torch.device | str,
    batch_size: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return predictions and evaluate-style, patient-weighted hard Dice."""
    return _predict_split(
        model, dataset, device=device, batch_size=batch_size, collect_dice=True
    )

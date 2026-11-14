"""Named model variants and their loss settings for the Phase 10 ablation runs (D-051).

``base`` is the Phase 06 model (R1 to R6). ``whole_brain`` is R7, the H1 ablation:
identical to ``base`` except that the pooled feature vector is the plain global mean
of the bottleneck features, not the tumour-probability-weighted mean. The auxiliary
segmentation head and its loss stay on, so R7 differs from R2 in the pooling and
nothing else.

R8, the H2 ablation (joint vs independent), is two training runs of one budget item:
``stage1_seg`` trains the segmentation network with the Dice loss only (the model
config equals ``whole_brain``; the training config sets ``cls_weight = 0`` and selects
the checkpoint on the calibration-split Dice loss); ``stage2_cls`` trains a classifier
with the IDH loss only (``seg_weight = 0``) that pools with the frozen stage-1 mask.
Nothing here is searched over (R-C08).
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from glioma_selective.models.segresnet import ModelConfig

__all__ = ["STAGE_VARIANTS", "VARIANTS", "model_config_for", "train_overrides"]

VARIANTS: tuple[str, ...] = ("base", "whole_brain", "stage1_seg", "stage2_cls")
STAGE_VARIANTS: tuple[str, ...] = ("stage1_seg", "stage2_cls")


def model_config_for(variant: str) -> ModelConfig:
    """The fixed model config for a named variant; unknown names are an error."""
    if variant == "base":
        return ModelConfig()
    if variant in ("whole_brain", "stage1_seg"):
        return replace(ModelConfig(), tumour_aware_pooling=False)
    if variant == "stage2_cls":
        return replace(ModelConfig(), two_stage=True)
    raise ValueError(f"unknown model variant {variant!r}; expected one of {VARIANTS}")


def train_overrides(variant: str) -> dict[str, Any]:
    """Training-config fields a variant changes from the base training config."""
    if variant in ("base", "whole_brain"):
        return {}
    if variant == "stage1_seg":
        return {"cls_weight": 0.0, "selection": "segmentation"}
    if variant == "stage2_cls":
        return {"seg_weight": 0.0}
    raise ValueError(f"unknown model variant {variant!r}; expected one of {VARIANTS}")

"""SegResNet backbone with an auxiliary segmentation head and an IDH classifier.

The architecture is fixed by SPEC §4.1 and D-037: MONAI ``SegResNet`` as the encoder
(and, when the auxiliary head is on, its decoder), learnable per-modality input
weights, tumour-aware pooling of the bottleneck features, one logit out. There is no
search over any of these choices.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any, NamedTuple

import torch
from monai.networks.nets import SegResNet
from torch import nn

from glioma_selective.models.heads import ClassificationHead
from glioma_selective.models.pooling import tumour_aware_pool

__all__ = ["IDHNet", "ModelConfig", "ModelOutput", "build_model", "parameter_count"]


@dataclass(frozen=True)
class ModelConfig:
    """Every value here mirrors ``configs/model/base.yaml``."""

    in_channels: int = 4
    seg_channels: int = 3
    init_filters: int = 32
    blocks_down: tuple[int, ...] = (1, 2, 2, 4)
    blocks_up: tuple[int, ...] = (1, 1, 1)
    aux_segmentation: bool = True
    tumour_aware_pooling: bool = True
    pooling_min_mass: float = 1.0
    head_hidden: int = 64
    head_dropout: float = 0.2

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> ModelConfig:
        """Build from a config mapping; unknown keys are an error, not ignored."""
        known = {field.name for field in fields(cls)}
        extra = set(values) - known
        if extra:
            raise ValueError(f"unknown model config keys: {sorted(extra)}")
        converted = dict(values)
        for key in ("blocks_down", "blocks_up"):
            if key in converted:
                converted[key] = tuple(int(item) for item in converted[key])
        return cls(**converted)


class ModelOutput(NamedTuple):
    """``logit`` is ``[B]``; ``seg_logits`` is ``[B, seg, D, H, W]`` or None."""

    logit: torch.Tensor
    seg_logits: torch.Tensor | None


class IDHNet(nn.Module):
    """Four-channel volume in, IDH-mutant logit (and optional tumour segmentation) out.

    A modality that is zeroed in the input stays zero after the per-modality weight,
    so missing-modality inputs are zeroed and never imputed (SPEC §4.4).
    """

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        if config.tumour_aware_pooling and not config.aux_segmentation:
            raise ValueError(
                "tumour-aware pooling needs the auxiliary segmentation head"
            )
        self.config = config
        self.modality_weights = nn.Parameter(torch.ones(config.in_channels))
        self.backbone = SegResNet(
            spatial_dims=3,
            init_filters=config.init_filters,
            in_channels=config.in_channels,
            out_channels=config.seg_channels,
            blocks_down=config.blocks_down,
            blocks_up=config.blocks_up,
        )
        bottleneck = config.init_filters * 2 ** (len(config.blocks_down) - 1)
        self.head = ClassificationHead(
            bottleneck, config.head_hidden, config.head_dropout
        )

    def forward(self, image: torch.Tensor) -> ModelOutput:
        weighted = image * self.modality_weights.view(1, -1, 1, 1, 1)
        features, skips = self.backbone.encode(weighted)
        seg_logits: torch.Tensor | None = None
        if self.config.aux_segmentation:
            skips.reverse()
            seg_logits = self.backbone.decode(features, skips)
        if self.config.tumour_aware_pooling and seg_logits is not None:
            # Whole-tumour probability, detached: the classification loss must not
            # move the segmentation head (D-037).
            whole_tumour = torch.sigmoid(seg_logits.detach()).amax(dim=1, keepdim=True)
            pooled = tumour_aware_pool(
                features, whole_tumour, min_mass=self.config.pooling_min_mass
            )
        else:
            pooled = features.mean(dim=(2, 3, 4))
        return ModelOutput(logit=self.head(pooled), seg_logits=seg_logits)


def build_model(config: ModelConfig | Mapping[str, Any]) -> IDHNet:
    """Construct the network from a ``ModelConfig`` or a config mapping."""
    if not isinstance(config, ModelConfig):
        config = ModelConfig.from_mapping(config)
    return IDHNet(config)


def parameter_count(model: nn.Module) -> int:
    """Number of trainable parameters."""
    return sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )

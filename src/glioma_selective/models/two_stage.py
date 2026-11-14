"""Two-stage independent segment-then-classify network (R8, D-051).

Stage 1 is the same SegResNet as the joint model, trained with the segmentation loss
only. Stage 2 is a second SegResNet encoder with its own classification head, trained
with the IDH loss only. Stage 2 pools its bottleneck features with the whole-tumour
probability that the frozen stage-1 network predicts for the same (possibly
modality-dropped) input, so the only link between the stages is that fixed mask. No
gradient crosses from the classification loss into stage 1, and none from the
segmentation loss into stage 2. Nothing here is searched over (R-C08).
"""

from __future__ import annotations

from dataclasses import replace

import torch

from glioma_selective.models.pooling import tumour_aware_pool
from glioma_selective.models.segresnet import IDHNet, ModelConfig

__all__ = ["TwoStageNet"]


class TwoStageNet(IDHNet):
    """IDHNet whose pooling mask comes from a frozen, separately trained stage 1.

    The inherited ``backbone``, ``modality_weights`` and ``head`` are the stage-2
    classifier; ``stage1`` is the segmentation network. ``seg_logits`` in the output
    are stage 1's, so segmentation Dice reports the stage-1 network.
    """

    def __init__(self, config: ModelConfig) -> None:
        if not config.two_stage:
            raise ValueError("TwoStageNet needs config.two_stage = True")
        super().__init__(config)
        self.stage1 = IDHNet(
            replace(
                config,
                two_stage=False,
                aux_segmentation=True,
                tumour_aware_pooling=False,
            )
        )
        self.stage1.requires_grad_(False)
        self.stage1.eval()

    def train(self, mode: bool = True) -> TwoStageNet:
        super().train(mode)
        self.stage1.eval()  # frozen: never trains, whatever the stage-2 mode is
        return self

    def pooled_features(
        self, image: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        with torch.no_grad():
            seg_logits = self.stage1(image).seg_logits
        if seg_logits is None:
            raise RuntimeError("stage 1 produced no segmentation logits")
        whole_tumour = torch.sigmoid(seg_logits).amax(dim=1, keepdim=True)
        weighted = image * self.modality_weights.view(1, -1, 1, 1, 1)
        features, _ = self.backbone.encode(weighted)
        pooled = tumour_aware_pool(
            features, whole_tumour, min_mass=self.config.pooling_min_mass
        )
        return pooled, seg_logits

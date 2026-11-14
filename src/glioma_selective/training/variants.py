"""Named model variants for the Phase 10 ablation runs (D-051).

``base`` is the Phase 06 model (R1 to R6). ``whole_brain`` is R7, the H1 ablation:
identical to ``base`` except that the pooled feature vector is the plain global mean
of the bottleneck features, not the tumour-probability-weighted mean. The auxiliary
segmentation head and its loss stay on, so the run differs from R2 in the pooling
and nothing else. Nothing here is searched over (R-C08).
"""

from __future__ import annotations

from dataclasses import replace

from glioma_selective.models.segresnet import ModelConfig

__all__ = ["VARIANTS", "model_config_for"]

VARIANTS: tuple[str, ...] = ("base", "whole_brain")


def model_config_for(variant: str) -> ModelConfig:
    """The fixed model config for a named variant; unknown names are an error."""
    if variant == "base":
        return ModelConfig()
    if variant == "whole_brain":
        return replace(ModelConfig(), tumour_aware_pooling=False)
    raise ValueError(f"unknown model variant {variant!r}; expected one of {VARIANTS}")

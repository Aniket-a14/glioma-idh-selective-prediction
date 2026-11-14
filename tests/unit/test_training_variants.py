"""R7 whole-brain pooling variant (D-051): one flag differs, nothing else."""

from __future__ import annotations

from dataclasses import asdict, replace

import pytest
import torch

from glioma_selective.models.segresnet import ModelConfig, build_model
from glioma_selective.training import authorization
from glioma_selective.training.run import RunSpec
from glioma_selective.training.variants import VARIANTS, model_config_for

SMALL = ModelConfig(init_filters=8, head_hidden=8, head_dropout=0.0)


def test_base_variant_is_the_default_model_config() -> None:
    assert model_config_for("base") == ModelConfig()
    assert RunSpec(label="x").variant == "base"


def test_whole_brain_differs_from_base_only_in_pooling() -> None:
    base = asdict(model_config_for("base"))
    whole = asdict(model_config_for("whole_brain"))
    changed = {key for key in base if base[key] != whole[key]}
    assert changed == {"tumour_aware_pooling"}
    assert whole["tumour_aware_pooling"] is False
    assert whole["aux_segmentation"] is True


def test_unknown_variant_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown model variant"):
        model_config_for("two_stage_typo")
    assert set(VARIANTS) == {"base", "whole_brain"}


def test_authorization_digest_depends_on_the_variant() -> None:
    assert authorization.base_config_sha256() == authorization.base_config_sha256(
        "base"
    )
    assert authorization.base_config_sha256(
        "whole_brain"
    ) != authorization.base_config_sha256("base")


def test_whole_brain_model_pools_with_the_plain_mean() -> None:
    torch.manual_seed(0)
    config = replace(SMALL, tumour_aware_pooling=False)
    model = build_model(config).eval()
    image = torch.randn(2, 4, 32, 32, 32)
    with torch.no_grad():
        pooled, seg_logits = model.pooled_features(image)
        weighted = image * model.modality_weights.view(1, -1, 1, 1, 1)
        features, _ = model.backbone.encode(weighted)
    assert seg_logits is not None
    assert torch.equal(pooled, features.mean(dim=(2, 3, 4)))


def test_whole_brain_and_base_models_have_the_same_parameter_shapes() -> None:
    base = build_model(replace(SMALL, tumour_aware_pooling=True))
    whole = build_model(replace(SMALL, tumour_aware_pooling=False))
    base_shapes = {name: p.shape for name, p in base.named_parameters()}
    whole_shapes = {name: p.shape for name, p in whole.named_parameters()}
    assert base_shapes == whole_shapes


def test_synthetic_harness_config_follows_the_variant() -> None:
    base = authorization._model_config(True, "base")
    whole = authorization._model_config(True, "whole_brain")
    assert base.tumour_aware_pooling is True
    assert whole.tumour_aware_pooling is False
    assert whole.init_filters == base.init_filters

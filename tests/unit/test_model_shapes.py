"""Shapes, parameter count, zeroed channels and pooling of the Phase 06 model."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import torch
from omegaconf import OmegaConf

from glioma_selective.models.pooling import tumour_aware_pool
from glioma_selective.models.segresnet import (
    IDHNet,
    ModelConfig,
    build_model,
    parameter_count,
)

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "configs/model/base.yaml"
# Same architecture family at a size that runs on a CPU in a unit test.
SMALL = ModelConfig(init_filters=8, head_hidden=8)


def _image(batch: int, size: int, seed: int = 0) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    return torch.randn(batch, 4, size, size, size, generator=generator)


def test_default_config_parameter_count_is_within_the_spec_range() -> None:
    count = parameter_count(build_model(ModelConfig()))
    assert 10_000_000 <= count <= 30_000_000


def test_yaml_config_equals_the_dataclass_defaults() -> None:
    raw = OmegaConf.to_container(OmegaConf.load(CONFIG_PATH), resolve=True)
    assert ModelConfig.from_mapping(raw) == ModelConfig()  # type: ignore[arg-type]


def test_unknown_config_key_is_an_error() -> None:
    with pytest.raises(ValueError, match="unknown model config keys"):
        ModelConfig.from_mapping({"init_filters": 8, "depth": 5})


@pytest.mark.parametrize("size", [96, 128])
def test_output_shapes_at_both_patch_sizes(size: int) -> None:
    model = IDHNet(SMALL).eval()
    with torch.no_grad():
        output = model(_image(1, size))
    assert output.logit.shape == (1,)
    assert output.seg_logits is not None
    assert output.seg_logits.shape == (1, 3, size, size, size)


def test_batch_of_two_gives_one_logit_per_patient() -> None:
    model = IDHNet(SMALL).eval()
    with torch.no_grad():
        output = model(_image(2, 32))
    assert output.logit.shape == (2,)


def test_without_the_aux_head_there_is_no_segmentation_output() -> None:
    model = IDHNet(
        replace(SMALL, aux_segmentation=False, tumour_aware_pooling=False)
    ).eval()
    with torch.no_grad():
        output = model(_image(1, 32))
    assert output.seg_logits is None
    assert output.logit.shape == (1,)


def test_tumour_aware_pooling_requires_the_aux_head() -> None:
    with pytest.raises(ValueError, match="auxiliary segmentation"):
        IDHNet(replace(SMALL, aux_segmentation=False, tumour_aware_pooling=True))


def test_forward_works_with_a_zeroed_channel_and_the_weight_cannot_revive_it() -> None:
    model = IDHNet(SMALL).eval()
    image = _image(1, 32)
    image[:, 2] = 0.0
    with torch.no_grad():
        before = model(image)
        model.modality_weights[2] = 5.0
        after = model(image)
    assert torch.isfinite(before.logit).all()
    assert torch.equal(before.logit, after.logit)


def test_pooling_weights_features_by_tumour_probability() -> None:
    features = torch.tensor([2.0, 4.0]).view(1, 1, 2, 1, 1)
    probability = torch.tensor([1.0, 3.0]).view(
        1, 1, 2, 1, 1
    )  # weights need not sum to 1
    pooled = tumour_aware_pool(features, probability, min_mass=1.0)
    assert pooled.item() == pytest.approx((2 * 1 + 4 * 3) / 4)  # 3.5


def test_pooling_with_an_all_ones_mask_is_global_average_pooling() -> None:
    features = torch.randn(2, 5, 3, 4, 2)
    pooled = tumour_aware_pool(features, torch.ones(2, 1, 3, 4, 2), min_mass=1.0)
    assert torch.allclose(pooled, features.mean(dim=(2, 3, 4)), atol=1e-6)


def test_pooling_falls_back_to_global_when_the_predicted_mass_is_tiny() -> None:
    features = torch.tensor([2.0, 4.0]).view(1, 1, 2, 1, 1)
    probability = torch.tensor([0.2, 0.3]).view(1, 1, 2, 1, 1)  # mass 0.5 < 1.0
    assert tumour_aware_pool(
        features, probability, min_mass=1.0
    ).item() == pytest.approx(3.0)


def test_pooling_averages_a_finer_mask_down_to_the_feature_grid() -> None:
    features = torch.tensor([2.0, 4.0]).view(1, 1, 2, 1, 1)
    probability = torch.tensor([1.0, 1.0, 0.0, 0.0]).view(1, 1, 4, 1, 1)
    # feature cell weights become [1, 0], so only the first cell counts
    assert tumour_aware_pool(
        features, probability, min_mass=1.0
    ).item() == pytest.approx(2.0)


def test_pooling_treats_each_patient_separately() -> None:
    features = torch.tensor([[2.0, 4.0], [2.0, 4.0]]).view(2, 1, 2, 1, 1)
    probability = torch.tensor([[1.0, 0.0], [0.0, 1.0]]).view(2, 1, 2, 1, 1)
    pooled = tumour_aware_pool(features, probability, min_mass=1.0)
    assert pooled.flatten().tolist() == pytest.approx([2.0, 4.0])


def test_full_predicted_mask_makes_the_model_equal_global_pooling() -> None:
    aware = IDHNet(SMALL).eval()
    with torch.no_grad():
        final = aware.backbone.conv_final[-1]
        final.conv.weight.zero_()
        final.conv.bias.fill_(50.0)  # sigmoid(50) == 1 in float32
    plain = IDHNet(replace(SMALL, tumour_aware_pooling=False)).eval()
    plain.load_state_dict(aware.state_dict())
    image = _image(1, 32)
    with torch.no_grad():
        assert torch.allclose(aware(image).logit, plain(image).logit, atol=1e-5)


def test_classification_loss_does_not_reach_the_segmentation_head() -> None:
    model = IDHNet(SMALL)
    model(_image(1, 32)).logit.sum().backward()
    assert (
        model.backbone.convInit.conv.weight.grad is not None
    )  # the shared encoder learns
    mask_head = model.backbone.conv_final[-1]
    assert mask_head.conv.weight.grad is None  # the mask head does not
    assert all(p.grad is None for p in model.backbone.up_layers.parameters())

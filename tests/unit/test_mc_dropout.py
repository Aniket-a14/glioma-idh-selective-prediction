"""Head-only MC-dropout (M3, D-048): what it perturbs, reproducibility, mode restore."""

from __future__ import annotations

from dataclasses import replace

import pytest
import torch
from torch import nn

from glioma_selective.models.segresnet import IDHNet, ModelConfig, build_model
from glioma_selective.uncertainty.mc_dropout import mc_dropout_probabilities

SMALL = ModelConfig(init_filters=8, head_hidden=8)


def _model(config: ModelConfig = SMALL) -> IDHNet:
    torch.manual_seed(0)
    return build_model(config).eval()


def _image(batch: int = 2, size: int = 16, seed: int = 0) -> torch.Tensor:
    generator = torch.Generator().manual_seed(seed)
    return torch.randn(batch, 4, size, size, size, generator=generator)


def test_pooled_features_then_head_equals_the_forward_pass() -> None:
    model, image = _model(), _image()
    with torch.no_grad():
        pooled, seg = model.pooled_features(image)
        output = model(image)
    assert torch.equal(model.head(pooled), output.logit)
    assert seg is not None and torch.equal(seg, output.seg_logits)  # type: ignore[arg-type]


def test_passes_vary_with_dropout_and_have_the_right_shape() -> None:
    probabilities = mc_dropout_probabilities(
        _model(), _image(), passes=12, generator=torch.Generator().manual_seed(1)
    )
    assert probabilities.shape == (2, 12)
    assert probabilities.dtype == torch.float32
    assert bool(((probabilities > 0) & (probabilities < 1)).all())
    assert float(probabilities.std(dim=1).min()) > 0.0


def test_without_dropout_every_pass_equals_the_deterministic_probability() -> None:
    model = _model(replace(SMALL, head_dropout=0.0))
    image = _image()
    with torch.no_grad():
        deterministic = torch.sigmoid(model(image).logit.double()).float()
    probabilities = mc_dropout_probabilities(
        model, image, passes=5, generator=torch.Generator().manual_seed(2)
    )
    assert torch.allclose(probabilities, deterministic[:, None].expand(-1, 5))


def test_a_seeded_generator_reproduces_and_another_seed_differs() -> None:
    model, image = _model(), _image()
    first = mc_dropout_probabilities(
        model, image, passes=6, generator=torch.Generator().manual_seed(3)
    )
    again = mc_dropout_probabilities(
        model, image, passes=6, generator=torch.Generator().manual_seed(3)
    )
    other = mc_dropout_probabilities(
        model, image, passes=6, generator=torch.Generator().manual_seed(4)
    )
    assert torch.equal(first, again)
    assert not torch.equal(first, other)


def test_a_single_pass_matches_a_hand_computed_masked_head() -> None:
    model, image = _model(), _image(batch=1)
    drawn = mc_dropout_probabilities(
        model, image, passes=1, generator=torch.Generator().manual_seed(5)
    )
    with torch.no_grad():
        pooled, _ = model.pooled_features(image)
        linear_in, _relu, dropout, linear_out = model.head.layers
        hidden = torch.relu(linear_in(pooled))
        keep = 1.0 - dropout.p
        mask = torch.bernoulli(
            torch.full_like(hidden, keep), generator=torch.Generator().manual_seed(5)
        )
        expected = torch.sigmoid(linear_out(hidden * mask / keep).squeeze(-1).double())
    assert drawn[0, 0] == pytest.approx(float(expected[0]), abs=1e-6)


def test_dropout_modes_are_restored_and_the_backbone_stays_in_eval() -> None:
    model, image = _model(), _image()
    mc_dropout_probabilities(model, image, passes=2)
    assert not any(
        layer.training
        for layer in model.head.modules()
        if isinstance(layer, nn.Dropout)
    )
    assert not model.backbone.training


def test_the_global_rng_path_also_works_and_bad_arguments_fail() -> None:
    model, image = _model(), _image()
    assert mc_dropout_probabilities(model, image, passes=3).shape == (2, 3)
    with pytest.raises(ValueError, match="passes"):
        mc_dropout_probabilities(model, image, passes=0)

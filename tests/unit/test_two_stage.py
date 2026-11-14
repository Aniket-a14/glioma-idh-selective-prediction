"""R8 two-stage ablation (D-051): stage isolation, loss weights, selection."""

from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path

import pytest
import torch
from tests.unit.test_training_loop import CPU, SMALL, _Dataset, _Loader

from glioma_selective.models.segresnet import IDHNet, ModelConfig, build_model
from glioma_selective.models.two_stage import TwoStageNet
from glioma_selective.training import authorization
from glioma_selective.training.checkpoint import load_model_weights, save_model_weights
from glioma_selective.training.loop import TrainConfig, fit
from glioma_selective.training.losses import joint_loss
from glioma_selective.training.variants import (
    STAGE_VARIANTS,
    model_config_for,
    train_overrides,
)

TWO_STAGE = replace(SMALL, two_stage=True)


def _model() -> TwoStageNet:
    torch.manual_seed(0)
    model = build_model(TWO_STAGE)
    assert isinstance(model, TwoStageNet)
    return model


def test_variant_configs_and_training_overrides() -> None:
    stage1, stage2 = model_config_for("stage1_seg"), model_config_for("stage2_cls")
    assert stage1 == model_config_for("whole_brain")
    assert stage2.two_stage and not stage1.two_stage
    assert train_overrides("stage1_seg") == {
        "cls_weight": 0.0,
        "selection": "segmentation",
    }
    assert train_overrides("stage2_cls") == {"seg_weight": 0.0}
    assert train_overrides("base") == {} == train_overrides("whole_brain")
    assert set(STAGE_VARIANTS) == {"stage1_seg", "stage2_cls"}


def test_authorization_digests_differ_across_all_four_variants() -> None:
    digests = {
        v: authorization.base_config_sha256(v)
        for v in ("base", "whole_brain", "stage1_seg", "stage2_cls")
    }
    assert len(set(digests.values())) == 4


def test_stage_one_is_frozen_and_stays_in_eval_mode() -> None:
    model = _model()
    assert not any(p.requires_grad for p in model.stage1.parameters())
    model.train()
    assert model.training and not model.stage1.training


def test_classification_gradient_never_reaches_stage_one() -> None:
    model = _model()
    model.train()
    output = model(torch.randn(2, 4, 16, 16, 16))
    output.logit.sum().backward()
    assert all(p.grad is None for p in model.stage1.parameters())
    assert any(p.grad is not None for p in model.head.parameters())
    assert any(p.grad is not None for p in model.backbone.parameters())


def test_segmentation_logits_are_stage_ones_and_mask_changes_pooling() -> None:
    model = _model().eval()
    image = torch.randn(2, 4, 16, 16, 16)
    with torch.no_grad():
        output = model(image)
        expected = model.stage1(image).seg_logits
        assert expected is not None
        assert torch.equal(output.seg_logits, expected)  # type: ignore[arg-type]
        pooled_before, _ = model.pooled_features(image)
        for parameter in model.stage1.parameters():
            parameter.add_(0.5)
        pooled_after, _ = model.pooled_features(image)
    assert not torch.equal(pooled_before, pooled_after)


def test_state_dict_round_trip_restores_both_stages(tmp_path: Path) -> None:
    source = _model()
    path = tmp_path / "best.pt"
    save_model_weights(path, source, epoch=3)
    torch.manual_seed(1)
    target = build_model(TWO_STAGE)
    assert load_model_weights(path, target) == 3
    probe = torch.randn(1, 4, 16, 16, 16)
    source.eval()
    target.eval()
    with torch.no_grad():
        assert torch.equal(source(probe).logit, target(probe).logit)


def test_stage_one_weights_load_into_the_stage_two_wrapper(tmp_path: Path) -> None:
    torch.manual_seed(2)
    trained = IDHNet(replace(SMALL, tumour_aware_pooling=False))
    path = tmp_path / "stage1.pt"
    save_model_weights(path, trained, epoch=1)
    wrapper = _model()
    load_model_weights(path, wrapper.stage1)
    for a, b in zip(trained.parameters(), wrapper.stage1.parameters(), strict=True):
        assert torch.equal(a, b)


def test_joint_loss_weights_select_one_task() -> None:
    logit = torch.tensor([0.5, -1.0])
    label = torch.tensor([1.0, 0.0])
    seg_logits = torch.randn(2, 3, 4, 4, 4)
    seg = (torch.rand(2, 3, 4, 4, 4) > 0.5).float()
    has_seg = torch.tensor([True, True])
    kwargs = dict(pos_weight=1.0, dice_smooth=1.0)
    both = joint_loss(logit, seg_logits, label, seg, has_seg, seg_weight=1.0, **kwargs)
    seg_only = joint_loss(
        logit, seg_logits, label, seg, has_seg, seg_weight=1.0, cls_weight=0.0, **kwargs
    )
    cls_only = joint_loss(
        logit, seg_logits, label, seg, has_seg, seg_weight=0.0, **kwargs
    )
    assert torch.allclose(both.total, both.classification + both.segmentation)
    assert torch.allclose(seg_only.total, both.segmentation)
    assert torch.allclose(cls_only.total, both.classification)


def test_train_config_rejects_bad_selection_and_negative_weights() -> None:
    with pytest.raises(ValueError, match="selection"):
        TrainConfig(selection="auroc")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="negative"):
        TrainConfig(cls_weight=-1.0)
    assert asdict(TrainConfig())["cls_weight"] == 1.0


def test_stage_one_training_ignores_the_classifier_and_selects_on_dice(
    tmp_path: Path,
) -> None:
    torch.manual_seed(0)
    model = IDHNet(replace(SMALL, tumour_aware_pooling=False))
    head_before = [p.detach().clone() for p in model.head.parameters()]
    config = replace(
        TrainConfig(
            max_epochs=3,
            batch_size=1,
            accumulation_steps=2,
            learning_rate=1e-2,
            weight_decay=0.0,
            amp="off",
            early_stopping_patience=5,
        ),
        **train_overrides("stage1_seg"),
    )
    train = _Loader(_Dataset(8, 1), 5, True)
    calibration = _Loader(_Dataset(4, 2), 0, False)
    result = fit(
        model,
        train,
        calibration,
        config,
        pos_weight=1.0,
        checkpoint_dir=tmp_path,
        device=CPU,
    )
    history = result.state.history
    best_epoch = min(
        range(len(history)), key=lambda i: history[i]["calibration_segmentation"]
    )
    assert result.state.best_epoch == best_epoch
    assert result.state.best_value == pytest.approx(
        history[best_epoch]["calibration_segmentation"]
    )
    for before, after in zip(head_before, model.head.parameters(), strict=True):
        assert torch.equal(
            before, after
        )  # weight_decay 0 and zero classification gradient


def test_stage_two_training_leaves_stage_one_unchanged(tmp_path: Path) -> None:
    model = _model()
    stage1_before = [p.detach().clone() for p in model.stage1.parameters()]
    head_before = [p.detach().clone() for p in model.head.parameters()]
    config = replace(
        TrainConfig(
            max_epochs=2,
            batch_size=1,
            accumulation_steps=2,
            learning_rate=1e-2,
            amp="off",
            early_stopping_patience=5,
        ),
        **train_overrides("stage2_cls"),
    )
    fit(
        model,
        _Loader(_Dataset(8, 1), 5, True),
        _Loader(_Dataset(4, 2), 0, False),
        config,
        pos_weight=1.0,
        checkpoint_dir=tmp_path,
        device=CPU,
    )
    for before, after in zip(stage1_before, model.stage1.parameters(), strict=True):
        assert torch.equal(before, after)
    assert any(
        not torch.equal(b, a)
        for b, a in zip(head_before, model.head.parameters(), strict=True)
    )


def test_model_config_still_rejects_unknown_keys() -> None:
    values = asdict(ModelConfig())
    values["two_stage"] = True
    assert ModelConfig.from_mapping(values).two_stage is True
    values["bogus"] = 1
    with pytest.raises(ValueError, match="unknown model config keys"):
        ModelConfig.from_mapping(values)

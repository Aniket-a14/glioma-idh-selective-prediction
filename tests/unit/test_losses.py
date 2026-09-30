"""Hand-worked values for the Phase 06 losses (T06.4), and a tiny end-to-end fit."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest
import torch

from glioma_selective.models.segresnet import IDHNet, ModelConfig
from glioma_selective.training.losses import (
    class_balanced_bce,
    joint_loss,
    pos_weight_from_counts,
    soft_dice_loss,
)

HIGH = 50.0  # sigmoid(50) is 1.0 and sigmoid(-50) is 2e-22 in float32


def test_pos_weight_is_negatives_over_positives() -> None:
    assert pos_weight_from_counts(10, 5) == 2.0
    assert pos_weight_from_counts(265, 103) == pytest.approx(2.5728, abs=1e-4)


def test_pos_weight_needs_both_classes() -> None:
    with pytest.raises(ValueError):
        pos_weight_from_counts(10, 0)


def test_bce_at_logit_zero_is_ln2_times_the_class_weight() -> None:
    logits = torch.zeros(2)
    labels = torch.tensor([1.0, 0.0])
    # y=1: 2 * ln 2 ; y=0: ln 2 ; mean of the two
    expected = (2 * math.log(2) + math.log(2)) / 2
    assert class_balanced_bce(logits, labels, pos_weight=2.0).item() == pytest.approx(
        expected
    )


def test_bce_gives_a_missed_positive_more_loss_than_a_missed_negative() -> None:
    miss_positive = class_balanced_bce(
        torch.tensor([-2.0]), torch.tensor([1.0]), pos_weight=3.0
    )
    miss_negative = class_balanced_bce(
        torch.tensor([2.0]), torch.tensor([0.0]), pos_weight=3.0
    )
    assert miss_positive.item() == pytest.approx(3 * miss_negative.item())


def _seg(pred: list[float], truth: list[float]) -> tuple[torch.Tensor, torch.Tensor]:
    logits = torch.tensor([HIGH if p else -HIGH for p in pred]).view(1, 1, -1, 1, 1)
    return logits, torch.tensor(truth).view(1, 1, -1, 1, 1)


def test_dice_loss_with_a_perfect_prediction_is_zero() -> None:
    logits, truth = _seg([1, 1, 0, 0], [1, 1, 0, 0])
    loss = soft_dice_loss(logits, truth, torch.tensor([True]), smooth=1e-6)
    assert loss.item() == pytest.approx(0.0, abs=1e-5)


def test_dice_loss_with_half_overlap_is_one_third() -> None:
    # pred covers 2 voxels, truth 1 of them: dice = 2*1 / (2+1) = 2/3, loss = 1/3
    logits, truth = _seg([1, 1, 0, 0], [1, 0, 0, 0])
    loss = soft_dice_loss(logits, truth, torch.tensor([True]), smooth=1e-6)
    assert loss.item() == pytest.approx(1 / 3, abs=1e-4)


def test_dice_loss_averages_over_channels() -> None:
    first, truth_first = _seg([1, 1, 0, 0], [1, 0, 0, 0])  # dice 2/3
    second, truth_second = _seg([1, 0, 0, 0], [1, 0, 0, 0])  # dice 1
    logits = torch.cat([first, second], dim=1)
    truth = torch.cat([truth_first, truth_second], dim=1)
    loss = soft_dice_loss(logits, truth, torch.tensor([True]), smooth=1e-6)
    assert loss.item() == pytest.approx(1 - (2 / 3 + 1) / 2, abs=1e-4)  # 1/6


def test_dice_loss_of_an_empty_target_and_empty_prediction_is_zero() -> None:
    logits, truth = _seg([0, 0, 0, 0], [0, 0, 0, 0])
    loss = soft_dice_loss(logits, truth, torch.tensor([True]), smooth=1e-6)
    assert loss.item() == pytest.approx(0.0, abs=1e-5)


def test_dice_loss_skips_patients_without_a_segmentation() -> None:
    good, truth_good = _seg([1, 1, 0, 0], [1, 0, 0, 0])
    bad, truth_bad = _seg([1, 1, 1, 1], [0, 0, 0, 0])
    logits = torch.cat([good, bad])
    truth = torch.cat([truth_good, truth_bad])
    both = soft_dice_loss(logits, truth, torch.tensor([True, False]), smooth=1e-6)
    alone = soft_dice_loss(good, truth_good, torch.tensor([True]), smooth=1e-6)
    assert both.item() == pytest.approx(alone.item())


def test_dice_loss_is_zero_with_a_gradient_path_when_nobody_has_a_segmentation() -> (
    None
):
    logits = torch.zeros(2, 3, 2, 2, 2, requires_grad=True)
    loss = soft_dice_loss(
        logits, torch.zeros(2, 3, 2, 2, 2), torch.tensor([False, False]), smooth=1e-6
    )
    loss.backward()
    assert loss.item() == 0.0
    assert logits.grad is not None


def test_joint_loss_adds_the_weighted_segmentation_term() -> None:
    logits, truth = _seg([1, 1, 0, 0], [1, 0, 0, 0])
    result = joint_loss(
        torch.zeros(1),
        logits,
        torch.tensor([1.0]),
        truth,
        torch.tensor([True]),
        pos_weight=2.0,
        seg_weight=0.5,
        dice_smooth=1e-6,
    )
    assert result.classification.item() == pytest.approx(2 * math.log(2))
    assert result.segmentation.item() == pytest.approx(1 / 3, abs=1e-4)
    assert result.total.item() == pytest.approx(2 * math.log(2) + 0.5 / 3, abs=1e-4)


def test_joint_loss_without_the_aux_head_is_just_the_classification_loss() -> None:
    result = joint_loss(
        torch.zeros(1),
        None,
        torch.tensor([1.0]),
        torch.zeros(1, 3, 2, 2, 2),
        torch.tensor([True]),
        pos_weight=2.0,
        seg_weight=0.5,
        dice_smooth=1e-6,
    )
    assert result.segmentation.item() == 0.0
    assert result.total.item() == pytest.approx(result.classification.item())


def test_the_model_and_the_loss_fit_four_synthetic_patients() -> None:
    """Wiring check only. The Phase 06 tiny-overfit test on real patients is T06.8."""
    torch.manual_seed(0)
    size = 16
    label = torch.tensor([1.0, 0.0, 1.0, 0.0])
    image = torch.randn(4, 4, size, size, size) * 0.1
    image += (label * 2 - 1).view(4, 1, 1, 1, 1)  # class-dependent brightness
    seg = torch.zeros(4, 3, size, size, size)
    seg[:, 0, 4:12, 4:12, 4:12] = 1.0
    has_seg = torch.tensor([True, True, True, True])
    model = IDHNet(
        replace(ModelConfig(), init_filters=8, head_hidden=8, head_dropout=0.0)
    )
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-3)
    first = last = None
    for _ in range(60):
        optimizer.zero_grad()
        output = model(image)
        loss = joint_loss(
            output.logit,
            output.seg_logits,
            label,
            seg,
            has_seg,
            pos_weight=1.0,
            seg_weight=1.0,
            dice_smooth=1e-6,
        )
        loss.total.backward()
        optimizer.step()
        first = loss.classification.item() if first is None else first
        last = loss.classification.item()
    assert last is not None and first is not None
    assert last < 0.05 < first

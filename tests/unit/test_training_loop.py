"""Training loop, checkpoint resume and early stopping on synthetic patients (T06.6)."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch
from omegaconf import OmegaConf

from glioma_selective.models.segresnet import IDHNet, ModelConfig
from glioma_selective.training.checkpoint import (
    TrainState,
    file_sha256,
    load_checkpoint,
    load_model_weights,
    save_checkpoint,
)
from glioma_selective.training.loop import (
    TrainConfig,
    evaluate,
    fit,
    make_optimizer,
)
from glioma_selective.training.metrics import binary_auroc, hard_dice

CPU = torch.device("cpu")
TRAINING_YAML = (
    Path(__file__).resolve().parent.parent.parent / "configs/training/base.yaml"
)
SIZE = 8
SMALL = ModelConfig(
    init_filters=8, blocks_down=(1, 1, 1, 1), head_hidden=8, head_dropout=0.0
)
CONFIG = TrainConfig(
    max_epochs=3,
    batch_size=1,
    accumulation_steps=2,
    learning_rate=1e-2,
    amp="off",
    early_stopping_patience=2,
)


class _Dataset:
    def __init__(self, count: int, seed: int) -> None:
        generator = torch.Generator().manual_seed(seed)
        self.labels = torch.tensor([float(i % 2) for i in range(count)])
        self.images = torch.randn(count, 4, SIZE, SIZE, SIZE, generator=generator) * 0.1
        self.images += (self.labels * 2 - 1).view(-1, 1, 1, 1, 1)
        self.seg = torch.zeros(count, 3, SIZE, SIZE, SIZE)
        self.seg[:, 0, 2:6, 2:6, 2:6] = 1.0
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch


class _Loader:
    """Deterministic shuffled batches of one patient, ordered by (seed, epoch)."""

    def __init__(self, dataset: _Dataset, seed: int, shuffle: bool) -> None:
        self.dataset = dataset
        self.seed = seed
        self.shuffle = shuffle

    def __iter__(self):  # type: ignore[no-untyped-def]
        count = len(self.dataset.labels)
        if self.shuffle:
            generator = torch.Generator().manual_seed(self.seed + self.dataset.epoch)
            order = torch.randperm(count, generator=generator).tolist()
        else:
            order = list(range(count))
        for index in order:
            yield {
                "image": self.dataset.images[index : index + 1],
                "seg": self.dataset.seg[index : index + 1],
                "has_seg": torch.tensor([True]),
                "label": self.dataset.labels[index : index + 1],
            }


def _model() -> IDHNet:
    torch.manual_seed(0)
    return IDHNet(SMALL)


def _loaders() -> tuple[_Loader, _Loader]:
    return _Loader(_Dataset(8, 1), 5, True), _Loader(_Dataset(4, 2), 0, False)


def _params(model: torch.nn.Module) -> list[torch.Tensor]:
    return [p.detach().clone() for p in model.parameters()]


def test_binary_auroc_hand_values() -> None:
    label = np.array([1, 1, 0, 0])
    assert binary_auroc(np.array([0.9, 0.8, 0.3, 0.1]), label) == 1.0
    assert binary_auroc(np.array([0.1, 0.3, 0.8, 0.9]), label) == 0.0
    # one positive ties with one negative (0.5), the other pair is ordered: 3.5 / 4
    assert binary_auroc(np.array([0.9, 0.5, 0.5, 0.1]), label) == pytest.approx(0.875)
    assert math.isnan(binary_auroc(np.array([0.2, 0.4]), np.array([1, 1])))


def test_hard_dice_counts_empty_matches_and_skips_missing_masks() -> None:
    logits = torch.tensor([[[50.0, 50.0, -50.0, -50.0]], [[50.0, 50.0, 50.0, 50.0]]])
    logits = logits.view(2, 1, 4, 1, 1)
    target = torch.tensor([[[1.0, 0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0, 0.0]]]).view(
        2, 1, 4, 1, 1
    )
    both = hard_dice(logits, target, torch.tensor([True, False]))
    assert both.item() == pytest.approx(2 / 3)  # 2*1 / (2+1); second patient ignored
    empty = hard_dice(
        -logits.abs(), torch.zeros_like(target), torch.tensor([True, True])
    )
    assert empty.item() == 1.0  # empty prediction on an empty target
    assert torch.isnan(hard_dice(logits, target, torch.tensor([False, False]))).all()


def test_fit_lowers_the_calibration_loss_and_writes_both_checkpoints(
    tmp_path: Path,
) -> None:
    train, calibration = _loaders()
    model = _model()
    before = evaluate(model, calibration, CONFIG, 1.0, CPU).classification_loss
    result = fit(
        model,
        train,
        calibration,
        CONFIG,
        pos_weight=1.0,
        checkpoint_dir=tmp_path,
        device=CPU,
    )
    assert result.state.history[0]["calibration_classification"] == pytest.approx(
        result.state.history[0]["calibration_classification"]
    )
    assert result.state.best_value < before
    assert (tmp_path / "last.pt").is_file() and (tmp_path / "best.pt").is_file()
    assert len(result.state.history) == result.state.epoch


def test_best_weights_reproduce_the_best_calibration_loss(tmp_path: Path) -> None:
    train, calibration = _loaders()
    model = _model()
    result = fit(
        model,
        train,
        calibration,
        CONFIG,
        pos_weight=1.0,
        checkpoint_dir=tmp_path,
        device=CPU,
    )
    fresh = _model()
    epoch = load_model_weights(tmp_path / "best.pt", fresh)
    assert epoch == result.state.best_epoch
    reloaded = evaluate(fresh, calibration, CONFIG, 1.0, CPU).classification_loss
    assert reloaded == pytest.approx(result.state.best_value, abs=1e-6)


def test_early_stopping_ends_after_patience_epochs_without_improvement(
    tmp_path: Path,
) -> None:
    train, calibration = _loaders()
    frozen = replace(
        CONFIG, learning_rate=0.0, max_epochs=10, early_stopping_patience=2
    )
    result = fit(
        _model(),
        train,
        calibration,
        frozen,
        pos_weight=1.0,
        checkpoint_dir=tmp_path,
        device=CPU,
    )
    # lr 0: epoch 0 sets the best, epochs 1 and 2 cannot beat it -> stop after epoch 2
    assert result.stopped_early
    assert result.state.epoch == 3
    assert result.state.best_epoch == 0


def test_resume_from_mid_epoch_matches_an_uninterrupted_run(tmp_path: Path) -> None:
    train, calibration = _loaders()
    straight = _model()
    fit(
        straight,
        train,
        calibration,
        CONFIG,
        pos_weight=2.0,
        checkpoint_dir=tmp_path / "a",
        device=CPU,
    )

    train, calibration = _loaders()
    interrupted = _model()
    first = fit(
        interrupted,
        train,
        calibration,
        CONFIG,
        pos_weight=2.0,
        checkpoint_dir=tmp_path / "b",
        device=CPU,
        stop_after_steps=3,
    )
    assert first.interrupted
    assert (first.state.epoch, first.state.step_in_epoch) == (0, 3)  # 4 steps per epoch

    train, calibration = _loaders()
    resumed = _model()
    second = fit(
        resumed,
        train,
        calibration,
        CONFIG,
        pos_weight=2.0,
        checkpoint_dir=tmp_path / "b",
        device=CPU,
    )
    assert not second.interrupted
    for got, want in zip(_params(resumed), _params(straight), strict=True):
        assert torch.equal(got, want)


def test_resumed_history_matches_the_uninterrupted_history_except_timing(
    tmp_path: Path,
) -> None:
    train, calibration = _loaders()
    straight = fit(
        _model(),
        train,
        calibration,
        CONFIG,
        pos_weight=2.0,
        checkpoint_dir=tmp_path / "a",
        device=CPU,
    )
    train, calibration = _loaders()
    fit(
        _model(),
        train,
        calibration,
        CONFIG,
        pos_weight=2.0,
        checkpoint_dir=tmp_path / "b",
        device=CPU,
        stop_after_steps=6,
    )
    train, calibration = _loaders()
    resumed = fit(
        _model(),
        train,
        calibration,
        CONFIG,
        pos_weight=2.0,
        checkpoint_dir=tmp_path / "b",
        device=CPU,
    )
    assert len(resumed.state.history) == len(straight.state.history)
    for a, b in zip(resumed.state.history, straight.state.history, strict=True):
        for key in a:
            if key != "seconds":
                assert a[key] == b[key], key


def test_checkpoint_save_load_forward_is_numerically_identical(tmp_path: Path) -> None:
    model = _model().eval()
    optimizer = make_optimizer(model, CONFIG)
    image = torch.randn(1, 4, SIZE, SIZE, SIZE)
    with torch.no_grad():
        before = model(image).logit.clone()
    digest = save_checkpoint(
        tmp_path / "c.pt",
        model=model,
        optimizer=optimizer,
        scaler=None,
        state=TrainState(epoch=4),
    )
    assert digest == file_sha256(tmp_path / "c.pt")
    other = IDHNet(SMALL).eval()
    state = load_checkpoint(
        tmp_path / "c.pt",
        model=other,
        optimizer=make_optimizer(other, CONFIG),
        scaler=None,
        expected_sha256=digest,
    )
    with torch.no_grad():
        after = other(image).logit
    assert torch.equal(before, after)
    assert state.epoch == 4


def test_checkpoint_with_the_wrong_digest_is_refused(tmp_path: Path) -> None:
    model = _model()
    optimizer = make_optimizer(model, CONFIG)
    save_checkpoint(
        tmp_path / "c.pt",
        model=model,
        optimizer=optimizer,
        scaler=None,
        state=TrainState(),
    )
    with pytest.raises(ValueError, match="SHA-256"):
        load_checkpoint(
            tmp_path / "c.pt",
            model=model,
            optimizer=optimizer,
            scaler=None,
            expected_sha256="0" * 64,
        )


def test_a_save_leaves_no_temporary_file(tmp_path: Path) -> None:
    model = _model()
    save_checkpoint(
        tmp_path / "c.pt",
        model=model,
        optimizer=make_optimizer(model, CONFIG),
        scaler=None,
        state=TrainState(),
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == ["c.pt"]


def test_bf16_autocast_stays_close_to_full_precision() -> None:
    _, calibration = _loaders()
    model = _model()
    full = evaluate(model, calibration, replace(CONFIG, amp="off"), 1.0, CPU)
    mixed = evaluate(model, calibration, replace(CONFIG, amp="bf16"), 1.0, CPU)
    assert mixed.classification_loss == pytest.approx(
        full.classification_loss, abs=0.05
    )


def test_accumulation_takes_one_optimizer_step_per_group_of_batches(
    tmp_path: Path,
) -> None:
    train, calibration = _loaders()
    config = replace(CONFIG, max_epochs=1)
    result = fit(
        _model(),
        train,
        calibration,
        config,
        pos_weight=1.0,
        checkpoint_dir=tmp_path,
        device=CPU,
    )
    assert result.state.global_step == 4  # 8 batches / 2 per step


def test_a_short_last_group_still_takes_a_step(tmp_path: Path) -> None:
    train = _Loader(_Dataset(5, 1), 5, True)
    _, calibration = _loaders()
    result = fit(
        _model(),
        train,
        calibration,
        replace(CONFIG, max_epochs=1),
        pos_weight=1.0,
        checkpoint_dir=tmp_path,
        device=CPU,
    )
    assert result.state.global_step == 3  # groups of 2, 2, 1


def test_yaml_config_equals_the_dataclass_defaults() -> None:
    raw = OmegaConf.to_container(OmegaConf.load(TRAINING_YAML), resolve=True)
    assert isinstance(raw, dict)
    assert TrainConfig(**raw) == TrainConfig()  # type: ignore[arg-type]

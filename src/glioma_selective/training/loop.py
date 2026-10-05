"""Training loop: AMP, gradient accumulation, checkpointing, early stopping (T06.6).

Model selection reads the UTSW calibration split only (SI-08). The stopping signal is
the class-balanced classification loss on that split (D-039). The loop never sees a
test or external cohort.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterable, Iterator, Mapping
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import torch

from glioma_selective.models.segresnet import IDHNet
from glioma_selective.training.checkpoint import (
    TrainState,
    load_checkpoint,
    save_checkpoint,
    save_model_weights,
)
from glioma_selective.training.determinism import deterministic_mode
from glioma_selective.training.losses import joint_loss
from glioma_selective.training.metrics import binary_auroc, hard_dice
from glioma_selective.training.modality_dropout import apply_modality_dropout

__all__ = [
    "EvalResult",
    "FitResult",
    "TrainConfig",
    "evaluate",
    "fit",
    "make_optimizer",
    "make_scaler",
]

LOGGER = logging.getLogger(__name__)
AmpMode = Literal["off", "bf16", "fp16"]
Batch = Mapping[str, Any]


@dataclass(frozen=True)
class TrainConfig:
    """Every value here mirrors ``configs/training/base.yaml``."""

    seed: int = 0
    max_epochs: int = 300
    batch_size: int = 2
    accumulation_steps: int = 4
    learning_rate: float = 3.0e-4
    weight_decay: float = 1.0e-4
    grad_clip_norm: float = 1.0
    amp: AmpMode = "bf16"
    seg_weight: float = 1.0
    dice_smooth: float = 1.0
    early_stopping_patience: int = 30
    early_stopping_min_delta: float = 0.0
    checkpoint_every_steps: int = 0
    deterministic: bool = True
    modality_dropout: bool = False
    modality_dropout_keep_all_probability: float = 0.5

    def __post_init__(self) -> None:
        if self.accumulation_steps < 1 or self.max_epochs < 1:
            raise ValueError("accumulation_steps and max_epochs must be at least 1")
        if self.amp not in ("off", "bf16", "fp16"):
            raise ValueError(f"unknown amp mode: {self.amp}")


@dataclass(frozen=True)
class EvalResult:
    """Losses, AUROC and hard Dice over one loader, plus the per-patient outputs."""

    loss: float
    classification_loss: float
    segmentation_loss: float
    auroc: float
    dice: tuple[float, ...]
    logits: np.ndarray
    labels: np.ndarray


@dataclass(frozen=True)
class FitResult:
    """Where a call to ``fit`` ended."""

    state: TrainState
    stopped_early: bool
    interrupted: bool


def make_optimizer(
    model: torch.nn.Module, config: TrainConfig
) -> torch.optim.Optimizer:
    """AdamW with the configured learning rate and weight decay."""
    return torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )


def make_scaler(
    config: TrainConfig, device: torch.device
) -> torch.amp.GradScaler | None:
    """A GradScaler only for fp16 on CUDA; bf16 and fp32 need none."""
    if config.amp == "fp16" and device.type == "cuda":
        return torch.amp.GradScaler("cuda")
    return None


def _autocast(
    config: TrainConfig, device: torch.device
) -> AbstractContextManager[None]:
    if config.amp == "off":
        return nullcontext()
    dtype = torch.bfloat16 if config.amp == "bf16" else torch.float16
    return cast(
        AbstractContextManager[None],
        torch.autocast(device_type=device.type, dtype=dtype),
    )


def _to_device(batch: Batch, device: torch.device) -> dict[str, torch.Tensor]:
    return {
        key: batch[key].to(device, non_blocking=True)
        for key in ("image", "seg", "has_seg", "label")
    }


def _set_epoch(loader: Iterable[Batch], epoch: int) -> None:
    dataset = getattr(loader, "dataset", None)
    setter = getattr(dataset, "set_epoch", None)
    if callable(setter):
        setter(epoch)


def _batch_loss(
    model: IDHNet,
    tensors: Mapping[str, torch.Tensor],
    config: TrainConfig,
    pos_weight: float,
    device: torch.device,
) -> tuple[Any, Any]:
    with _autocast(config, device):
        output = model(tensors["image"])
    # Losses in float32: autocast covers the network, not the reductions.
    logit = output.logit.float()
    seg_logits = None if output.seg_logits is None else output.seg_logits.float()
    losses = joint_loss(
        logit,
        seg_logits,
        tensors["label"],
        tensors["seg"],
        tensors["has_seg"],
        pos_weight=pos_weight,
        seg_weight=config.seg_weight,
        dice_smooth=config.dice_smooth,
    )
    return losses, output


def _train_epoch(
    model: IDHNet,
    loader: Iterable[Batch],
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler | None,
    config: TrainConfig,
    pos_weight: float,
    device: torch.device,
    state: TrainState,
    save_now: Any,
    stop_after_steps: int | None,
) -> tuple[dict[str, float], bool]:
    """One pass; returns the epoch means and whether it was interrupted."""
    model.train()
    batches: Iterator[Batch] = iter(loader)
    skip = state.step_in_epoch * config.accumulation_steps
    if skip:
        batches = islice(batches, skip, None)  # resume: consume what was already done
    if not state.epoch_sums:
        state.epoch_sums = {"loss": 0.0, "classification": 0.0, "segmentation": 0.0}
    sums = (
        state.epoch_sums
    )  # carried in the checkpoint so a resumed epoch averages all of it
    pending = 0
    optimizer.zero_grad(set_to_none=True)
    for batch in batches:
        tensors = _to_device(batch, device)
        if config.modality_dropout:
            # The stream depends only on (seed, epoch, batch index), so a resumed
            # run draws the same channels as an uninterrupted one.
            dropout_rng = np.random.default_rng(
                np.random.SeedSequence(
                    [config.seed, state.epoch, state.epoch_batches, 41]
                )
            )
            tensors["image"] = apply_modality_dropout(
                tensors["image"],
                dropout_rng,
                config.modality_dropout_keep_all_probability,
            )
        losses, _ = _batch_loss(model, tensors, config, pos_weight, device)
        scaled = losses.total / config.accumulation_steps
        (scaler.scale(scaled) if scaler is not None else scaled).backward()
        sums["loss"] += float(losses.total.detach())
        sums["classification"] += float(losses.classification.detach())
        sums["segmentation"] += float(losses.segmentation.detach())
        state.epoch_batches += 1
        pending += 1
        if pending < config.accumulation_steps:
            continue
        _optimizer_step(model, optimizer, scaler, config)
        pending = 0
        state.step_in_epoch += 1
        state.global_step += 1
        every = config.checkpoint_every_steps
        if every and state.global_step % every == 0:
            save_now()
        if stop_after_steps is not None and state.global_step >= stop_after_steps:
            save_now()
            return _means(sums, state.epoch_batches), True
    if pending:
        _optimizer_step(model, optimizer, scaler, config)
        state.step_in_epoch += 1
        state.global_step += 1
    return _means(sums, state.epoch_batches), False


def _optimizer_step(
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler | None,
    config: TrainConfig,
) -> None:
    if scaler is not None:
        scaler.unscale_(optimizer)
    if config.grad_clip_norm > 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip_norm)
    if scaler is not None:
        scaler.step(optimizer)
        scaler.update()
    else:
        optimizer.step()
    optimizer.zero_grad(set_to_none=True)


def _means(sums: Mapping[str, float], count: int) -> dict[str, float]:
    return {key: value / max(count, 1) for key, value in sums.items()}


@torch.no_grad()
def evaluate(
    model: IDHNet,
    loader: Iterable[Batch],
    config: TrainConfig,
    pos_weight: float,
    device: torch.device,
) -> EvalResult:
    """Run the model over a loader without gradients; losses are means over batches."""
    model.eval()
    totals = {"loss": 0.0, "classification": 0.0, "segmentation": 0.0}
    logits: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    dice_sum: torch.Tensor | None = None
    dice_count = 0
    count = 0
    for batch in loader:
        tensors = _to_device(batch, device)
        losses, output = _batch_loss(model, tensors, config, pos_weight, device)
        totals["loss"] += float(losses.total)
        totals["classification"] += float(losses.classification)
        totals["segmentation"] += float(losses.segmentation)
        count += 1
        logits.append(output.logit.float().cpu().numpy())
        labels.append(tensors["label"].cpu().numpy())
        if output.seg_logits is not None and bool(tensors["has_seg"].any()):
            per_channel = hard_dice(
                output.seg_logits.float().cpu(),
                tensors["seg"].cpu(),
                tensors["has_seg"].cpu(),
            )
            weight = int(tensors["has_seg"].sum())
            dice_sum = (
                per_channel * weight
                if dice_sum is None
                else dice_sum + per_channel * weight
            )
            dice_count += weight
    all_logits = np.concatenate(logits)
    all_labels = np.concatenate(labels)
    dice = (
        tuple(float(v) for v in (dice_sum / dice_count)) if dice_sum is not None else ()
    )
    means = _means(totals, count)
    return EvalResult(
        loss=means["loss"],
        classification_loss=means["classification"],
        segmentation_loss=means["segmentation"],
        auroc=binary_auroc(all_logits, all_labels),
        dice=dice,
        logits=all_logits,
        labels=all_labels,
    )


def fit(
    model: IDHNet,
    train_loader: Iterable[Batch],
    calibration_loader: Iterable[Batch],
    config: TrainConfig,
    *,
    pos_weight: float,
    checkpoint_dir: Path,
    device: torch.device,
    resume: bool = True,
    stop_after_steps: int | None = None,
) -> FitResult:
    """Run ``_fit`` under deterministic algorithms unless the config turns them off.

    Deterministic mode makes a resumed run identical to an uninterrupted one on
    CUDA as well as on CPU (D-040); ``deterministic: false`` is for speed tests.
    """
    with deterministic_mode() if config.deterministic else nullcontext():
        return _fit(
            model,
            train_loader,
            calibration_loader,
            config,
            pos_weight=pos_weight,
            checkpoint_dir=checkpoint_dir,
            device=device,
            resume=resume,
            stop_after_steps=stop_after_steps,
        )


def _fit(
    model: IDHNet,
    train_loader: Iterable[Batch],
    calibration_loader: Iterable[Batch],
    config: TrainConfig,
    *,
    pos_weight: float,
    checkpoint_dir: Path,
    device: torch.device,
    resume: bool = True,
    stop_after_steps: int | None = None,
) -> FitResult:
    """Train until the calibration-split loss stops improving, or ``max_epochs``.

    ``last.pt`` is written at every epoch end (and every ``checkpoint_every_steps``
    optimizer steps); ``best.pt`` holds the weights of the best calibration-split
    classification loss. With ``resume`` a run continues from ``last.pt`` exactly,
    including mid-epoch. ``stop_after_steps`` saves and returns after that many
    optimizer steps in total; the authorization harness uses it for the
    save-and-resume equivalence check.
    """
    model.to(device)
    optimizer = make_optimizer(model, config)
    scaler = make_scaler(config, device)
    last_path = checkpoint_dir / "last.pt"
    best_path = checkpoint_dir / "best.pt"
    state = TrainState()
    if resume and last_path.is_file():
        state = load_checkpoint(
            last_path, model=model, optimizer=optimizer, scaler=scaler
        )
        LOGGER.info("resumed at epoch %d step %d", state.epoch, state.step_in_epoch)
    else:
        torch.manual_seed(config.seed)

    def save_now() -> None:
        save_checkpoint(
            last_path, model=model, optimizer=optimizer, scaler=scaler, state=state
        )

    stopped_early = False
    while state.epoch < config.max_epochs and not state.finished:
        started = time.monotonic()
        _set_epoch(train_loader, state.epoch)
        train_means, interrupted = _train_epoch(
            model,
            train_loader,
            optimizer,
            scaler,
            config,
            pos_weight,
            device,
            state,
            save_now,
            stop_after_steps,
        )
        if interrupted:
            return FitResult(state=state, stopped_early=False, interrupted=True)
        calibration = evaluate(model, calibration_loader, config, pos_weight, device)
        improved = calibration.classification_loss < (
            state.best_value - config.early_stopping_min_delta
        )
        if improved:
            state.best_value = calibration.classification_loss
            state.best_epoch = state.epoch
            state.epochs_without_improvement = 0
            save_model_weights(best_path, model, epoch=state.epoch)
        else:
            state.epochs_without_improvement += 1
        state.history.append(
            {
                "epoch": float(state.epoch),
                "train_loss": train_means["loss"],
                "train_classification": train_means["classification"],
                "train_segmentation": train_means["segmentation"],
                "calibration_classification": calibration.classification_loss,
                "calibration_segmentation": calibration.segmentation_loss,
                "calibration_auroc": calibration.auroc,
                "seconds": time.monotonic() - started,
            }
        )
        LOGGER.info(
            "epoch %d train %.4f calibration %.4f auroc %.3f%s",
            state.epoch,
            train_means["loss"],
            calibration.classification_loss,
            calibration.auroc,
            " *" if improved else "",
        )
        state.epoch += 1
        state.step_in_epoch = 0
        state.epoch_sums = {}
        state.epoch_batches = 0
        if state.epochs_without_improvement >= config.early_stopping_patience:
            stopped_early = True
            state.finished = True
        save_now()
    state.finished = True
    save_now()
    return FitResult(state=state, stopped_early=stopped_early, interrupted=False)

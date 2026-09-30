"""Atomic checkpoints that resume a run exactly (T06.6).

``last.pt`` holds everything needed to continue: model, optimizer, AMP scaler, the
loop position, the early-stopping state, the history so far, and the global RNG
states. ``best.pt`` holds the best-on-calibration-loss model weights only.
"""

from __future__ import annotations

import hashlib
import os
import random
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import torch

__all__ = [
    "TrainState",
    "file_sha256",
    "load_checkpoint",
    "load_model_weights",
    "save_checkpoint",
    "save_model_weights",
]

CHECKPOINT_VERSION = 1


@dataclass
class TrainState:
    """Where a run is: the epoch in progress and the optimizer steps done in it."""

    epoch: int = 0
    step_in_epoch: int = 0
    global_step: int = 0
    best_value: float = float("inf")
    best_epoch: int = -1
    epochs_without_improvement: int = 0
    finished: bool = False
    epoch_sums: dict[str, float] = field(default_factory=dict)
    epoch_batches: int = 0
    history: list[dict[str, float]] = field(default_factory=list)


def file_sha256(path: Path) -> str:
    """SHA-256 of a file's bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_save(payload: dict[str, Any], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(descriptor)
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return file_sha256(path)


def save_checkpoint(
    path: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler | None,
    state: TrainState,
) -> str:
    """Write the full training state atomically and return the file's SHA-256."""
    payload: dict[str, Any] = {
        "version": CHECKPOINT_VERSION,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scaler": scaler.state_dict() if scaler is not None else None,
        "state": asdict(state),
        "rng_torch": torch.get_rng_state(),
        "rng_cuda": torch.cuda.get_rng_state_all()
        if torch.cuda.is_available()
        else None,
        "rng_python": random.getstate(),
    }
    return _atomic_save(payload, path)


def load_checkpoint(
    path: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler | None,
    expected_sha256: str | None = None,
) -> TrainState:
    """Restore a full training state in place; a wrong digest is an error."""
    if expected_sha256 is not None and file_sha256(path) != expected_sha256:
        raise ValueError("checkpoint does not match the expected SHA-256")
    payload = torch.load(path, map_location="cpu", weights_only=True)
    if payload["version"] != CHECKPOINT_VERSION:
        raise ValueError("unsupported checkpoint version")
    model.load_state_dict(payload["model"])
    optimizer.load_state_dict(payload["optimizer"])
    if scaler is not None and payload["scaler"] is not None:
        scaler.load_state_dict(payload["scaler"])
    torch.set_rng_state(payload["rng_torch"])
    if payload["rng_cuda"] is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(payload["rng_cuda"])
    random.setstate(payload["rng_python"])
    return TrainState(**payload["state"])


def save_model_weights(path: Path, model: torch.nn.Module, *, epoch: int) -> str:
    """Write model weights only (the best checkpoint) and return the SHA-256."""
    return _atomic_save(
        {"version": CHECKPOINT_VERSION, "model": model.state_dict(), "epoch": epoch},
        path,
    )


def load_model_weights(path: Path, model: torch.nn.Module) -> int:
    """Load weights from ``save_model_weights``; returns the epoch they came from."""
    payload = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(payload["model"])
    return int(payload["epoch"])

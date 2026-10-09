"""Freeze deterministic and head-only MC-dropout predictions for fixed UTSW splits."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import nn

from glioma_selective.training.determinism import deterministic_mode

LOGGER = logging.getLogger("freeze_mc_dropout")
_SPLITS = (("calibration", "utsw_calibration"), ("internal_test", "utsw_internal_test"))


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _current_git_sha() -> str:
    from scripts.freeze_predictions import REPOSITORY_ROOT

    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _load_record(run_id: str) -> tuple[Path, dict[str, Any]]:
    from glioma_selective.tracking import run_record

    path = run_record._record_path(run_id)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load run record for run {run_id}") from error
    if not isinstance(record, dict) or record.get("run_id") != run_id:
        raise ValueError("run record does not match its run ID")
    return path.parent, cast(dict[str, Any], record)


def _check_run(
    record: Mapping[str, Any], checkpoint_path: Path, *, allow_sha_mismatch: bool
) -> tuple[str, str, str]:
    from glioma_selective.training.checkpoint import file_sha256

    if record.get("status") != "completed":
        raise ValueError("MC-dropout freezing requires status=completed")
    if record.get("git_dirty") is not False:
        raise ValueError("MC-dropout freezing requires record git_dirty=false")
    expected = record.get("checkpoint_hash")
    if not isinstance(expected, str) or not expected:
        raise ValueError("run record has no checkpoint_hash")
    if file_sha256(checkpoint_path) != expected:
        raise ValueError(
            "best.pt SHA-256 does not match the run record checkpoint_hash"
        )
    record_sha = record.get("git_sha")
    if not isinstance(record_sha, str) or not record_sha:
        raise ValueError("run record has no git_sha")
    current_sha = _current_git_sha()
    if current_sha != record_sha:
        message = (
            f"current git SHA {current_sha} does not match run git SHA {record_sha}"
        )
        if not allow_sha_mismatch:
            raise ValueError(message)
        LOGGER.warning("Allowing SHA mismatch: %s", message)
    return current_sha, record_sha, expected


def _resolve_device(requested: str) -> torch.device:
    if requested not in ("cpu", "cuda", "auto"):
        raise ValueError("device must be cpu, cuda, or auto")
    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is unavailable")
    return torch.device(
        "cuda"
        if requested == "auto" and torch.cuda.is_available()
        else ("cpu" if requested == "auto" else requested)
    )


def _scalar_logit(output: Any) -> torch.Tensor:
    logits = output.logit
    if not isinstance(logits, torch.Tensor):
        raise ValueError("model output logit must be a tensor")
    if logits.ndim == 1:
        return logits
    if logits.ndim == 2 and logits.shape[1] == 1:
        return logits[:, 0]
    raise ValueError("model output logit must have shape (B,) or (B, 1)")


def _score_split(
    model: nn.Module,
    dataset: Any,
    *,
    device: torch.device,
    batch_size: int,
    passes: int,
    seed: int,
    cohort: str,
) -> list[dict[str, Any]]:
    from glioma_selective.uncertainty.mc_dropout import mc_dropout_probabilities

    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    generator = torch.Generator(device=device).manual_seed(seed)
    rows: list[dict[str, Any]] = []
    model.to(device)
    model.eval()
    with deterministic_mode(), torch.no_grad():
        for offset in range(0, len(dataset), batch_size):
            samples = [
                dataset[i]
                for i in range(offset, min(offset + batch_size, len(dataset)))
            ]
            image = torch.stack(
                [cast(torch.Tensor, sample["image"]) for sample in samples]
            ).to(device)
            if image.ndim != 5 or image.shape[1] != 4:
                raise ValueError("prediction dataset must provide four MRI sequences")
            logits = (
                _scalar_logit(model(image))
                .detach()
                .to(device="cpu", dtype=torch.float32)
            )
            probabilities = torch.sigmoid(logits.to(torch.float64)).to(torch.float32)
            mc = (
                mc_dropout_probabilities(
                    cast(Any, model), image, passes=passes, generator=generator
                )
                .detach()
                .to(device="cpu", dtype=torch.float32)
            )
            for sample, logit, probability, draws in zip(
                samples,
                logits.tolist(),
                probabilities.tolist(),
                mc.tolist(),
                strict=True,
            ):
                rows.append(
                    {
                        "patient_id": cast(str, sample["patient_id"]),
                        "cohort": cohort,
                        "modality_condition": "full",
                        "p_hat": np.float32(probability),
                        "logit": np.float32(logit),
                        "label": int(cast(torch.Tensor, sample["label"]).item()),
                        "mc_dropout_samples": [np.float32(value) for value in draws],
                    }
                )
    return rows


def freeze_mc_dropout(
    run_id: str,
    *,
    device: str = "cpu",
    passes: int = 30,
    seed: int = 0,
    batch_size: int = 1,
    allow_sha_mismatch: bool = False,
) -> Path:
    """Freeze head-only MC probabilities with deterministic split-local RNGs.

    For batch sizes above one, generator draws are consumed batch by batch, so
    sample values depend on batch size. The default batch size is one.
    """
    if passes < 1:
        raise ValueError("passes must be positive")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    from omegaconf import OmegaConf
    from scripts.freeze_predictions import REPOSITORY_ROOT

    from glioma_selective.data.dataset import IDHDataset, load_split_patient_ids
    from glioma_selective.models.segresnet import ModelConfig, build_model
    from glioma_selective.tracking.predictions import write_prediction_artifact
    from glioma_selective.training.checkpoint import load_model_weights
    from glioma_selective.training.run import _build_datasets

    run_dir, record = _load_record(run_id)
    artifact_path = run_dir / "mc_dropout.parquet"
    meta_path = run_dir / "mc_dropout_meta.json"
    if any(
        path.exists()
        for path in (
            artifact_path,
            artifact_path.with_name(artifact_path.name + ".sha256"),
            meta_path,
            meta_path.with_name(meta_path.name + ".sha256"),
        )
    ):
        raise FileExistsError("MC-dropout artifact or metadata already exists")
    checkpoint_path = run_dir / "checkpoints" / "best.pt"
    current_sha, record_sha, checkpoint_hash = _check_run(
        record, checkpoint_path, allow_sha_mismatch=allow_sha_mismatch
    )
    resolved_device = _resolve_device(device)
    config_path = REPOSITORY_ROOT / "configs" / "model" / "base.yaml"
    config_values = OmegaConf.to_container(OmegaConf.load(config_path), resolve=True)
    if not isinstance(config_values, Mapping):
        raise ValueError("base model configuration must be a mapping")
    model = build_model(
        ModelConfig.from_mapping(cast(Mapping[str, Any], config_values))
    )
    load_model_weights(checkpoint_path, model)
    model.to(resolved_device)

    _train_dataset, calibration_dataset, _stats_path = _build_datasets(
        int(record["seed"])
    )
    internal_dataset = IDHDataset(
        load_split_patient_ids("internal_test"),
        stats=calibration_dataset.stats,
        seed=int(record["seed"]),
        augment=False,
        zero_channels=(),
        storage=calibration_dataset.storage,
    )
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for index, (split, cohort) in enumerate(_SPLITS):
        dataset = calibration_dataset if split == "calibration" else internal_dataset
        split_rows = _score_split(
            model,
            dataset,
            device=resolved_device,
            batch_size=batch_size,
            passes=passes,
            seed=seed + index,
            cohort=cohort,
        )
        counts[cohort] = len(split_rows)
        rows.extend(split_rows)

    write_prediction_artifact(
        rows,
        artifact_path,
        run_id=run_id,
        git_sha=current_sha,
        checkpoint_hash=checkpoint_hash,
        record_git_sha=record_sha if record_sha != current_sha else None,
    )
    document = {
        "run_id": run_id,
        "checkpoint_hash": checkpoint_hash,
        "passes": passes,
        "seed": seed,
        "device": str(resolved_device),
    }
    payload = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    _write_exclusive(meta_path, payload)
    _write_exclusive(
        meta_path.with_name(meta_path.name + ".sha256"),
        f"{digest}  {meta_path.name}\n".encode("ascii"),
    )
    print(f"device={resolved_device}")
    for cohort, count in counts.items():
        print(f"rows[{cohort}]={count}")
    return artifact_path

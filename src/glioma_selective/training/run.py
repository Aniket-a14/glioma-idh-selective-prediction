"""One real training run: authorization, run record, fit, and the final record update.

Used by ``scripts/train.py`` for the pilot (T06.9) and for R1/R2 (T06.10). The run
trains on the frozen UTSW training split and stops on the calibration split only
(SI-08). The internal test split is not read here.
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import torch

from glioma_selective.models.segresnet import ModelConfig, build_model
from glioma_selective.tracking.run_record import (
    assert_launch_ready,
    build_run_record,
    update_run_record,
    write_run_record,
)
from glioma_selective.training.authorization import (
    assert_authorized,
    base_config_sha256,
)
from glioma_selective.training.checkpoint import file_sha256
from glioma_selective.training.loop import FitResult, TrainConfig, fit
from glioma_selective.training.losses import pos_weight_from_counts
from glioma_selective.utils import paths

__all__ = ["RunSpec", "training_config_for", "train_run"]

LOGGER = logging.getLogger(__name__)
NOT_APPLICABLE_CALIBRATION = "not_applicable: Phase 06 baseline is uncalibrated"
NOT_APPLICABLE_THRESHOLDS = "not_applicable: Phase 06 baseline is always-predict"
PREDICTIONS_PENDING = "not_applicable: frozen by T06.11 after training"


@dataclass(frozen=True)
class RunSpec:
    """What differs between runs; everything else comes from the fixed configs."""

    label: str
    seed: int = 0
    modality_dropout: bool = False
    max_epochs: int | None = None
    num_workers: int = 4
    resume_run_id: str | None = None


def training_config_for(spec: RunSpec) -> TrainConfig:
    """The base training config with this run's seed, dropout and epoch cap."""
    config = replace(
        TrainConfig(), seed=spec.seed, modality_dropout=spec.modality_dropout
    )
    if spec.max_epochs is not None:
        config = replace(config, max_epochs=spec.max_epochs)
    return config


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _record_failure(run_id: str, error: BaseException) -> None:
    update_run_record(
        run_id,
        status="failed",
        failure_reason=repr(error)[:500],
        end_time_utc=_utc_now(),
    )


def _record_completion(
    run_id: str, result: FitResult, run_dir: Path, log_path: Path
) -> None:
    best = result.state.history[result.state.best_epoch]
    update_run_record(
        run_id,
        status="completed",
        end_time_utc=_utc_now(),
        checkpoint_hash=file_sha256(run_dir / "checkpoints" / "best.pt"),
        training_history=result.state.history,
        predictions_path=PREDICTIONS_PENDING,
        calibration_params=NOT_APPLICABLE_CALIBRATION,
        selective_thresholds=NOT_APPLICABLE_THRESHOLDS,
        metrics={
            "best_epoch": result.state.best_epoch,
            "stopped_early": result.stopped_early,
            "calibration_classification_loss": result.state.best_value,
            "calibration_auroc_at_best_epoch": best["calibration_auroc"],
        },
        log_path=str(log_path),
    )


def _git_head() -> str:
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _build_datasets(seed: int) -> tuple[Any, Any, Any]:
    from glioma_selective.data.dataset import IDHDataset, load_split_patient_ids
    from glioma_selective.preprocessing.normalize import load_normalization_stats

    manifests = paths.manifests_dir()
    stats_path = manifests / "normalization_stats.json"
    expected = Path(str(stats_path) + ".sha256").read_text(encoding="ascii").split()[0]
    stats = load_normalization_stats(stats_path, expected_sha256=expected)
    storage = paths.processed_data_dir()
    train = IDHDataset(
        load_split_patient_ids("train"),
        stats=stats,
        seed=seed,
        augment=True,
        storage=storage,
    )
    calibration = IDHDataset(
        load_split_patient_ids("calibration"),
        stats=stats,
        seed=seed,
        augment=False,
        storage=storage,
    )
    return train, calibration, stats_path


def train_run(
    spec: RunSpec,
    *,
    authorization_report: Path,
    device: torch.device,
) -> tuple[str, FitResult]:
    """Train one model; returns the run id and the fit result."""
    from glioma_selective.data.dataset import make_loader

    git_sha = _git_head()
    assert_authorized(
        authorization_report, git_sha=git_sha, config_sha256=base_config_sha256()
    )
    model_config = ModelConfig()
    train_config = training_config_for(spec)
    train_dataset, calibration_dataset, stats_path = _build_datasets(spec.seed)
    labels = train_dataset.labels
    n_positive = int(sum(labels))
    pos_weight = pos_weight_from_counts(len(labels) - n_positive, n_positive)

    manifests = paths.manifests_dir()
    config = {
        "model": asdict(model_config),
        "training": asdict(train_config),
        "run": {"label": spec.label, "pos_weight": pos_weight},
    }
    if spec.resume_run_id is None:
        record = build_run_record(
            dataset_manifest_hash=_sha256(manifests / "preprocessing_outputs.json"),
            exclusion_list_hash=_sha256(manifests / "exclusion_manifest_post_qc.json"),
            config=config,
            seed=spec.seed,
            preprocessing_version="phase06-frozen-zscore-and-2mm-whole-brain",
            parameter_hash=hashlib.sha256(
                json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            normalization_stats_sha256=_sha256(stats_path),
            repo_root=Path(__file__).resolve().parents[3],
        )
        assert_launch_ready(record)
        write_run_record(record)
        run_id = record.run_id
        update_run_record(run_id, status="running")
    else:
        run_id = spec.resume_run_id
        saved = json.loads(
            (paths.experiments_dir() / run_id / "record.json").read_text("utf-8")
        )
        if saved["git_sha"] != git_sha:
            raise ValueError("cannot resume a run on a different commit")

    run_dir = paths.experiments_dir() / run_id
    log_path = run_dir / "train.log"
    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    try:
        model = build_model(model_config)
        train_loader = make_loader(
            train_dataset,
            batch_size=train_config.batch_size,
            shuffle=True,
            seed=spec.seed,
            num_workers=spec.num_workers,
        )
        calibration_loader = make_loader(
            calibration_dataset,
            batch_size=train_config.batch_size,
            shuffle=False,
            seed=spec.seed,
            num_workers=spec.num_workers,
        )
        result = fit(
            model,
            train_loader,
            calibration_loader,
            train_config,
            pos_weight=pos_weight,
            checkpoint_dir=run_dir / "checkpoints",
            device=device,
            resume=spec.resume_run_id is not None,
        )
    except BaseException as error:
        _record_failure(run_id, error)
        raise
    finally:
        logging.getLogger().removeHandler(handler)
        handler.close()

    _record_completion(run_id, result, run_dir, log_path)
    return run_id, result

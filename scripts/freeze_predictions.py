#!/usr/bin/env python3
"""Freeze calibration and internal-test UTSW predictions for a completed run."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for import_root in (REPOSITORY_ROOT, SOURCE_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

LOGGER = logging.getLogger("freeze_predictions")
_SPLITS = (("calibration", "utsw_calibration"), ("internal_test", "utsw_internal_test"))


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="completed run ULID")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument(
        "--allow-sha-mismatch",
        action="store_true",
        help="score with this tree and record both code SHAs in artifact metadata",
    )
    return parser


def _current_git_sha() -> str:
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
        raise ValueError("prediction freezing requires status=completed")
    if record.get("git_dirty") is not False:
        raise ValueError("prediction freezing requires record git_dirty=false")
    expected_checkpoint = record.get("checkpoint_hash")
    if not isinstance(expected_checkpoint, str) or not expected_checkpoint:
        raise ValueError("run record has no checkpoint_hash")
    actual_checkpoint = file_sha256(checkpoint_path)
    if actual_checkpoint != expected_checkpoint:
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
    return current_sha, record_sha, expected_checkpoint


def _resolve_device(requested: str) -> Any:
    import torch

    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is unavailable")
    return torch.device(requested)


def freeze_run(
    run_id: str, *, device: str = "auto", allow_sha_mismatch: bool = False
) -> Path:
    """Validate run provenance, score the two fixed UTSW splits, and freeze parquet."""
    from omegaconf import OmegaConf

    from glioma_selective.data.dataset import IDHDataset, load_split_patient_ids
    from glioma_selective.evaluation.freeze import predict_split_with_dice
    from glioma_selective.models.segresnet import ModelConfig, build_model
    from glioma_selective.tracking.predictions import write_prediction_artifact
    from glioma_selective.tracking.run_record import update_run_record
    from glioma_selective.training.checkpoint import load_model_weights
    from glioma_selective.training.metrics import binary_auroc
    from glioma_selective.training.run import _build_datasets

    run_dir, record = _load_record(run_id)
    dice_path = run_dir / "segmentation_dice.json"
    if any(
        path.exists()
        for path in (
            run_dir / "predictions.parquet",
            run_dir / "predictions.parquet.sha256",
            dice_path,
            dice_path.with_name(dice_path.name + ".sha256"),
        )
    ):
        raise FileExistsError("prediction or segmentation Dice artifact already exists")
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

    # Reuse training's frozen-stat loading and calibration dataset construction.
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
    all_rows: list[dict[str, Any]] = []
    internal_rows: list[dict[str, Any]] = []
    dice_by_split: dict[str, dict[str, Any]] = {}
    batch_size = int(record.get("config", {}).get("training", {}).get("batch_size", 1))
    for split, cohort in _SPLITS:
        dataset = calibration_dataset if split == "calibration" else internal_dataset
        scored, dice = predict_split_with_dice(
            model, dataset, device=resolved_device, batch_size=batch_size
        )
        dice_by_split[split] = dice
        rows = [
            {
                **row,
                "cohort": cohort,
                "modality_condition": "full",
            }
            for row in scored
        ]
        all_rows.extend(rows)
        if split == "internal_test":
            internal_rows = rows

    artifact_path = run_dir / "predictions.parquet"
    write_prediction_artifact(
        all_rows,
        artifact_path,
        run_id=run_id,
        git_sha=current_sha,
        checkpoint_hash=checkpoint_hash,
        record_git_sha=record_sha if record_sha != current_sha else None,
    )
    dice_document = {
        "run_id": run_id,
        "git_sha": current_sha,
        "checkpoint_hash": checkpoint_hash,
        "splits": dice_by_split,
    }
    dice_payload = (
        json.dumps(dice_document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    dice_digest = hashlib.sha256(dice_payload).hexdigest()
    _write_exclusive(dice_path, dice_payload)
    _write_exclusive(
        dice_path.with_name(dice_path.name + ".sha256"),
        f"{dice_digest}  {dice_path.name}\n".encode("ascii"),
    )
    update_run_record(run_id, predictions_path=str(artifact_path))

    counts: dict[str, int] = dict(Counter(row["cohort"] for row in all_rows))
    internal_labels = np.asarray([int(row["label"]) for row in internal_rows])
    internal_scores = np.asarray([float(row["p_hat"]) for row in internal_rows])
    positives = int((internal_labels == 1).sum())
    negatives = int((internal_labels == 0).sum())
    auroc = binary_auroc(internal_scores, internal_labels)
    print(f"artifact_sha256={_artifact_sha256(artifact_path)}")
    for cohort, count in counts.items():
        print(f"rows[{cohort}]={count}")
    # Sanity check for Phase 06 acceptance criterion 6, not a reported result: a
    # reported AUROC needs ECE, Brier, AURC and coverage beside it (SPEC 5.4).
    print(f"internal_test_auroc_sanity_check_only={auroc:.6f}")
    print(f"internal_test_class_counts=positive:{positives},negative:{negatives}")
    for split, dice in dice_by_split.items():
        print(f"{split}_segmentation_dice_mean={dice['mean']}")
    return artifact_path


def _artifact_sha256(path: Path) -> str:
    from glioma_selective.tracking.run_record import sha256_file

    return sha256_file(path)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    freeze_run(
        args.run_id, device=args.device, allow_sha_mismatch=args.allow_sha_mismatch
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

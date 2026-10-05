"""Report Phase 06 internal-test metrics from a frozen prediction artifact."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from glioma_selective.evaluation.calibration_metrics import (
    brier_score,
    expected_calibration_error,
)
from glioma_selective.tracking.predictions import read_prediction_artifact
from glioma_selective.tracking.run_record import sha256_file, update_run_record
from glioma_selective.training.metrics import binary_auroc
from glioma_selective.utils import paths

__all__ = ["average_precision", "bootstrap_intervals", "report_phase06"]

_BOOTSTRAP_ITERATIONS = 2000
_BOOTSTRAP_SEED = 0


def average_precision(scores: np.ndarray, labels: np.ndarray) -> float:
    """Compute non-interpolated average precision, grouping tied thresholds."""
    score = np.asarray(scores, dtype=np.float64)
    target = np.asarray(labels, dtype=np.int64)
    if (
        score.ndim != 1
        or target.ndim != 1
        or score.size != target.size
        or not score.size
    ):
        raise ValueError(
            "scores and labels must be non-empty one-dimensional arrays of equal size"
        )
    if not np.all(np.isfinite(score)) or not np.all(np.isin(target, (0, 1))):
        raise ValueError("scores must be finite and labels must be binary")
    positives = int(target.sum())
    if positives == 0:
        return float("nan")
    order = np.argsort(-score, kind="stable")
    sorted_scores = score[order]
    sorted_target = target[order]
    true_positive = np.cumsum(sorted_target)
    threshold_ends = np.r_[np.flatnonzero(np.diff(sorted_scores)), score.size - 1]
    recall = true_positive[threshold_ends] / positives
    precision = true_positive[threshold_ends] / (threshold_ends + 1)
    previous_recall = np.r_[0.0, recall[:-1]]
    return float(np.sum((recall - previous_recall) * precision))


def bootstrap_intervals(
    scores: np.ndarray,
    labels: np.ndarray,
    *,
    iterations: int = _BOOTSTRAP_ITERATIONS,
    seed: int = _BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Patient-index percentile intervals for AUROC and average precision."""
    score = np.asarray(scores, dtype=np.float64)
    target = np.asarray(labels, dtype=np.int64)
    if (
        score.ndim != 1
        or target.ndim != 1
        or score.size != target.size
        or not score.size
    ):
        raise ValueError(
            "scores and labels must be non-empty one-dimensional arrays of equal size"
        )
    if iterations < 1:
        raise ValueError("iterations must be positive")
    rng = np.random.default_rng(seed)
    auc_values: list[float] = []
    ap_values: list[float] = []
    skipped = 0
    for _ in range(iterations):
        indices = rng.integers(0, score.size, size=score.size)
        sampled_labels = target[indices]
        if np.unique(sampled_labels).size != 2:
            skipped += 1
            continue
        sampled_scores = score[indices]
        auc_values.append(binary_auroc(sampled_scores, sampled_labels))
        ap_values.append(average_precision(sampled_scores, sampled_labels))
    if not auc_values:
        raise ValueError("all bootstrap resamples had only one class")
    auc_ci = np.quantile(auc_values, [0.025, 0.975], method="linear")
    ap_ci = np.quantile(ap_values, [0.025, 0.975], method="linear")
    return {
        "auroc_ci": [float(value) for value in auc_ci],
        "auprc_ci": [float(value) for value in ap_ci],
        "skipped_resamples": skipped,
    }


def criterion_flags(auroc: float, auroc_ci: list[float]) -> dict[str, bool]:
    """Return the Phase 06 point-estimate and CI criterion flags."""
    if len(auroc_ci) != 2:
        raise ValueError("auroc_ci must contain lower and upper bounds")
    point = auroc >= 0.75
    interval = auroc_ci[0] > 0.5
    return {
        "auroc_ge_0.75": point,
        "auroc_ci_excludes_0.5": interval,
        "criterion_6_met": point and interval,
    }


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def report_phase06(run_id: str) -> Path:
    """Validate provenance, report internal-test metrics, and merge run metrics."""
    record_path = paths.experiments_dir() / run_id / "record.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load run record for run {run_id}") from error
    if not isinstance(record, dict) or record.get("run_id") != run_id:
        raise ValueError("run record does not match its run ID")
    if record.get("status") != "completed":
        raise ValueError("Phase 06 reporting requires status=completed")
    run_dir = record_path.parent
    artifact_path = run_dir / "predictions.parquet"
    frame, metadata = read_prediction_artifact(artifact_path)
    if metadata.get("run_id") != run_id:
        raise ValueError("prediction artifact run_id does not match the run record")
    if metadata.get("checkpoint_hash") != record.get("checkpoint_hash"):
        raise ValueError(
            "prediction artifact checkpoint_hash does not match the run record"
        )
    selected = frame.loc[
        (frame["cohort"] == "utsw_internal_test")
        & (frame["modality_condition"] == "full")
    ]
    labels = selected["label"].to_numpy(dtype=np.int64)
    scores = selected["p_hat"].to_numpy(dtype=np.float64)
    if np.unique(labels).size != 2:
        raise ValueError("internal-test rows must contain exactly two classes")
    auroc = binary_auroc(scores, labels)
    auprc = average_precision(scores, labels)
    intervals = bootstrap_intervals(scores, labels)
    brier = brier_score(scores, labels)
    ece = expected_calibration_error(scores, labels, n_bins=10)
    positives = int(labels.sum())
    n = int(labels.size)
    ci = intervals["auroc_ci"]
    assert isinstance(ci, list)
    flags = criterion_flags(auroc, [float(ci[0]), float(ci[1])])
    dice_path = run_dir / "segmentation_dice.json"
    if dice_path.exists():
        try:
            segmentation_dice: Any = json.loads(dice_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("segmentation_dice.json is invalid") from error
    else:
        segmentation_dice = "not_available: run scripts/freeze_predictions.py first"
    report: dict[str, Any] = {
        "artifact_sha256": sha256_file(artifact_path),
        "auprc": auprc,
        "auprc_no_skill_prevalence": positives / n,
        "auprc_ci": intervals["auprc_ci"],
        "auroc": auroc,
        "auroc_ci": intervals["auroc_ci"],
        "auroc_ci_excludes_0.5": flags["auroc_ci_excludes_0.5"],
        "auroc_ge_0.75": flags["auroc_ge_0.75"],
        "bootstrap": {
            "iterations": _BOOTSTRAP_ITERATIONS,
            "seed": _BOOTSTRAP_SEED,
            "skipped_resamples": intervals["skipped_resamples"],
        },
        "brier": brier,
        "checkpoint_hash": metadata["checkpoint_hash"],
        "coverage": 1.0,
        "criterion_6_met": flags["criterion_6_met"],
        "ece": ece,
        "git_sha": metadata["git_sha"],
        "n": n,
        "negatives": n - positives,
        "positives": positives,
        "run_id": run_id,
        "segmentation_dice": segmentation_dice,
        "selective_metrics_note": (
            "always-predict baseline; AURC and selective metrics belong to Phase 09"
        ),
    }
    report_path = run_dir / "phase06_report.json"
    sidecar_path = report_path.with_name(report_path.name + ".sha256")
    if report_path.exists() or sidecar_path.exists():
        raise FileExistsError(f"Phase 06 report already exists: {report_path.name}")
    encoded = (
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    _write_exclusive(report_path, encoded)
    _write_exclusive(sidecar_path, f"{digest}  {report_path.name}\n".encode("ascii"))
    existing_metrics = record.get("metrics")
    metrics = dict(existing_metrics) if isinstance(existing_metrics, dict) else {}
    metrics["internal_test"] = {
        "auroc": auroc,
        "auroc_ci": intervals["auroc_ci"],
        "auprc": auprc,
        "auprc_ci": intervals["auprc_ci"],
        "brier": brier,
        "ece": ece,
        "n": n,
    }
    update_run_record(run_id, metrics=metrics)
    print(f"internal_test AUROC={auroc:.6f} CI95={ci[0]:.6f},{ci[1]:.6f}")
    auprc_ci = intervals["auprc_ci"]
    assert isinstance(auprc_ci, list)
    print(f"internal_test AUPRC={auprc:.6f} CI95={auprc_ci[0]:.6f},{auprc_ci[1]:.6f}")
    print(f"internal_test Brier={brier:.6f} ECE={ece:.6f} n={n}")
    print(
        "criterion_6_met="
        f"{report['criterion_6_met']} (auroc_ge_0.75={flags['auroc_ge_0.75']}, "
        f"auroc_ci_excludes_0.5={flags['auroc_ci_excludes_0.5']})"
    )
    return report_path

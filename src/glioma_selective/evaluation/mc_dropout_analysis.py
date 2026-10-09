"""Compare M3 head-only MC-dropout to M2 on frozen internal-test predictions."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from glioma_selective.calibration.temperature import apply_temperature, fit_temperature
from glioma_selective.evaluation.selective_metrics import (
    rejected_but_correct_rate,
    selective_risk_at_coverage,
)
from glioma_selective.selective.abstention import confidence_scores, mc_dropout_scores
from glioma_selective.selective.aurc import (
    aurc_mean_over_cutoffs,
    aurc_trapezoid,
    oracle_aurc,
)
from glioma_selective.selective.risk_coverage import monotonicity_violations, rc_points
from glioma_selective.tracking.predictions import read_prediction_artifact
from glioma_selective.tracking.run_record import sha256_file
from glioma_selective.utils import paths

_COVERAGE_GRID = (0.9, 0.8, 0.7, 0.6, 0.5)


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _selective_summary(scores: list[float], losses: list[int]) -> dict[str, Any]:
    correct = [1 - loss for loss in losses]
    points = rc_points(scores, losses)
    violations, magnitude = monotonicity_violations(points)
    operating: dict[str, Any] = {}
    for target in _COVERAGE_GRID:
        attained, risk = selective_risk_at_coverage(scores, losses, target)
        rejected_rate, rejected_count = rejected_but_correct_rate(
            scores, correct, target
        )
        operating[str(target)] = {
            "attained_coverage": attained,
            "risk": risk,
            "rejected_but_correct_rate": rejected_rate,
            "rejected_count": rejected_count,
        }
    return {
        "rc_points": [[coverage, risk] for coverage, risk in points],
        "aurc_mean_over_cutoffs": aurc_mean_over_cutoffs(scores, losses),
        "aurc_trapezoid": aurc_trapezoid(scores, losses),
        "oracle_aurc": oracle_aurc(losses),
        "operating_points": operating,
        "monotonicity_violations": violations,
        "monotonicity_violation_magnitude": magnitude,
    }


def _split(frame: Any, cohort: str) -> Any:
    result = frame.loc[
        (frame["cohort"] == cohort) & (frame["modality_condition"] == "full")
    ]
    if result.empty:
        raise ValueError(f"{cohort} rows are required")
    return result


def _entropy_summary(rows: Any) -> dict[str, Any]:
    samples = np.asarray(rows["mc_dropout_samples"].tolist(), dtype=np.float64)
    if samples.ndim != 2 or samples.shape[0] == 0 or samples.shape[1] == 0:
        raise ValueError("MC-dropout samples must be a non-empty rectangular matrix")
    scores = mc_dropout_scores(samples)
    entropy = -np.asarray(scores, dtype=np.float64)
    sample_std = np.std(samples, axis=1, ddof=1) if samples.shape[1] > 1 else None
    return {
        "n": int(samples.shape[0]),
        "passes": int(samples.shape[1]),
        "mean_entropy": float(np.mean(entropy)),
        "median_entropy": float(np.median(entropy)),
        "mean_sample_standard_deviation": (
            float(np.mean(sample_std)) if sample_std is not None else None
        ),
    }


def analyze_mc_dropout(run_id: str) -> Path:
    """Validate frozen M3 provenance and write internal-test selective metrics."""
    record_path = paths.experiments_dir() / run_id / "record.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load run record for run {run_id}") from error
    if not isinstance(record, dict) or record.get("run_id") != run_id:
        raise ValueError("run record does not match its run ID")
    if record.get("status") != "completed":
        raise ValueError("MC-dropout analysis requires status=completed")

    run_dir = record_path.parent
    report_path = run_dir / "mc_dropout_analysis.json"
    sidecar_path = report_path.with_name(report_path.name + ".sha256")
    if report_path.exists() or sidecar_path.exists():
        raise FileExistsError(f"MC-dropout analysis already exists: {report_path.name}")

    predictions, pred_meta = read_prediction_artifact(run_dir / "predictions.parquet")
    mc_rows, mc_meta = read_prediction_artifact(run_dir / "mc_dropout.parquet")
    checkpoint_hash = record.get("checkpoint_hash")
    for label, metadata in (("prediction", pred_meta), ("MC-dropout", mc_meta)):
        if metadata.get("run_id") != run_id:
            raise ValueError(f"{label} artifact run_id does not match the run record")
        if metadata.get("checkpoint_hash") != checkpoint_hash:
            raise ValueError(
                f"{label} artifact checkpoint_hash does not match the run record"
            )

    test_predictions = _split(predictions, "utsw_internal_test")
    test_mc = _split(mc_rows, "utsw_internal_test")
    pred_patients = set(test_predictions["patient_id"].tolist())
    mc_patients = set(test_mc["patient_id"].tolist())
    if pred_patients != mc_patients:
        raise ValueError("internal-test patient sets differ between artifacts")
    pred_by_id = test_predictions.set_index("patient_id")
    mc_by_id = test_mc.set_index("patient_id")
    ordered_ids = sorted(pred_patients)
    pred_aligned = pred_by_id.loc[ordered_ids]
    mc_aligned = mc_by_id.loc[ordered_ids]
    probability_difference = np.abs(
        pred_aligned["p_hat"].to_numpy(dtype=np.float64)
        - mc_aligned["p_hat"].to_numpy(dtype=np.float64)
    )
    maximum_difference = float(np.max(probability_difference))
    if maximum_difference > 1e-5:
        raise ValueError("internal-test p_hat values differ by more than 1e-5")

    calibration = _split(predictions, "utsw_calibration")
    calibration_labels = calibration["label"].to_numpy(dtype=np.int64)
    if np.unique(calibration_labels).size != 2:
        raise ValueError("utsw_calibration rows must contain exactly two classes")
    temperature = fit_temperature(
        calibration["logit"].to_numpy(dtype=np.float64), calibration_labels
    )
    test_logits = pred_aligned["logit"].to_numpy(dtype=np.float64)
    test_labels = pred_aligned["label"].to_numpy(dtype=np.int64)
    test_probabilities = pred_aligned["p_hat"].to_numpy(dtype=np.float64)
    losses = (
        ((test_probabilities >= 0.5) != (test_labels == 1)).astype(np.int64).tolist()
    )
    mc_samples = np.asarray(mc_aligned["mc_dropout_samples"].tolist(), dtype=np.float64)
    m3_scores = mc_dropout_scores(mc_samples)
    m2_probabilities = apply_temperature(test_logits, temperature)
    m2_scores = confidence_scores(m2_probabilities.tolist())
    m3 = _selective_summary(m3_scores, losses)
    m2 = _selective_summary(m2_scores, losses)
    split_entropy = {
        "calibration": _entropy_summary(_split(mc_rows, "utsw_calibration")),
        "internal_test": _entropy_summary(test_mc),
    }
    document: dict[str, Any] = {
        "provenance": {
            "run_id": run_id,
            "checkpoint_hash": checkpoint_hash,
            "predictions_sha256": sha256_file(run_dir / "predictions.parquet"),
            "mc_dropout_sha256": sha256_file(run_dir / "mc_dropout.parquet"),
            "temperature": temperature,
            "internal_test_p_hat_max_abs_difference": maximum_difference,
            "coverage_grid": list(_COVERAGE_GRID),
            "splits": split_entropy,
        },
        "views": {
            "M3_mc_dropout": m3,
            "M2_temperature_scaled": m2,
            "aurc_mean_over_cutoffs_M3_minus_M2": (
                m3["aurc_mean_over_cutoffs"] - m2["aurc_mean_over_cutoffs"]
            ),
        },
    }
    encoded = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    _write_exclusive(report_path, encoded)
    _write_exclusive(sidecar_path, f"{digest}  {report_path.name}\n".encode("ascii"))
    print(f"internal_test M3 AURC={m3['aurc_mean_over_cutoffs']:.6f}")
    print(f"internal_test M2 AURC={m2['aurc_mean_over_cutoffs']:.6f}")
    return report_path

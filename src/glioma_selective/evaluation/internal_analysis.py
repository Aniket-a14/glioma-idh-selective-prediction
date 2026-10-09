"""Internal calibration and selective analysis of a frozen prediction artifact."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

from glioma_selective.calibration.conformal import (
    conformal_quantile,
    conformal_summary,
    nonconformity_scores,
    prediction_sets,
)
from glioma_selective.calibration.crc import accept, crc_threshold
from glioma_selective.calibration.temperature import (
    apply_temperature,
    fit_temperature,
)
from glioma_selective.evaluation.calibration_metrics import (
    brier_score,
    expected_calibration_error,
    reliability_bins,
)
from glioma_selective.evaluation.phase06_report import average_precision
from glioma_selective.evaluation.selective_metrics import (
    rejected_but_correct_rate,
    selective_risk_at_coverage,
)
from glioma_selective.selective.abstention import confidence_scores
from glioma_selective.selective.aurc import (
    aurc_mean_over_cutoffs,
    aurc_trapezoid,
    oracle_aurc,
)
from glioma_selective.selective.risk_coverage import (
    monotonicity_violations,
    rc_points,
)
from glioma_selective.tracking.predictions import read_prediction_artifact
from glioma_selective.tracking.run_record import sha256_file, update_run_record
from glioma_selective.training.metrics import binary_auroc
from glioma_selective.utils import paths

__all__ = ["analyze_internal"]

_COVERAGE_GRID = (0.9, 0.8, 0.7, 0.6, 0.5)
_ALPHA_GRID = (0.05, 0.10, 0.20)


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _finite_or_inf(value: float) -> float | str:
    return "inf" if math.isinf(value) else value


def _split_arrays(frame: Any, cohort: str) -> tuple[np.ndarray, ...]:
    rows = frame.loc[
        (frame["cohort"] == cohort) & (frame["modality_condition"] == "full")
    ]
    labels = rows["label"].to_numpy(dtype=np.int64)
    if np.unique(labels).size != 2:
        raise ValueError(f"{cohort} rows must contain exactly two classes")
    return (
        rows["logit"].to_numpy(dtype=np.float64),
        rows["p_hat"].to_numpy(dtype=np.float64),
        labels,
    )


def _classification_metrics(
    probabilities: np.ndarray, labels: np.ndarray
) -> dict[str, Any]:
    predicted = probabilities >= 0.5
    actual = labels == 1
    true_positive = int(np.sum(predicted & actual))
    true_negative = int(np.sum(~predicted & ~actual))
    positives = int(np.sum(actual))
    negatives = int(labels.size - positives)
    return {
        "auroc": binary_auroc(probabilities, labels),
        "auprc": average_precision(probabilities, labels),
        "coverage": 1.0,
        "brier": brier_score(probabilities, labels),
        "ece": {
            str(bins): expected_calibration_error(probabilities, labels, n_bins=bins)
            for bins in (10, 5, 15)
        },
        "reliability_bins": reliability_bins(probabilities, labels, n_bins=10),
        "accuracy": float(np.mean(predicted == actual)),
        "sensitivity": true_positive / positives,
        "specificity": true_negative / negatives,
    }


def _selective_metrics(probabilities: np.ndarray, labels: np.ndarray) -> dict[str, Any]:
    predictions = probabilities >= 0.5
    losses = (predictions != (labels == 1)).astype(np.int64)
    correct = 1 - losses
    scores = confidence_scores(probabilities.tolist())
    points = rc_points(scores, losses.tolist())
    violations, violation_magnitude = monotonicity_violations(points)
    operating_points: dict[str, Any] = {}
    for target in _COVERAGE_GRID:
        attained, risk = selective_risk_at_coverage(scores, losses.tolist(), target)
        rejected_correct, rejected_count = rejected_but_correct_rate(
            scores, correct.tolist(), target
        )
        operating_points[str(target)] = {
            "attained_coverage": attained,
            "risk": risk,
            "rejected_but_correct_rate": rejected_correct,
            "rejected_count": rejected_count,
        }
    return {
        "rc_points": [[coverage, risk] for coverage, risk in points],
        "aurc_mean_over_cutoffs": aurc_mean_over_cutoffs(scores, losses.tolist()),
        "aurc_trapezoid": aurc_trapezoid(scores, losses.tolist()),
        "oracle_aurc": oracle_aurc(losses.tolist()),
        "operating_points": operating_points,
        "monotonicity_violations": violations,
        "monotonicity_violation_magnitude": violation_magnitude,
    }


def _conformal_metrics(
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
    test_labels: np.ndarray,
) -> dict[str, Any]:
    scores = nonconformity_scores(
        calibration_probabilities.tolist(), calibration_labels.tolist()
    )
    result: dict[str, Any] = {}
    for alpha in _ALPHA_GRID:
        quantile = conformal_quantile(scores, alpha)
        sets = prediction_sets(test_probabilities.tolist(), quantile)
        summary = conformal_summary(sets, test_labels.tolist())
        singleton_sets = [item for item in sets if len(item) == 1]
        singleton_correct = sum(
            label in item
            for item, label in zip(sets, test_labels.tolist(), strict=True)
            if len(item) == 1
        )
        result[str(alpha)] = {
            "alpha": alpha,
            "nominal_coverage": 1.0 - alpha,
            "quantile": _finite_or_inf(quantile),
            **summary,
            "singleton_true_label_fraction": (
                singleton_correct / len(singleton_sets) if singleton_sets else None
            ),
            "singleton_count": len(singleton_sets),
            "empty_count": sum(len(item) == 0 for item in sets),
            "full_count": sum(len(item) == 2 for item in sets),
        }
    return result


def _crc_metrics(
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
    test_labels: np.ndarray,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    predictions = test_probabilities >= 0.5
    wrong = predictions != (test_labels == 1)
    for alpha in _ALPHA_GRID:
        threshold = crc_threshold(
            calibration_probabilities.tolist(), calibration_labels.tolist(), alpha
        )
        accepted = np.asarray(
            [
                accept(float(probability), threshold)
                for probability in test_probabilities
            ]
        )
        accepted_count = int(accepted.sum())
        result[str(alpha)] = {
            "alpha": alpha,
            "tau": _finite_or_inf(threshold),
            "coverage": float(np.mean(accepted)),
            "accepted_and_wrong_rate": float(np.mean(accepted & wrong)),
            "risk_among_accepted": (
                float(np.mean(wrong[accepted])) if accepted_count else None
            ),
        }
    return result


def analyze_internal(run_id: str) -> Path:
    """Analyze internal calibration and test rows in a frozen artifact."""
    record_path = paths.experiments_dir() / run_id / "record.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load run record for run {run_id}") from error
    if not isinstance(record, dict) or record.get("run_id") != run_id:
        raise ValueError("run record does not match its run ID")
    if record.get("status") != "completed":
        raise ValueError("internal analysis requires status=completed")

    run_dir = record_path.parent
    report_path = run_dir / "internal_analysis.json"
    sidecar_path = report_path.with_name(report_path.name + ".sha256")
    if report_path.exists() or sidecar_path.exists():
        raise FileExistsError(f"internal analysis already exists: {report_path.name}")

    artifact_path = run_dir / "predictions.parquet"
    frame, metadata = read_prediction_artifact(artifact_path)
    if metadata.get("run_id") != run_id:
        raise ValueError("prediction artifact run_id does not match the run record")
    if metadata.get("checkpoint_hash") != record.get("checkpoint_hash"):
        raise ValueError(
            "prediction artifact checkpoint_hash does not match the run record"
        )
    calibration_logits, calibration_raw, calibration_labels = _split_arrays(
        frame, "utsw_calibration"
    )
    test_logits, test_raw, test_labels = _split_arrays(frame, "utsw_internal_test")

    temperature = fit_temperature(calibration_logits, calibration_labels)
    calibration_scaled = apply_temperature(calibration_logits, temperature)
    test_scaled = apply_temperature(test_logits, temperature)
    raw_test = _classification_metrics(test_raw, test_labels)
    scaled_test = _classification_metrics(test_scaled, test_labels)
    raw_selective = _selective_metrics(test_raw, test_labels)
    scaled_selective = _selective_metrics(test_scaled, test_labels)
    conformal = _conformal_metrics(
        calibration_scaled, calibration_labels, test_scaled, test_labels
    )
    crc = _crc_metrics(calibration_scaled, calibration_labels, test_scaled, test_labels)

    def split_counts(labels: np.ndarray) -> dict[str, int]:
        positives = int(labels.sum())
        return {
            "n": int(labels.size),
            "positives": positives,
            "negatives": int(labels.size - positives),
        }

    document: dict[str, Any] = {
        "provenance": {
            "run_id": run_id,
            "checkpoint_hash": metadata["checkpoint_hash"],
            "artifact_sha256": sha256_file(artifact_path),
            "git_sha": metadata["git_sha"],
            "temperature": temperature,
            "splits": {
                "calibration": split_counts(calibration_labels),
                "internal_test": split_counts(test_labels),
            },
            "coverage_grid": list(_COVERAGE_GRID),
            "alpha_grid": list(_ALPHA_GRID),
            "ece_bins": {"primary": 10, "sensitivity": [5, 15]},
        },
        "views": {
            "M1_raw": {"classification": raw_test, "selective": raw_selective},
            "M2_scaled": {"classification": scaled_test, "selective": scaled_selective},
        },
        "conformal": conformal,
        "crc": crc,
    }
    encoded = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    _write_exclusive(report_path, encoded)
    _write_exclusive(sidecar_path, f"{digest}  {report_path.name}\n".encode("ascii"))

    existing_metrics = record.get("metrics")
    metrics = dict(existing_metrics) if isinstance(existing_metrics, dict) else {}
    alpha_summary = conformal["0.1"]
    metrics["internal_analysis"] = {
        "temperature": temperature,
        "M1_raw": {
            "ece": raw_test["ece"]["10"],
            "brier": raw_test["brier"],
            "aurc_mean_over_cutoffs": raw_selective["aurc_mean_over_cutoffs"],
        },
        "M2_scaled": {
            "ece": scaled_test["ece"]["10"],
            "brier": scaled_test["brier"],
            "aurc_mean_over_cutoffs": scaled_selective["aurc_mean_over_cutoffs"],
        },
        "alpha_0.10": {
            "coverage": alpha_summary["coverage"],
            "abstention_rate": alpha_summary["abstention_rate"],
        },
    }
    update_run_record(run_id, metrics=metrics)
    print(f"calibration temperature={temperature:.6f}")
    print(
        "M1_raw "
        f"ECE={raw_test['ece']['10']:.6f} Brier={raw_test['brier']:.6f} "
        f"AURC={raw_selective['aurc_mean_over_cutoffs']:.6f}"
    )
    print(
        "M2_scaled "
        f"ECE={scaled_test['ece']['10']:.6f} Brier={scaled_test['brier']:.6f} "
        f"AURC={scaled_selective['aurc_mean_over_cutoffs']:.6f}"
    )
    print(
        "conformal alpha=0.10 "
        f"coverage={alpha_summary['coverage']:.6f} "
        f"abstention={alpha_summary['abstention_rate']:.6f}"
    )
    print(
        "CRC alpha=0.10 "
        f"coverage={crc['0.1']['coverage']:.6f} "
        f"accepted_and_wrong={crc['0.1']['accepted_and_wrong_rate']:.6f}"
    )
    return report_path

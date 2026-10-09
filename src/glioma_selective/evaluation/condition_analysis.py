"""Analyze frozen internal predictions for each missing-modality condition."""

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
    nonconformity_scores,
    prediction_sets,
)
from glioma_selective.calibration.crc import accept, crc_threshold
from glioma_selective.calibration.temperature import apply_temperature, fit_temperature
from glioma_selective.evaluation.calibration_metrics import (
    brier_score,
    expected_calibration_error,
)
from glioma_selective.evaluation.phase06_report import average_precision
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
from glioma_selective.selective.risk_coverage import rc_points
from glioma_selective.tracking.predictions import read_prediction_artifact
from glioma_selective.tracking.run_record import sha256_file
from glioma_selective.training.metrics import binary_auroc
from glioma_selective.utils import paths

_ALPHAS = (0.05, 0.10, 0.20)
_COVERAGES = (0.9, 0.8, 0.7, 0.6, 0.5)
_CONDITIONS = (
    "full",
    "drop_t1",
    "drop_t1ce",
    "drop_t2",
    "drop_flair",
    "t1ce_flair_only",
)


def _write_exclusive(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _read_json_with_sidecar(path: Path) -> dict[str, Any]:
    sidecar = path.with_name(path.name + ".sha256")
    try:
        payload = path.read_bytes()
        expected = sidecar.read_text(encoding="ascii").split()[0].lower()
        document = json.loads(payload)
    except (OSError, UnicodeError, IndexError, json.JSONDecodeError) as error:
        raise ValueError(f"{path.name} or its SHA-256 sidecar is invalid") from error
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"{path.name} does not match its SHA-256 sidecar")
    if not isinstance(document, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return document


def _rows(frame: Any, cohort: str, condition: str) -> Any:
    selected = frame.loc[
        (frame["cohort"] == cohort) & (frame["modality_condition"] == condition)
    ]
    if selected.empty:
        raise ValueError(f"{cohort} rows are required for {condition}")
    return selected


def _arrays(rows: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    logits = rows["logit"].to_numpy(dtype=np.float64)
    probabilities = rows["p_hat"].to_numpy(dtype=np.float64)
    labels = rows["label"].to_numpy(dtype=np.int64)
    if np.unique(labels).size != 2:
        raise ValueError("each split must contain exactly two classes")
    return (
        logits,
        probabilities,
        labels,
        np.asarray(rows["mc_dropout_samples"].tolist(), dtype=np.float64),
    )


def _finite_or_inf(value: float) -> float | str:
    return "inf" if math.isinf(value) else value


def _raw_metrics(probabilities: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    return {
        "auroc": binary_auroc(probabilities, labels),
        "auprc": average_precision(probabilities, labels),
        "brier": brier_score(probabilities, labels),
        "ece_10_bins": expected_calibration_error(probabilities, labels, n_bins=10),
    }


def _conformal_summary(
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
    test_labels: np.ndarray,
    alpha: float,
) -> dict[str, Any]:
    scores = nonconformity_scores(
        calibration_probabilities.tolist(), calibration_labels.tolist()
    )
    quantile = conformal_quantile(scores, alpha)
    sets = prediction_sets(test_probabilities.tolist(), quantile)
    n = len(sets)
    singleton = [item for item in sets if len(item) == 1]
    singleton_correct = sum(
        label in item
        for item, label in zip(sets, test_labels.tolist(), strict=True)
        if len(item) == 1
    )
    return {
        "quantile": _finite_or_inf(quantile),
        "empirical_coverage": sum(
            label in item
            for item, label in zip(sets, test_labels.tolist(), strict=True)
        )
        / n,
        "abstention_rate": sum(len(item) != 1 for item in sets) / n,
        "empty_count": sum(len(item) == 0 for item in sets),
        "singleton_count": len(singleton),
        "full_count": sum(len(item) == 2 for item in sets),
        "singleton_true_label_fraction": singleton_correct / len(singleton)
        if singleton
        else None,
    }


def _crc_summary(
    calibration_probabilities: np.ndarray,
    calibration_labels: np.ndarray,
    test_probabilities: np.ndarray,
    test_labels: np.ndarray,
    alpha: float,
) -> dict[str, Any]:
    threshold = crc_threshold(
        calibration_probabilities.tolist(), calibration_labels.tolist(), alpha
    )
    accepted = np.asarray(
        [accept(float(probability), threshold) for probability in test_probabilities],
        dtype=bool,
    )
    wrong = (test_probabilities >= 0.5) != (test_labels == 1)
    return {
        "tau": _finite_or_inf(threshold),
        "acceptance_rate": float(np.mean(accepted)),
        "accepted_and_wrong_rate": float(np.mean(accepted & wrong)),
    }


def _selective_summary(scores: list[float], losses: list[int]) -> dict[str, Any]:
    points = rc_points(scores, losses)
    operating: dict[str, Any] = {}
    correct = [1 - loss for loss in losses]
    for target in _COVERAGES:
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
        "selective_risk_at_coverage": operating,
    }


def analyze_conditions(run_id: str) -> Path:
    """Validate provenance and write internal-split condition comparisons."""
    record_path = paths.experiments_dir() / run_id / "record.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load run record for run {run_id}") from error
    if not isinstance(record, dict) or record.get("run_id") != run_id:
        raise ValueError("run record does not match its run ID")
    if record.get("status") != "completed":
        raise ValueError("condition analysis requires status=completed")
    run_dir = record_path.parent
    report_path = run_dir / "conditions_analysis.json"
    if (
        report_path.exists()
        or report_path.with_name(report_path.name + ".sha256").exists()
    ):
        raise FileExistsError(f"condition analysis already exists: {report_path.name}")

    predictions, prediction_meta = read_prediction_artifact(
        run_dir / "predictions.parquet"
    )
    checkpoint_hash = record.get("checkpoint_hash")
    for label, metadata in (("prediction", prediction_meta),):
        if metadata.get("run_id") != run_id:
            raise ValueError(f"{label} artifact run_id does not match the run record")
        if metadata.get("checkpoint_hash") != checkpoint_hash:
            raise ValueError(
                f"{label} artifact checkpoint_hash does not match the run record"
            )
    conditions_dir = run_dir / "conditions"
    meta = _read_json_with_sidecar(conditions_dir / "conditions_meta.json")
    if meta.get("run_id") != run_id or meta.get("checkpoint_hash") != checkpoint_hash:
        raise ValueError("conditions metadata provenance does not match the run")
    condition_frames: dict[str, Any] = {}
    for condition in _CONDITIONS:
        frame, metadata = read_prediction_artifact(
            conditions_dir / f"{condition}.parquet"
        )
        if (
            metadata.get("run_id") != run_id
            or metadata.get("checkpoint_hash") != checkpoint_hash
        ):
            raise ValueError(f"{condition} artifact provenance does not match the run")
        if not bool((frame["modality_condition"] == condition).all()):
            raise ValueError(f"{condition} artifact contains another condition")
        condition_frames[condition] = frame

    baseline = _rows(predictions, "utsw_internal_test", "full")
    baseline_ids = set(baseline["patient_id"].tolist())
    for condition, frame in condition_frames.items():
        condition_test = _rows(frame, "utsw_internal_test", condition)
        if set(condition_test["patient_id"].tolist()) != baseline_ids:
            raise ValueError(f"internal-test patient sets differ for {condition}")

    full_calibration = _rows(condition_frames["full"], "utsw_calibration", "full")
    full_cal_logits, _full_cal_raw, full_cal_labels, _ = _arrays(full_calibration)
    full_temperature = fit_temperature(full_cal_logits, full_cal_labels)
    full_cal_scaled = apply_temperature(full_cal_logits, full_temperature)
    condition_results: dict[str, Any] = {}
    aurocs: dict[str, float] = {}
    for condition in _CONDITIONS:
        frame = condition_frames[condition]
        calibration = _rows(frame, "utsw_calibration", condition)
        test = _rows(frame, "utsw_internal_test", condition)
        cal_logits, _cal_raw, cal_labels, _ = _arrays(calibration)
        test_logits, test_raw, test_labels, mc_samples = _arrays(test)
        raw_metrics = _raw_metrics(test_raw, test_labels)
        aurocs[condition] = raw_metrics["auroc"]
        condition_temperature = fit_temperature(cal_logits, cal_labels)
        variants: dict[str, Any] = {}
        for variant, temperature, calibration_scaled in (
            ("carried_over", full_temperature, full_cal_scaled),
            (
                "refit",
                condition_temperature,
                apply_temperature(cal_logits, condition_temperature),
            ),
        ):
            test_scaled = apply_temperature(test_logits, temperature)
            by_alpha: dict[str, Any] = {}
            for alpha in _ALPHAS:
                by_alpha[str(alpha)] = {
                    "conformal": _conformal_summary(
                        calibration_scaled,
                        full_cal_labels if variant == "carried_over" else cal_labels,
                        test_scaled,
                        test_labels,
                        alpha,
                    ),
                    "crc": _crc_summary(
                        calibration_scaled,
                        full_cal_labels if variant == "carried_over" else cal_labels,
                        test_scaled,
                        test_labels,
                        alpha,
                    ),
                }
            variants[variant] = {
                "temperature": temperature,
                "m2_brier": brier_score(test_scaled, test_labels),
                "m2_ece_10_bins": expected_calibration_error(
                    test_scaled, test_labels, n_bins=10
                ),
                "by_alpha": by_alpha,
            }

        losses = (((test_raw >= 0.5) != (test_labels == 1)).astype(np.int64)).tolist()
        m2 = _selective_summary(confidence_scores(test_raw.tolist()), losses)
        m3 = _selective_summary(mc_dropout_scores(mc_samples), losses)
        condition_results[condition] = {
            "raw": raw_metrics,
            "recalibration": variants,
            "selective": {
                "M2_confidence": m2,
                "M3_mc_dropout_entropy": m3,
                "M3_minus_M2_aurc_mean_over_cutoffs": (
                    m3["aurc_mean_over_cutoffs"] - m2["aurc_mean_over_cutoffs"]
                ),
            },
        }

    order = sorted(_CONDITIONS, key=lambda condition: aurocs[condition], reverse=True)
    document = {
        "provenance": {
            "run_id": run_id,
            "checkpoint_hash": checkpoint_hash,
            "predictions_sha256": sha256_file(run_dir / "predictions.parquet"),
            "conditions_meta_sha256": sha256_file(
                conditions_dir / "conditions_meta.json"
            ),
            "internal_split_only": True,
            "alpha_grid": list(_ALPHAS),
            "coverage_grid": list(_COVERAGES),
            "full_temperature": full_temperature,
        },
        "conditions": condition_results,
        "degradation": {
            "auroc": aurocs,
            "difference_from_full": {
                condition: aurocs[condition] - aurocs["full"]
                for condition in _CONDITIONS
            },
            "auroc_drop_t1ce_below_drop_t1": aurocs["drop_t1ce"] < aurocs["drop_t1"],
            "all_conditions_below_full": all(
                aurocs[name] < aurocs["full"] for name in _CONDITIONS if name != "full"
            ),
            "ordering_highest_to_lowest": order,
        },
    }
    encoded = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    digest = hashlib.sha256(encoded).hexdigest()
    _write_exclusive(report_path, encoded)
    _write_exclusive(
        report_path.with_name(report_path.name + ".sha256"),
        f"{digest}  {report_path.name}\n".encode("ascii"),
    )
    print(f"conditions={len(_CONDITIONS)} internal_test_n={len(baseline_ids)}")
    return report_path

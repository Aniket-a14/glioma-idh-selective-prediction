"""Assemble Phase 09 internal results from frozen prediction artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import numpy as np

from glioma_selective.calibration.conformal import (
    conformal_quantile,
    empirical_coverage,
    nonconformity_scores,
    prediction_sets,
)
from glioma_selective.calibration.temperature import apply_temperature, fit_temperature
from glioma_selective.evaluation.condition_analysis import (
    _read_json_with_sidecar,
    _rows,
    _write_exclusive,
)
from glioma_selective.evaluation.selective_metrics import (
    rejected_but_correct_rate,
    selective_risk_at_coverage,
)
from glioma_selective.selective.abstention import (
    confidence_scores,
    ensemble_variance_scores,
    mc_dropout_scores,
)
from glioma_selective.selective.aurc import (
    aurc_mean_over_cutoffs,
    aurc_trapezoid,
    oracle_aurc,
)
from glioma_selective.selective.claims import (
    Status,
    deviation_label,
    status_c4,
    status_c5,
    status_c6,
    status_risk_difference,
    worst_status,
)
from glioma_selective.selective.coverage import coverage_deviation_bootstrap
from glioma_selective.selective.risk_coverage import (
    monotonicity_total_bootstrap,
    monotonicity_violations,
    rc_points,
)
from glioma_selective.statistics.multiplicity import benjamini_hochberg
from glioma_selective.statistics.permutation import enrichment_permutation_test
from glioma_selective.statistics.resampling import (
    bootstrap_indices,
    percentile_interval,
)
from glioma_selective.tracking.predictions import read_prediction_artifact
from glioma_selective.utils import paths

CONDITIONS = (
    "full",
    "drop_t1",
    "drop_t1ce",
    "drop_t2",
    "drop_flair",
    "t1ce_flair_only",
)
COVERAGE_GRID = (0.9, 0.8, 0.7, 0.6, 0.5)
ALPHA_GRID = (0.05, 0.10, 0.20)
MECHANISMS = ("M1", "M2", "M3", "M4", "M5", "M6")


def _aligned_values(frame: Any, ids: list[str]) -> tuple[np.ndarray, ...]:
    rows = frame.set_index("patient_id").loc[ids]
    logits = rows["logit"].to_numpy(dtype=np.float64)
    probabilities = rows["p_hat"].to_numpy(dtype=np.float64)
    labels = rows["label"].to_numpy(dtype=np.int64)
    if not np.all(np.isin(labels, (0, 1))) or np.unique(labels).size != 2:
        raise ValueError("each UTSW split must contain both binary classes")
    return logits, probabilities, labels


def _probability_matrix(rows: Any, column: str) -> np.ndarray:
    try:
        values = np.asarray(rows[column].tolist(), dtype=np.float64)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            f"{column} must contain rectangular probability rows"
        ) from error
    if values.ndim != 2 or values.shape[0] != len(rows) or values.shape[1] < 1:
        raise ValueError(f"{column} must contain a non-empty rectangular matrix")
    if not np.all(np.isfinite(values)) or np.any((values < 0) | (values > 1)):
        raise ValueError(f"{column} values must be finite probabilities")
    return values


def _validate_artifact(
    path: Path, run_id: str, checkpoint_hash: str, condition: str | None = None
) -> Any:
    frame, metadata = read_prediction_artifact(path)
    if metadata.get("run_id") != run_id:
        raise ValueError(f"{path.name} run_id does not match its run record")
    if metadata.get("checkpoint_hash") != checkpoint_hash:
        raise ValueError(f"{path.name} checkpoint_hash does not match its run record")
    if not bool((frame["run_id"] == run_id).all()):
        raise ValueError(f"{path.name} row run_id does not match its run record")
    if not bool((frame["checkpoint_hash"] == checkpoint_hash).all()):
        raise ValueError(
            f"{path.name} row checkpoint_hash does not match its run record"
        )
    if condition is not None and not bool(
        (frame["modality_condition"] == condition).all()
    ):
        raise ValueError(f"{path.name} contains another modality condition")
    return frame


def _interval(values: Sequence[float] | np.ndarray) -> dict[str, float]:
    lower, upper = percentile_interval(cast(Any, values))
    return {"lower": lower, "upper": upper}


def _selected_statistics(
    scores: list[float], losses: np.ndarray, indices: np.ndarray
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    n = len(losses)
    always_risk = float(np.mean(losses))
    points = rc_points(scores, losses.tolist())
    count, magnitude = monotonicity_violations(points)
    metric: dict[str, Any] = {
        "n": n,
        "n_errors": int(np.sum(losses)),
        "always_predict_risk": always_risk,
        "rc_points": [[coverage, risk] for coverage, risk in points],
        "aurc_mean_over_cutoffs": aurc_mean_over_cutoffs(scores, losses.tolist()),
        "aurc_trapezoid": aurc_trapezoid(scores, losses.tolist()),
        "oracle_aurc": oracle_aurc(losses.tolist()),
        "monotonicity": {
            "violations": count,
            "magnitude": magnitude,
            "bootstrap_95_interval": {"lower": 0.0, "upper": 0.0},
        },
    }
    operation: dict[str, Any] = {}
    difference_draws: dict[str, list[float]] = {}
    risk_draws: dict[str, list[float]] = {}
    for target in COVERAGE_GRID:
        key = str(target)
        attained, risk = selective_risk_at_coverage(scores, losses.tolist(), target)
        rbcr, rejected_count = rejected_but_correct_rate(
            scores, (1 - losses).tolist(), target
        )
        operation[key] = {
            "risk": risk,
            "attained_coverage": attained,
            "rejected_but_correct_rate": rbcr,
            "n_rejected": rejected_count,
        }
        boot_risks: list[float] = []
        boot_coverages: list[float] = []
        boot_differences: list[float] = []
        score_array = np.asarray(scores, dtype=np.float64)
        for sample_indices in indices:
            sample_scores = score_array[sample_indices].tolist()
            sample_losses = losses[sample_indices]
            sample_coverage, sample_risk = selective_risk_at_coverage(
                sample_scores, sample_losses.tolist(), target
            )
            boot_coverages.append(sample_coverage)
            boot_risks.append(sample_risk)
            boot_differences.append(sample_risk - float(np.mean(sample_losses)))
        risk_draws[key] = boot_risks
        difference_draws[key] = boot_differences
        operation[key]["risk_95_interval"] = _interval(boot_risks)
        operation[key]["attained_coverage_95_interval"] = _interval(boot_coverages)
        diff_interval = _interval(boot_differences)
        operation[key]["D_phi"] = {
            "point": risk - always_risk,
            "lower": diff_interval["lower"],
            "upper": diff_interval["upper"],
        }
    adjacent: list[dict[str, float]] = []
    for higher, lower in zip(COVERAGE_GRID, COVERAGE_GRID[1:], strict=False):
        point = operation[str(lower)]["risk"] - operation[str(higher)]["risk"]
        draws = [
            low - high
            for low, high in zip(
                risk_draws[str(lower)], risk_draws[str(higher)], strict=True
            )
        ]
        adjacent.append({"point": point, **_interval(draws)})
    metric["selective_risk_at_coverage"] = operation
    metric["adjacent_grid_risk_differences"] = adjacent
    metric["aurc_bootstrap_95_interval"] = _interval(
        [
            aurc_mean_over_cutoffs(
                np.asarray(scores, dtype=np.float64)[sample_indices].tolist(),
                losses[sample_indices].tolist(),
            )
            for sample_indices in indices
        ]
    )
    return metric, difference_draws


def _cell_metrics(
    scores: list[float],
    losses: np.ndarray,
    indices: np.ndarray,
    permutations: int,
    seed: int,
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    metric, difference_draws = _selected_statistics(scores, losses, indices)
    enrichment: dict[str, Any] = {}
    p_values: list[float] = []
    tested_keys: list[str] = []
    for offset, target in enumerate(COVERAGE_GRID):
        key = str(target)
        _, rejected_count = rejected_but_correct_rate(
            scores, (1 - losses).tolist(), target
        )
        if rejected_count:
            accepted_count = len(scores) - rejected_count
            cutoff = sorted(scores, reverse=True)[accepted_count - 1]
            rejected = np.asarray(scores, dtype=np.float64) < cutoff
            if int(np.sum(rejected)) != rejected_count:
                raise RuntimeError("score tie block and rejected count disagree")
        else:
            rejected = np.zeros(len(scores), dtype=bool)
        result = enrichment_permutation_test(
            rejected.astype(np.int64), losses, permutations, seed + offset
        )
        enrichment[key] = {
            "observed_difference": result.observed,
            "p_value": result.p_value,
            "n_rejected": result.n_rejected,
        }
        if result.p_value is not None:
            p_values.append(float(result.p_value))
            tested_keys.append(key)
    adjusted, rejected_bh = (
        benjamini_hochberg(cast(Sequence[Any], p_values), q=0.05)
        if p_values
        else ([], [])
    )
    # Exact Fraction output is serialized consistently as reduced rational strings.
    adjusted_by_key = dict(zip(tested_keys, adjusted, strict=True))
    reject_by_key = dict(zip(tested_keys, rejected_bh, strict=True))
    for key in map(str, COVERAGE_GRID):
        p_adjusted = adjusted_by_key.get(key)
        enrichment[key]["adjusted_p_value"] = (
            str(p_adjusted) if p_adjusted is not None else None
        )
        enrichment[key]["bh_reject_q_0.05"] = reject_by_key.get(key)
    metric["enrichment"] = enrichment
    metric["enrichment_adjustment"] = "BH adjusted values are reduced Fraction strings"
    return metric, difference_draws


def _random_control(scores: list[float], losses: np.ndarray) -> dict[str, Any]:
    risks = [
        selective_risk_at_coverage(scores, losses.tolist(), target)[1]
        for target in COVERAGE_GRID
    ]
    return {
        "aurc_mean_over_cutoffs": aurc_mean_over_cutoffs(scores, losses.tolist()),
        "maximum_absolute_grid_risk_gap_from_always_predict": max(
            abs(risk - float(np.mean(losses))) for risk in risks
        ),
        "claim_attached": False,
    }


def _conformal_variant(
    cal_p: np.ndarray,
    cal_y: np.ndarray,
    test_p: np.ndarray,
    test_y: np.ndarray,
    alpha: float,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    quantile = conformal_quantile(
        nonconformity_scores(cal_p.tolist(), cal_y.tolist()), alpha
    )
    cal_sets = prediction_sets(cal_p.tolist(), quantile)
    test_sets = prediction_sets(test_p.tolist(), quantile)
    set_metrics = _summarize_sets(test_sets, test_y)
    coverage = set_metrics["empirical_coverage"]
    draws = coverage_deviation_bootstrap(
        cal_p.tolist(),
        cal_y.tolist(),
        test_p.tolist(),
        test_y.tolist(),
        alpha,
        iterations,
        seed,
    )
    lower, upper = percentile_interval(draws)
    lower_05, upper_05 = lower, upper
    label_07 = deviation_label(lower, upper, 0.07)
    label_05 = deviation_label(lower_05, upper_05, 0.05)
    return {
        "quantile": "inf" if math.isinf(quantile) else quantile,
        **set_metrics,
        "calibration_empirical_coverage": empirical_coverage(cal_sets, cal_y.tolist()),
        "test_minus_calibration_coverage": coverage
        - empirical_coverage(cal_sets, cal_y.tolist()),
        "coverage_deviation_bootstrap": {
            "lower": lower,
            "upper": upper,
            "half_width": label_07.half_width,
            "deviation_label_band_0.07": label_07.label,
            "deviation_label_band_0.05": label_05.label,
        },
    }


def _summarize_sets(sets: list[tuple[int, ...]], labels: np.ndarray) -> dict[str, Any]:
    n = len(labels)
    singletons = [item for item in sets if len(item) == 1]
    singleton_correct = sum(
        label in item
        for item, label in zip(sets, labels.tolist(), strict=True)
        if len(item) == 1
    )
    return {
        "empirical_coverage": empirical_coverage(sets, labels.tolist()),
        "abstention_rate": sum(len(item) != 1 for item in sets) / n,
        "empty_rate": sum(len(item) == 0 for item in sets) / n,
        "empty_count": sum(len(item) == 0 for item in sets),
        "singleton_count": len(singletons),
        "full_count": sum(len(item) == 2 for item in sets),
        "singleton_true_label_fraction": (
            singleton_correct / len(singletons) if singletons else None
        ),
    }


def _load_run(run_id: str) -> tuple[Path, dict[str, Any]]:
    record_path = paths.experiments_dir() / run_id / "record.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not load run record for run {run_id}") from error
    if not isinstance(record, dict) or record.get("run_id") != run_id:
        raise ValueError("run record does not match its run ID")
    if record.get("status") != "completed":
        raise ValueError(f"run {run_id} must have status=completed")
    if not isinstance(record.get("checkpoint_hash"), str):
        raise ValueError("run record has no checkpoint_hash")
    return record_path.parent, record


def _load_condition_frames(
    run_id: str, run_dir: Path, checkpoint_hash: str
) -> tuple[dict[str, Any], Any]:
    predictions = _validate_artifact(
        run_dir / "predictions.parquet", run_id, checkpoint_hash
    )
    conditions_dir = run_dir / "conditions"
    metadata = _read_json_with_sidecar(conditions_dir / "conditions_meta.json")
    if (
        metadata.get("run_id") != run_id
        or metadata.get("checkpoint_hash") != checkpoint_hash
    ):
        raise ValueError("conditions metadata provenance does not match the run")
    frames = {
        condition: _validate_artifact(
            conditions_dir / f"{condition}.parquet", run_id, checkpoint_hash, condition
        )
        for condition in CONDITIONS
    }
    mc_path = run_dir / "mc_dropout.parquet"
    if mc_path.exists() or mc_path.with_name(mc_path.name + ".sha256").exists():
        mc_frame = _validate_artifact(mc_path, run_id, checkpoint_hash)
        mc_meta = _read_json_with_sidecar(run_dir / "mc_dropout_meta.json")
        if (
            mc_meta.get("run_id") != run_id
            or mc_meta.get("checkpoint_hash") != checkpoint_hash
        ):
            raise ValueError("MC-dropout metadata provenance does not match the run")
    else:
        mc_frame = None
    return frames, (predictions, metadata, mc_frame)


def _member_probabilities(
    run_ids: Sequence[str],
    condition: str,
    ids: list[str],
    checkpoint_hashes: dict[str, str],
) -> np.ndarray:
    members: list[np.ndarray] = []
    for run_id in run_ids:
        run_dir, record = _load_run(run_id)
        checkpoint = str(record["checkpoint_hash"])
        checkpoint_hashes[run_id] = checkpoint
        metadata = _read_json_with_sidecar(
            run_dir / "conditions" / "conditions_meta.json"
        )
        if (
            metadata.get("run_id") != run_id
            or metadata.get("checkpoint_hash") != checkpoint
        ):
            raise ValueError("ensemble conditions metadata provenance does not match")
        frame = _validate_artifact(
            run_dir / "conditions" / f"{condition}.parquet",
            run_id,
            checkpoint,
            condition,
        )
        test = _rows(frame, "utsw_internal_test", condition)
        if set(test["patient_id"].tolist()) != set(ids):
            raise ValueError(f"ensemble member patient sets differ for {condition}")
        members.append(
            test.set_index("patient_id").loc[ids]["p_hat"].to_numpy(dtype=np.float64)
        )
    return np.column_stack(members)


def _claim(
    function_status: str,
    points: list[float],
    lowers: list[float],
    uppers: list[float],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": function_status,
        "numbers": {
            "points": points,
            "lower_95_limits": lowers,
            "upper_95_limits": uppers,
            **(extra or {}),
        },
    }


def _patient_roster(
    frames: dict[str, Any], predictions: Any, mc_frame: Any
) -> tuple[list[str], np.ndarray]:
    baseline = _rows(predictions, "utsw_internal_test", "full")
    ids = sorted(baseline["patient_id"].tolist())
    if len(ids) != len(set(ids)):
        raise ValueError("full internal-test patient IDs are not unique")
    baseline_labels = _aligned_values(baseline, ids)[2]
    for condition, frame in frames.items():
        test = _rows(frame, "utsw_internal_test", condition)
        if set(test["patient_id"].tolist()) != set(ids):
            raise ValueError(f"internal-test patient sets differ for {condition}")
        if not np.array_equal(_aligned_values(test, ids)[2], baseline_labels):
            raise ValueError(f"internal-test labels differ for {condition}")
    if mc_frame is not None:
        mc_test = _rows(mc_frame, "utsw_internal_test", "full")
        if set(mc_test["patient_id"].tolist()) != set(ids):
            raise ValueError("internal-test patient sets differ between artifacts")
        condition_test = _rows(frames["full"], "utsw_internal_test", "full")
        mc_p = (
            mc_test.set_index("patient_id").loc[ids]["p_hat"].to_numpy(dtype=np.float64)
        )
        condition_p = (
            condition_test.set_index("patient_id")
            .loc[ids]["p_hat"]
            .to_numpy(dtype=np.float64)
        )
        if np.max(np.abs(mc_p - condition_p)) > 1e-5:
            raise ValueError(
                "mc_dropout.parquet p_hat differs from full condition artifact"
            )
    return ids, baseline_labels


def _aligned_conditions(
    frames: dict[str, Any], ids: list[str], passes: int
) -> tuple[dict[str, dict[str, Any]], float, np.ndarray]:
    full_cal = _rows(frames["full"], "utsw_calibration", "full")
    full_cal_ids = sorted(full_cal["patient_id"].tolist())
    full_logits, _, full_labels = _aligned_values(full_cal, full_cal_ids)
    temperature = fit_temperature(full_logits, full_labels)
    full_scaled = apply_temperature(full_logits, temperature)
    aligned: dict[str, dict[str, Any]] = {}
    for condition in CONDITIONS:
        aligned[condition] = _align_condition(
            frames[condition], condition, ids, temperature, passes
        )
    return aligned, temperature, full_scaled


def _align_condition(
    frame: Any, condition: str, ids: list[str], full_temperature: float, passes: int
) -> dict[str, Any]:
    calibration = _rows(frame, "utsw_calibration", condition)
    cal_ids = sorted(calibration["patient_id"].tolist())
    cal_logits, _, cal_labels = _aligned_values(calibration, cal_ids)
    test = _rows(frame, "utsw_internal_test", condition)
    test_logits, raw_p, labels = _aligned_values(test, ids)
    scaled_full = apply_temperature(test_logits, full_temperature)
    refit_temperature = fit_temperature(cal_logits, cal_labels)
    samples = _probability_matrix(
        test.set_index("patient_id").loc[ids], "mc_dropout_samples"
    )
    if samples.shape[1] != passes:
        raise ValueError(f"{condition} MC-dropout samples do not match passes={passes}")
    return {
        "cal_logits": cal_logits,
        "cal_labels": cal_labels,
        "cal_scaled_refit": apply_temperature(cal_logits, refit_temperature),
        "scaled_refit": apply_temperature(test_logits, refit_temperature),
        "scaled_full": scaled_full,
        "raw_p": raw_p,
        "labels": labels,
        "samples": samples,
    }


def _condition_cells(
    condition: str,
    arrays: dict[str, Any],
    run_id: str,
    ids: list[str],
    ensemble_run_ids: Sequence[str] | None,
    checkpoint_hashes: dict[str, str],
    indices: np.ndarray,
    iterations: int,
    permutations: int,
    seed: int,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    raw_p, labels = arrays["raw_p"], arrays["labels"]
    raw_loss = ((raw_p >= 0.5) != (labels == 1)).astype(np.int64)
    scores = {
        "M1": confidence_scores(raw_p.tolist()),
        "M2": confidence_scores(arrays["scaled_full"].tolist()),
        "M3": mc_dropout_scores(arrays["samples"]),
        "M5": confidence_scores(arrays["scaled_full"].tolist()),
    }
    losses = {key: raw_loss for key in ("M1", "M2", "M3", "M5")}
    if ensemble_run_ids is not None:
        _add_ensemble_scores(
            condition,
            ids,
            run_id,
            ensemble_run_ids,
            checkpoint_hashes,
            scores,
            losses,
            labels,
        )
    cells: dict[str, Any] = {}
    absent: list[dict[str, str]] = []
    for mechanism in MECHANISMS:
        if mechanism in ("M4", "M6") and mechanism not in scores:
            reason = _absent_reason(mechanism)
            cells[mechanism] = {"absent": True, "reason": reason}
            absent.append(
                {"condition": condition, "mechanism": mechanism, "reason": reason}
            )
        else:
            cells[mechanism] = _measure_cell(
                condition,
                mechanism,
                scores[mechanism],
                losses[mechanism],
                indices,
                iterations,
                permutations,
                seed,
            )
    control_scores = np.random.default_rng(seed).uniform(size=len(raw_loss)).tolist()
    cells["random_confidence_control"] = _random_control(control_scores, raw_loss)
    return cells, absent


def _absent_reason(mechanism: str) -> str:
    if mechanism == "M6":
        return "needs its own training run, D-006"
    return "ensemble members R3-R6 not yet frozen"


def _add_ensemble_scores(
    condition: str,
    ids: list[str],
    run_id: str,
    ensemble_run_ids: Sequence[str],
    checkpoint_hashes: dict[str, str],
    scores: dict[str, list[float]],
    losses: dict[str, np.ndarray],
    labels: np.ndarray,
) -> None:
    member_matrix = _member_probabilities(
        [run_id, *ensemble_run_ids], condition, ids, checkpoint_hashes
    )
    mean_probability = member_matrix.mean(axis=1)
    scores["M4"] = ensemble_variance_scores(member_matrix.tolist())
    losses["M4"] = ((mean_probability >= 0.5) != (labels == 1)).astype(np.int64)


def _measure_cell(
    condition: str,
    mechanism: str,
    scores: list[float],
    losses: np.ndarray,
    indices: np.ndarray,
    iterations: int,
    permutations: int,
    seed: int,
) -> dict[str, Any]:
    metric, _ = _cell_metrics(scores, losses, indices, permutations, seed)
    mono_seed = (
        seed
        + CONDITIONS.index(condition) * len(MECHANISMS)
        + MECHANISMS.index(mechanism)
    )
    samples = monotonicity_total_bootstrap(
        scores, losses.tolist(), iterations, mono_seed
    )
    violations, magnitude = monotonicity_violations(rc_points(scores, losses.tolist()))
    metric["monotonicity"] = {
        "violations": violations,
        "magnitude": magnitude,
        "bootstrap_95_interval": dict(
            zip(("lower", "upper"), percentile_interval(samples), strict=True)
        ),
    }
    return metric


def _condition_conformal(
    condition: str,
    arrays: dict[str, Any],
    full_cal: np.ndarray,
    full_labels: np.ndarray,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for variant in ("carried_over", "refit"):
        cal_p, cal_y, test_p, variant_seed = _conformal_inputs(
            condition, variant, arrays, full_cal, full_labels, seed
        )
        result[variant] = {
            str(alpha): _conformal_variant(
                cal_p,
                cal_y,
                test_p,
                arrays["labels"],
                alpha,
                iterations,
                variant_seed + i,
            )
            for i, alpha in enumerate(ALPHA_GRID)
        }
    return result


def _conformal_inputs(
    condition: str,
    variant: str,
    arrays: dict[str, Any],
    full_cal: np.ndarray,
    full_labels: np.ndarray,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    condition_index = CONDITIONS.index(condition)
    if variant == "carried_over":
        return (
            full_cal,
            full_labels,
            arrays["scaled_full"],
            seed + 10000 + condition_index * 100,
        )
    return (
        arrays["cal_scaled_refit"],
        arrays["cal_labels"],
        arrays["scaled_refit"],
        seed + 20000 + condition_index * 100,
    )


def _risk_claims(cells: dict[str, dict[str, Any]]) -> dict[str, Any]:
    full = cells["full"]["M5"]["selective_risk_at_coverage"]
    points, lowers, uppers = _risk_difference_arrays(full)
    c1 = _claim(status_risk_difference(points, uppers), points, lowers, uppers)
    c1["worst_status"] = worst_status([c1["status"]])
    c2: dict[str, Any] = {}
    for condition in CONDITIONS[1:]:
        ops = cells[condition]["M5"]["selective_risk_at_coverage"]
        point_values, lower_values, upper_values = _risk_difference_arrays(ops)
        c2[condition] = _claim(
            status_risk_difference(point_values, upper_values),
            point_values,
            lower_values,
            upper_values,
        )
    return {
        "C1": {"full": c1, "worst_status": c1["status"]},
        "C2": {
            **c2,
            "worst_status": worst_status([value["status"] for value in c2.values()]),
        },
        "C3": {
            "status": "not evaluated",
            "reason": "external cohorts locked until Gate E",
        },
    }


def _risk_difference_arrays(
    ops: dict[str, Any],
) -> tuple[list[float], list[float], list[float]]:
    points = [ops[str(phi)]["D_phi"]["point"] for phi in COVERAGE_GRID]
    lowers = [ops[str(phi)]["D_phi"]["lower"] for phi in COVERAGE_GRID]
    uppers = [ops[str(phi)]["D_phi"]["upper"] for phi in COVERAGE_GRID]
    return points, lowers, uppers


def _c4_claim(conformal: dict[str, Any]) -> dict[str, Any]:
    per_condition: dict[str, Any] = {}
    intervals: list[tuple[float, float]] = []
    for condition in CONDITIONS:
        alphas: dict[str, Any] = {}
        statuses: list[Status] = []
        for alpha in ALPHA_GRID:
            values = conformal[condition]["carried_over"][str(alpha)]
            interval = values["coverage_deviation_bootstrap"]
            limits = (interval["lower"], interval["upper"])
            intervals.append(limits)
            primary = status_c4([limits], 0.07)
            secondary = status_c4([limits], 0.05)
            statuses.append(primary)
            alphas[str(alpha)] = {
                "status": primary,
                "status_band_0.05_secondary": secondary,
                "lower": limits[0],
                "upper": limits[1],
                "half_width": interval["half_width"],
                "deviation_label_band_0.07": interval["deviation_label_band_0.07"],
                "deviation_label_band_0.05": interval["deviation_label_band_0.05"],
            }
        per_condition[condition] = {
            "by_alpha": alphas,
            "status": worst_status(statuses),
        }
    return {
        **per_condition,
        "worst_status": status_c4(intervals, 0.07),
        "secondary_worst_status_band_0.05": status_c4(intervals, 0.05),
    }


def _shape_claims(cells: dict[str, dict[str, Any]]) -> dict[str, Any]:
    c5: dict[str, Any] = {}
    c6: dict[str, Any] = {}
    c5_statuses: list[Status] = []
    c6_statuses: list[Status] = []
    c6_undefined = False
    for condition in CONDITIONS:
        cell = cells[condition]["M5"]
        c5_condition = _c5_condition(cell)
        c6_condition = _c6_condition(cell)
        c5[condition] = c5_condition
        c6[condition] = c6_condition
        c5_statuses.append(c5_condition["status"])
        if c6_condition["status"] == "not evaluated":
            c6_undefined = True
        else:
            c6_statuses.append(c6_condition["status"])
    c5["worst_status"] = worst_status(c5_statuses)
    c6["worst_status"] = "not evaluated" if c6_undefined else worst_status(c6_statuses)
    return {"C5": c5, "C6": c6}


def _c5_condition(cell: dict[str, Any]) -> dict[str, Any]:
    adjacent = cell["adjacent_grid_risk_differences"]
    points = [item["point"] for item in adjacent]
    lowers = [item["lower"] for item in adjacent]
    return _claim(
        status_c5(points, lowers),
        points,
        lowers,
        [],
        {
            "adjacent_lower_coverage_minus_higher": points,
            "intervals": [
                {"lower": item["lower"], "upper": item["upper"]} for item in adjacent
            ],
        },
    )


def _c6_condition(cell: dict[str, Any]) -> dict[str, Any]:
    enrichment = cell["enrichment"]
    observed = [enrichment[str(phi)]["observed_difference"] for phi in COVERAGE_GRID]
    adjusted = [enrichment[str(phi)]["adjusted_p_value"] for phi in COVERAGE_GRID]
    n_rejected = [enrichment[str(phi)]["n_rejected"] for phi in COVERAGE_GRID]
    if any(value is None for value in observed + adjusted):
        return {
            "status": "not evaluated",
            "reason": (
                "zero rejected cases at a grid coverage leaves the "
                "C6 permutation test undefined"
            ),
            "numbers": {
                "observed": observed,
                "adjusted_p_values": adjusted,
                "n_rejected": n_rejected,
            },
        }
    fractions = [Fraction(str(value)) for value in adjusted]
    status = status_c6(cast(Sequence[float], observed), fractions)
    return {
        "status": status,
        "numbers": {
            "observed": observed,
            "adjusted_p_values": [str(value) for value in fractions],
            "n_rejected": n_rejected,
        },
    }


def _all_claims(
    cells: dict[str, dict[str, Any]], conformal: dict[str, Any]
) -> dict[str, Any]:
    return {**_risk_claims(cells), "C4": _c4_claim(conformal), **_shape_claims(cells)}


def _validate_options(
    run_id: str,
    ensemble_run_ids: Sequence[str] | None,
    iterations: int,
    permutations: int,
    passes: int,
) -> None:
    if iterations < 1 or permutations < 1 or passes < 1:
        raise ValueError("iterations, permutations, and passes must be positive")
    if ensemble_run_ids is not None and (
        run_id in ensemble_run_ids
        or len(set(ensemble_run_ids)) != len(ensemble_run_ids)
    ):
        raise ValueError("ensemble_run_ids must be unique and exclude run_id")


def _git_sha() -> str:
    repository = Path(__file__).resolve().parents[3]
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
        cwd=repository,
    ).stdout.strip()


def _write_report(path: Path, document: dict[str, Any]) -> Path:
    payload = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    digest = hashlib.sha256(payload).hexdigest()
    _write_exclusive(path, payload)
    _write_exclusive(
        path.with_name(path.name + ".sha256"),
        f"{digest}  {path.name}\n".encode("ascii"),
    )
    return path


def _summary(
    run_id: str,
    checkpoint_hash: str,
    git_sha: str,
    absent_cells: list[dict[str, str]],
    iterations: int,
    permutations: int,
    seed: int,
    passes: int,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "checkpoint_hash": checkpoint_hash,
        "git_sha": git_sha,
        "seed": seed,
        "paired_bootstrap_seed": seed,
        "permutation_seed_base": seed,
        "conformal_bootstrap_seed_base": seed,
        "iterations": iterations,
        "permutations": permutations,
        "passes": passes,
        "absent_cells": absent_cells,
        "random_confidence_seed": seed,
        "seed_schedule": {
            "paired_bootstrap_indices": "seed",
            "permutation_at_coverage_index": "seed + coverage_index (0 through 4)",
            "monotonicity_at_condition_mechanism": (
                "seed + condition_index * 6 + mechanism_index"
            ),
            "conformal_carried_over_at_condition_alpha": (
                "seed + 10000 + condition_index * 100 + alpha_index"
            ),
            "conformal_refit_at_condition_alpha": (
                "seed + 20000 + condition_index * 100 + alpha_index"
            ),
            "random_confidence": "seed",
        },
        "BH_adjusted_fraction_encoding": "reduced rational strings",
        "seed_default_assumption": (
            "seed defaults to 0 because SAP and frozen analysis scripts use seed 0"
        ),
    }


def analyze_phase09(
    run_id: str,
    *,
    ensemble_run_ids: Sequence[str] | None = None,
    iterations: int = 2000,
    permutations: int = 10000,
    seed: int = 0,
    passes: int = 30,
) -> Path:
    """Write the frozen-artifact Phase 09 results JSON and SHA-256 sidecar."""
    _validate_options(run_id, ensemble_run_ids, iterations, permutations, passes)
    run_dir, record = _load_run(run_id)
    checkpoint_hash = str(record["checkpoint_hash"])
    report_path = run_dir / "phase09_analysis.json"
    if (
        report_path.exists()
        or report_path.with_name(report_path.name + ".sha256").exists()
    ):
        raise FileExistsError(f"Phase 09 analysis already exists: {report_path.name}")
    frames, (predictions, _metadata, mc_frame) = _load_condition_frames(
        run_id, run_dir, checkpoint_hash
    )
    ids, _baseline_labels = _patient_roster(frames, predictions, mc_frame)
    index_matrix = bootstrap_indices(len(ids), iterations, seed)
    aligned, full_temperature, full_cal_scaled = _aligned_conditions(
        frames, ids, passes
    )
    cells, absent_cells, member_hashes = _all_condition_cells(
        run_id,
        aligned,
        ids,
        ensemble_run_ids,
        index_matrix,
        iterations,
        permutations,
        seed,
    )
    # Calibration labels accompany the fitted full calibration probabilities.
    full_cal = _rows(frames["full"], "utsw_calibration", "full")
    full_cal_ids = sorted(full_cal["patient_id"].tolist())
    full_cal_labels = _aligned_values(full_cal, full_cal_ids)[2]
    conformal = _all_conformal_results(
        aligned, full_cal_scaled, full_cal_labels, iterations, seed
    )
    git_sha = _git_sha()
    document = {
        "schema": "phase09_analysis.v1",
        "provenance": {
            "run_id": run_id,
            "checkpoint_hash": checkpoint_hash,
            "git_sha": git_sha,
            "conditions": list(CONDITIONS),
            "mechanisms": list(MECHANISMS),
            "internal_test_patient_count": len(ids),
            "full_temperature": full_temperature,
            "ensemble_checkpoint_hashes": member_hashes,
        },
        "results_summary": _summary(
            run_id,
            checkpoint_hash,
            git_sha,
            absent_cells,
            iterations,
            permutations,
            seed,
            passes,
        ),
        "conditions": cells,
        "conformal": conformal,
        "claims": _all_claims(cells, conformal),
    }
    return _write_report(report_path, document)


def _all_condition_cells(
    run_id: str,
    aligned: dict[str, dict[str, Any]],
    ids: list[str],
    ensemble_run_ids: Sequence[str] | None,
    indices: np.ndarray,
    iterations: int,
    permutations: int,
    seed: int,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]], dict[str, str]]:
    cells: dict[str, dict[str, Any]] = {}
    absent: list[dict[str, str]] = []
    hashes: dict[str, str] = {}
    for condition in CONDITIONS:
        cells[condition], missing = _condition_cells(
            condition,
            aligned[condition],
            run_id,
            ids,
            ensemble_run_ids,
            hashes,
            indices,
            iterations,
            permutations,
            seed,
        )
        absent.extend(missing)
    return cells, absent, hashes


def _all_conformal_results(
    aligned: dict[str, dict[str, Any]],
    full_cal: np.ndarray,
    full_labels: np.ndarray,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    return {
        condition: _condition_conformal(
            condition, aligned[condition], full_cal, full_labels, iterations, seed
        )
        for condition in CONDITIONS
    }

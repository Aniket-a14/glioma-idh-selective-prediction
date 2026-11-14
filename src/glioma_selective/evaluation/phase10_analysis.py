"""Phase 10 S4: internal statistics from validated frozen predictions only."""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from fractions import Fraction
from numbers import Real
from pathlib import Path
from statistics import NormalDist
from typing import Any, cast

import numpy as np

from glioma_selective.calibration.temperature import apply_temperature, fit_temperature
from glioma_selective.evaluation.calibration_metrics import (
    brier_score,
    expected_calibration_error,
)
from glioma_selective.evaluation.condition_analysis import _rows
from glioma_selective.evaluation.phase06_report import _read_dice, average_precision
from glioma_selective.evaluation.phase09_analysis import (
    CONDITIONS,
    COVERAGE_GRID,
    _aligned_conditions,
    _aligned_values,
    _condition_scores,
    _git_sha,
    _load_condition_frames,
    _load_run,
    _patient_roster,
    _single_model_scores,
    _validate_artifact,
    _validate_options,
    _write_report,
)
from glioma_selective.evaluation.selective_metrics import selective_risk_at_coverage
from glioma_selective.selective.aurc import aurc_mean_over_cutoffs
from glioma_selective.statistics.delong import delong_paired_auroc
from glioma_selective.statistics.multiplicity import benjamini_hochberg
from glioma_selective.statistics.paired import paired_bootstrap_p
from glioma_selective.statistics.resampling import (
    bootstrap_indices,
    percentile_interval,
)
from glioma_selective.training.metrics import binary_auroc
from glioma_selective.utils import paths


@dataclass(frozen=True)
class _Estimate:
    point: float
    draws: np.ndarray

    def interval(self) -> dict[str, float]:
        lower, upper = percentile_interval(self.draws)
        return {"lower": lower, "upper": upper}


def _estimate(
    statistic: Callable[..., float], arrays: Sequence[np.ndarray], indices: np.ndarray
) -> _Estimate:
    return _Estimate(
        float(statistic(*arrays)),
        np.asarray([statistic(*(a[row] for a in arrays)) for row in indices]),
    )


def _aurc(scores: np.ndarray, errors: np.ndarray) -> float:
    return aurc_mean_over_cutoffs(scores.tolist(), errors.tolist())


def _ece(probabilities: np.ndarray, labels: np.ndarray) -> float:
    return expected_calibration_error(probabilities, labels, n_bins=10)


def _difference(a: _Estimate, b: _Estimate, family_id: str, n: int) -> dict[str, Any]:
    """Subtract draws already evaluated on the single shared patient matrix."""
    draws = a.draws - b.draws
    lower, upper = percentile_interval(draws)
    return {
        "status": "computed",
        "family_member_id": family_id,
        "point": a.point - b.point,
        "lower": lower,
        "upper": upper,
        "p_value": str(paired_bootstrap_p(draws)),
        "n": n,
    }


def _metric_interval(estimate: _Estimate) -> dict[str, Any]:
    return {
        "point": estimate.point,
        "bootstrap_95_interval": {
            **estimate.interval(),
            "valid_draws": len(estimate.draws),
        },
    }


def _hanley_mcneil(auc: float, positives: int, negatives: int) -> dict[str, float]:
    """Normal 95% interval, Hanley & McNeil (1982), eq. 1 and Q approximations.

    Q1=A/(2-A), Q2=2*A*A/(1+A); n_A is positive, n_N negative.
    Source: https://www.math.ucdavis.edu/~saito/data/roc/hanley-mcneil-auc.pdf
    """
    q1 = auc / (2 - auc)
    q2 = 2 * auc * auc / (1 + auc)
    variance = (
        auc * (1 - auc)
        + (positives - 1) * (q1 - auc * auc)
        + (negatives - 1) * (q2 - auc * auc)
    ) / (positives * negatives)
    half_width = NormalDist().inv_cdf(0.975) * math.sqrt(variance)
    return {"lower": auc - half_width, "upper": auc + half_width}


def _valid_class_draws(labels: np.ndarray, indices: np.ndarray) -> np.ndarray:
    counts = labels[indices].sum(axis=1)
    valid = (counts > 0) & (counts < len(labels))
    if not valid.any():
        raise ValueError("all bootstrap resamples had only one class")
    return np.asarray(valid, dtype=np.bool_)


def _full_run_arrays(frame: Any, ids: list[str]) -> dict[str, Any]:
    cal = _rows(frame, "utsw_calibration", "full")
    cal_ids = sorted(cal["patient_id"].tolist())
    logits, _, labels = _aligned_values(cal, cal_ids)
    temperature = fit_temperature(logits, labels)
    test = _rows(frame, "utsw_internal_test", "full")
    test_logits, raw_p, test_labels = _aligned_values(test, ids)
    return {
        "logits": test_logits,
        "raw_p": raw_p,
        "scaled_full": apply_temperature(test_logits, temperature),
        "labels": test_labels,
        "temperature": temperature,
    }


def _run_metrics(
    run_id: str,
    run_dir: Path,
    checkpoint: str,
    arrays: dict[str, Any],
    scores: dict[str, list[float]],
    errors: dict[str, np.ndarray],
    indices: np.ndarray,
    valid: np.ndarray,
    aurc: _Estimate,
) -> tuple[dict[str, Any], dict[str, _Estimate]]:
    labels, raw_p = arrays["labels"], arrays["raw_p"]
    valid_indices = indices[valid]
    auc = _estimate(binary_auroc, (raw_p, labels), valid_indices)
    ap = _estimate(average_precision, (raw_p, labels), valid_indices)
    auc_report = _metric_interval(auc)
    ap_report = _metric_interval(ap)
    for report in (auc_report, ap_report):
        report["bootstrap_95_interval"]["skipped_single_class_draws"] = int(
            (~valid).sum()
        )
    hm = _hanley_mcneil(auc.point, int(labels.sum()), len(labels) - int(labels.sum()))
    auc_report["hanley_mcneil_95_interval"] = hm
    boot = auc.interval()
    auc_report["quoted"] = (
        "hanley_mcneil_95_interval"
        if hm["upper"] - hm["lower"] > boot["upper"] - boot["lower"]
        else "bootstrap_95_interval"
    )
    calibration: dict[str, Any] = {}
    estimates: dict[str, _Estimate] = {}
    for mechanism, probabilities in (("M1", raw_p), ("M2", arrays["scaled_full"])):
        metrics = {}
        for name, statistic in (("ece", _ece), ("brier", brier_score)):
            estimate = _estimate(statistic, (probabilities, labels), indices)
            estimates[f"{mechanism}:{name}"] = estimate
            metrics[name] = _metric_interval(estimate)
        calibration[mechanism] = {
            "probability": "raw" if mechanism == "M1" else "temperature_scaled",
            **metrics,
        }
    selective = {}
    score_array = np.asarray(scores["M5"])
    for coverage in COVERAGE_GRID:

        def risk(s: np.ndarray, e: np.ndarray, target: float = coverage) -> float:
            return selective_risk_at_coverage(s.tolist(), e.tolist(), target)[1]

        attained, _ = selective_risk_at_coverage(
            scores["M5"], errors["M5"].tolist(), coverage
        )
        selective[str(coverage)] = {
            **_metric_interval(_estimate(risk, (score_array, errors["M5"]), indices)),
            "attained_coverage": attained,
        }
    dice = _read_dice(
        run_dir / "segmentation_dice.json", run_id=run_id, checkpoint_hash=checkpoint
    )
    try:
        internal_dice = dice["splits"]["internal_test"]
        if not internal_dice["per_channel"]:
            raise ValueError("internal-test segmentation Dice needs per-channel values")
    except (KeyError, TypeError) as error:
        raise ValueError(
            "internal-test per-channel segmentation Dice is required"
        ) from error
    return {
        "status": "computed",
        "run_id": run_id,
        "checkpoint_hash": checkpoint,
        "n": len(labels),
        "temperature": arrays["temperature"],
        "coverage": 1.0,
        "auroc": auc_report,
        "auprc": ap_report,
        "calibration": calibration,
        "aurc_mean_over_cutoffs": _metric_interval(aurc),
        "selective_mechanism": "M5",
        "selective_risk_at_coverage": selective,
        "segmentation_dice": internal_dice,
        "hd95": {"status": "absent", "reason": "needs a segmentation freeze (T10.10)"},
    }, estimates


def _family(include_egd: bool) -> list[dict[str, str]]:
    """Enumerate SAP section 6 without reading any external artifacts."""
    descriptions = {
        "A1": "AURC(M5) - AURC(M3), full",
        "A2": "AURC(M5) - AURC(M4), full",
        "A3": "AURC(M3) - AURC(M4), full",
        **{
            f"B{i}": f"AURC(M5, {c}) - AURC(M5, full)"
            for i, c in enumerate(CONDITIONS[1:], 1)
        },
        "D1": "ECE(M1) - ECE(M2), full",
        "D2": "Brier(M1) - Brier(M2), full",
        "E1": "AUROC(R7) - AUROC(R2), full",
        "E2": "AURC(R7) - AURC(R2), full",
        "E3": "AUROC(R8) - AUROC(R2), full",
        "E4": "AURC(R8) - AURC(R2), full",
    }
    rows = []
    for cohort in ("utsw", "ucsf_pdgm", *(("egd",) if include_egd else ())):
        for local_id, comparison in descriptions.items():
            rows.append(
                {
                    "id": f"{cohort}:{local_id}",
                    "block": local_id[0],
                    "comparison": comparison,
                    "cohort": cohort,
                    "status": "absent" if cohort == "utsw" else "pending_external",
                }
            )
        if cohort != "utsw":
            rows.append(
                {
                    "id": f"{cohort}:C1",
                    "block": "C",
                    "comparison": (
                        f"AURC(M5, {cohort}) - AURC(M5, utsw), full; unpaired"
                    ),
                    "cohort": cohort,
                    "status": "pending_external",
                }
            )
    return rows


def _supplementary(comparisons: dict[str, Any]) -> dict[str, Any]:
    computed = [
        (key, row) for key, row in comparisons.items() if row["status"] == "computed"
    ]
    # Preserve rational p-values for reporting; the existing BH helper consumes
    # real-valued p-values and converts their decimal repr to exact fractions.
    adjusted, rejected = benjamini_hochberg(
        cast(Sequence[Real], [float(Fraction(row["p_value"])) for _, row in computed]),
        0.05,
    )
    return {
        "label": "supplementary; not the pre-registered family (D-052)",
        "q": 0.05,
        "members": [
            {
                "family_member_id": row["family_member_id"],
                "adjusted_p_value": str(p),
                "reject": reject,
            }
            for (_, row), p, reject in zip(computed, adjusted, rejected, strict=True)
        ],
    }


def _ablation(
    run_id: str | None,
    ids: list[str],
    labels: np.ndarray,
) -> (
    tuple[Path, str, dict[str, Any], dict[str, list[float]], dict[str, np.ndarray]]
    | None
):
    if run_id is None:
        return None
    run_dir = paths.experiments_dir() / run_id
    path = run_dir / "predictions.parquet"
    if not path.exists() and not path.with_name(path.name + ".sha256").exists():
        return None
    run_dir, record = _load_run(run_id)
    checkpoint = str(record["checkpoint_hash"])
    frame = _validate_artifact(path, run_id, checkpoint)
    other_ids, other_labels = _patient_roster({"full": frame}, frame, None)
    if other_ids != ids or not np.array_equal(other_labels, labels):
        raise ValueError("ablation internal-test patient sets or labels differ from R2")
    arrays = _full_run_arrays(frame, ids)
    scores, errors = _single_model_scores(
        arrays["raw_p"], arrays["scaled_full"], labels
    )
    return run_dir, checkpoint, arrays, scores, errors


def _validate_request(
    run_id: str,
    ensemble_run_ids: Sequence[str],
    r7_run_id: str | None,
    r8_run_id: str | None,
    iterations: int,
) -> None:
    _validate_options(run_id, ensemble_run_ids, iterations, 1, 30)
    if (
        isinstance(iterations, bool)
        or not isinstance(iterations, int)
        or iterations < 1000
    ):
        raise ValueError("iterations must be an integer of at least 1000")
    if len(ensemble_run_ids) != 4:
        raise ValueError(
            "ensemble_run_ids must contain R3-R6 (four members besides R2)"
        )
    supplied = [
        run_id,
        *ensemble_run_ids,
        *[x for x in (r7_run_id, r8_run_id) if x is not None],
    ]
    if len(supplied) != len(set(supplied)):
        raise ValueError("R2, ensemble members, R7 and R8 must be distinct runs")


def _validate_ensemble_labels(
    ensemble_run_ids: Sequence[str],
    ids: list[str],
    labels: np.ndarray,
) -> None:
    # The Phase 09 ensemble builder aligns IDs; also verify their labels here.
    for member in ensemble_run_ids:
        member_dir, member_record = _load_run(member)
        member_frames, (member_predictions, _, member_mc) = _load_condition_frames(
            member, member_dir, str(member_record["checkpoint_hash"])
        )
        member_ids, member_labels = _patient_roster(
            member_frames, member_predictions, member_mc
        )
        if member_ids != ids or not np.array_equal(member_labels, labels):
            raise ValueError(
                "ensemble internal-test patient sets or labels differ from R2"
            )


def _cell_aurcs(
    cells: dict[str, tuple[dict[str, list[float]], dict[str, np.ndarray]]],
    indices: np.ndarray,
) -> dict[tuple[str, str], _Estimate]:
    return {
        (condition, mechanism): _estimate(
            _aurc, (np.asarray(scores[mechanism]), errors[mechanism]), indices
        )
        for condition, (scores, errors) in cells.items()
        for mechanism in (("M3", "M4", "M5") if condition == "full" else ("M5",))
    }


def _internal_comparisons(
    aurcs: dict[tuple[str, str], _Estimate],
    calibration: dict[str, _Estimate],
    n: int,
) -> dict[str, Any]:
    pairs = {
        "A1": (aurcs["full", "M5"], aurcs["full", "M3"]),
        "A2": (aurcs["full", "M5"], aurcs["full", "M4"]),
        "A3": (aurcs["full", "M3"], aurcs["full", "M4"]),
        **{
            f"B{i}": (aurcs[c, "M5"], aurcs["full", "M5"])
            for i, c in enumerate(CONDITIONS[1:], 1)
        },
        "D1": (calibration["M1:ece"], calibration["M2:ece"]),
        "D2": (calibration["M1:brier"], calibration["M2:brier"]),
    }
    return {key: _difference(a, b, f"utsw:{key}", n) for key, (a, b) in pairs.items()}


def _ablation_results(
    name: str,
    ablation_id: str | None,
    offset: int,
    full_arrays: dict[str, Any],
    ids: list[str],
    labels: np.ndarray,
    indices: np.ndarray,
    valid: np.ndarray,
    primary_aurc: _Estimate,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    data = _ablation(ablation_id, ids, labels)
    if data is None:
        absent = {"status": "absent", "reason": f"{name} has no frozen predictions"}
        return dict(absent), dict(absent), dict(absent)
    directory, digest, arrays, scores, errors = data
    estimate = _estimate(_aurc, (np.asarray(scores["M5"]), errors["M5"]), indices)
    assert ablation_id is not None
    run, _ = _run_metrics(
        ablation_id,
        directory,
        digest,
        arrays,
        scores,
        errors,
        indices,
        valid,
        estimate,
    )
    test = delong_paired_auroc(arrays["logits"], full_arrays["logits"], labels)
    auc_a = _estimate(binary_auroc, (arrays["logits"], labels), indices[valid])
    auc_b = _estimate(binary_auroc, (full_arrays["logits"], labels), indices[valid])
    row = _difference(auc_a, auc_b, f"utsw:E{offset}", len(ids))
    row.update(
        point=test.difference,
        p_value=test.p_value,
        method="delong_paired_auroc",
        valid_draws=int(valid.sum()),
        skipped_single_class_draws=int((~valid).sum()),
    )
    return (
        run,
        row,
        _difference(estimate, primary_aurc, f"utsw:E{offset + 1}", len(ids)),
    )


def analyze_phase10(
    run_id: str,
    *,
    ensemble_run_ids: Sequence[str],
    r7_run_id: str | None = None,
    r8_run_id: str | None = None,
    iterations: int = 2000,
    seed: int = 0,
    include_egd: bool = False,
) -> Path:
    """Write S4 raw internal comparisons, intervals, family listing and sidecar.

    ``include_egd`` extends the family listing only; external artifacts are never
    opened. Production uses 2000 draws; fewer than 1000 are rejected.
    """
    _validate_request(run_id, ensemble_run_ids, r7_run_id, r8_run_id, iterations)
    run_dir, record = _load_run(run_id)
    report_path = run_dir / "phase10_analysis.json"
    if (
        report_path.exists()
        or report_path.with_name(report_path.name + ".sha256").exists()
    ):
        raise FileExistsError(f"Phase 10 analysis already exists: {report_path.name}")
    checkpoint = str(record["checkpoint_hash"])
    frames, (predictions, _, mc_frame) = _load_condition_frames(
        run_id, run_dir, checkpoint
    )
    ids, labels = _patient_roster(frames, predictions, mc_frame)
    indices = bootstrap_indices(len(ids), iterations, seed)
    valid = _valid_class_draws(labels, indices)
    aligned, temperature, _ = _aligned_conditions(frames, ids, 30)
    hashes: dict[str, str] = {}
    cells = {
        c: _condition_scores(c, aligned[c], run_id, ids, ensemble_run_ids, hashes)
        for c in CONDITIONS
    }
    _validate_ensemble_labels(ensemble_run_ids, ids, labels)
    aurcs = _cell_aurcs(cells, indices)
    full_arrays = {
        **aligned["full"],
        "temperature": temperature,
        "logits": _aligned_values(
            _rows(frames["full"], "utsw_internal_test", "full"), ids
        )[0],
    }
    runs: dict[str, Any] = {}
    runs["R2"], calibration = _run_metrics(
        run_id,
        run_dir,
        checkpoint,
        full_arrays,
        *cells["full"],
        indices,
        valid,
        aurcs["full", "M5"],
    )
    comparisons = _internal_comparisons(aurcs, calibration, len(ids))
    for name, ablation_id, offset in (("R7", r7_run_id, 1), ("R8", r8_run_id, 3)):
        runs[name], auroc_row, aurc_row = _ablation_results(
            name,
            ablation_id,
            offset,
            full_arrays,
            ids,
            labels,
            indices,
            valid,
            aurcs["full", "M5"],
        )
        comparisons[f"E{offset}"] = auroc_row
        comparisons[f"E{offset + 1}"] = aurc_row
    family = _family(include_egd)
    for row in family:
        if row["cohort"] == "utsw":
            row["status"] = comparisons[row["id"].split(":")[1]]["status"]
    return _write_report(
        report_path,
        {
            "schema": "phase10_analysis.v1",
            "provenance": {
                "run_id": run_id,
                "checkpoint_hash": checkpoint,
                "git_sha": _git_sha(),
                "ensemble_checkpoint_hashes": hashes,
                "internal_test_patient_count": len(ids),
                "iterations": iterations,
                "seed": seed,
                "bootstrap": "one shared patient-index matrix",
            },
            "confirmatory": comparisons,
            "bh_family": family,
            "supplementary_bh_internal_only": _supplementary(comparisons),
            "runs": runs,
        },
    )

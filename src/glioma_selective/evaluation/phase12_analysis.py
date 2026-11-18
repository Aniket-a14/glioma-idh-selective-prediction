"""Phase 12 analysis of frozen external predictions (UCSF-PDGM), behind Gate E.

Reuses the Phase 09 and Phase 10 builders unchanged apart from their optional
``test_cohort`` and ``cohort_label`` arguments, so the external numbers come from
the same code paths as the internal ones. Calibration stays on the UTSW
calibration split: the temperature and the conformal quantile are carried over
and nothing is fitted on external rows (``PHASE_12_EXTERNAL_EVALUATION.md``).

Every external file is checked against the signed freeze manifest it was frozen
under before any number is computed. The firewall is called first, so this
module reads no external label unless Gate E is passed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from glioma_selective.evaluation import firewall
from glioma_selective.evaluation.condition_analysis import _read_json_with_sidecar
from glioma_selective.evaluation.phase09_analysis import (
    CONDITIONS,
    _aligned_conditions,
    _aligned_values,
    _all_claims,
    _all_condition_cells,
    _all_conformal_results,
    _condition_scores,
    _git_sha,
    _load_condition_frames,
    _load_run,
    _measure_cell,
    _patient_roster,
    _summary,
    _validate_artifact,
    _write_report,
)
from glioma_selective.evaluation.phase10_analysis import (
    _ablation_results,
    _aurc,
    _cell_aurcs,
    _difference,
    _estimate,
    _full_run_arrays,
    _internal_comparisons,
    _run_metrics,
    _valid_class_draws,
)
from glioma_selective.selective.abstention import confidence_scores
from glioma_selective.statistics.resampling import bootstrap_indices
from glioma_selective.tracking.predictions import read_prediction_artifact
from glioma_selective.utils import paths

__all__ = ["FreezeProvenanceError", "analyze_external"]

PRIMARY_ROLE = "primary_seed0"
ENSEMBLE_ROLES = (
    "ensemble_seed1",
    "ensemble_seed2",
    "ensemble_seed3",
    "ensemble_seed4",
)
M6_ROLE = "m6_comparator_r1"
ABLATION_ROLES = {"R7": "ablation_r7_whole_brain", "R8": "ablation_r8_two_stage"}
_TEMPERATURE_TOLERANCE = 1e-9


class FreezeProvenanceError(ValueError):
    """An external artifact does not match the signed freeze manifest."""


@dataclass(frozen=True)
class _ExternalRun:
    directory: Path
    run_id: str
    cohort: str
    manifest_digest: str
    manifest: dict[str, Any]
    roles: dict[str, dict[str, Any]]


def _open_external_run(cohort: str, run_id: str, manifest_path: Path) -> _ExternalRun:
    """Verify the report, the signed manifest and the run records for one run."""
    firewall._check_manifest(manifest_path)  # signature, sidecar, required fields
    payload = manifest_path.read_bytes()
    manifest = json.loads(payload)
    digest = hashlib.sha256(payload).hexdigest()
    directory = paths.experiments_dir() / "external_frozen" / cohort / run_id
    report = _read_json_with_sidecar(directory / "report.json")
    checks = {
        "run_id": report.get("run_id") == run_id,
        "cohort": report.get("cohort") == cohort,
        "freeze_manifest_sha256": report.get("freeze_manifest_sha256") == digest,
        "git_sha": report.get("git_sha") == manifest["code_commit_sha"],
        "git_sha_unchanged": report.get("git_sha_unchanged") is True,
        "model_checkpoints": report.get("model_checkpoints")
        == manifest["model_checkpoints"],
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise FreezeProvenanceError(
            f"external report does not match its manifest: {', '.join(failed)}"
        )
    roles: dict[str, dict[str, Any]] = {}
    for entry in manifest["model_checkpoints"]:
        _directory, record = _load_run(entry["run_id"])
        if record["checkpoint_hash"] != entry["sha256"]:
            raise FreezeProvenanceError(
                f"manifest checkpoint hash differs from run record {entry['run_id']}"
            )
        roles[entry["role"]] = entry
    return _ExternalRun(directory, run_id, cohort, digest, manifest, roles)


def _external_frames(run: _ExternalRun, role: str) -> dict[str, Any]:
    """Per-condition frames of one member, checked against metadata and manifest."""
    if role not in run.roles:
        raise FreezeProvenanceError(f"manifest has no checkpoint role {role}")
    entry = run.roles[role]
    frames = {}
    for condition in CONDITIONS:
        path = run.directory / role / f"{condition}.parquet"
        frame, metadata = read_prediction_artifact(path)
        expected = {
            "run_id": run.run_id,
            "checkpoint_hash": entry["sha256"],
            "git_sha": run.manifest["code_commit_sha"],
            "freeze_manifest_sha256": run.manifest_digest,
        }
        for key, value in expected.items():
            if metadata.get(key) != value:
                raise FreezeProvenanceError(f"{path.name} metadata {key} mismatch")
        if not bool((frame["run_id"] == run.run_id).all()) or not bool(
            (frame["checkpoint_hash"] == entry["sha256"]).all()
        ):
            raise FreezeProvenanceError(f"{path.name} rows do not match the manifest")
        if not bool((frame["modality_condition"] == condition).all()):
            raise FreezeProvenanceError(f"{path.name} contains another condition")
        if not bool((frame["cohort"] == run.cohort).all()):
            raise FreezeProvenanceError(f"{path.name} contains another cohort")
        frames[condition] = frame
    return frames


def _combine(internal: Any, external: Any) -> Any:
    """UTSW calibration rows plus the external rows, for the shared builders."""
    return pd.concat([internal, external], ignore_index=True)


def _aligned_p(frame: Any, ids: list[str]) -> np.ndarray:
    return np.asarray(frame.set_index("patient_id").loc[ids]["p_hat"], dtype=np.float64)


def _aligned_labels(frame: Any, ids: list[str]) -> np.ndarray:
    return np.asarray(frame.set_index("patient_id").loc[ids]["label"], dtype=np.int64)


def _m6_cells(
    run: _ExternalRun,
    ids: list[str],
    labels: np.ndarray,
    indices: np.ndarray,
    iterations: int,
    permutations: int,
    seed: int,
) -> dict[str, Any]:
    frames = _external_frames(run, M6_ROLE)
    cells = {}
    for condition in CONDITIONS:
        raw_p = _aligned_p(frames[condition], ids)
        if not np.array_equal(_aligned_labels(frames[condition], ids), labels):
            raise FreezeProvenanceError("M6 comparator labels differ from the primary")
        loss = ((raw_p >= 0.5) != (labels == 1)).astype(np.int64)
        cells[condition] = _measure_cell(
            condition,
            "M6",
            confidence_scores(raw_p.tolist()),
            loss,
            indices,
            iterations,
            permutations,
            seed,
        )
    return cells


def _external_claims(
    cells: dict[str, Any], conformal: dict[str, Any]
) -> dict[str, Any]:
    """C3 to C6 on the external cohort, by the pre-registered rules (SAP section 5).

    C3 is the C1 rule on the external ``full`` condition, the per-condition
    results being secondary; C4 to C6 are unchanged.
    """
    claims = _all_claims(cells, conformal)
    secondary = {k: v for k, v in claims["C2"].items() if k != "worst_status"}
    return {
        "C3": {
            "full": claims["C1"]["full"],
            "status": claims["C1"]["full"]["status"],
            "secondary_by_condition": secondary,
            "secondary_worst_status": claims["C2"]["worst_status"],
        },
        "C4": claims["C4"],
        "C5": claims["C5"],
        "C6": claims["C6"],
    }


def _check_temperature(run: _ExternalRun, fitted: float) -> None:
    carried = run.manifest["calibration_parameters"]["temperature"]
    if abs(float(carried) - fitted) > _TEMPERATURE_TOLERANCE:
        raise FreezeProvenanceError(
            "the manifest temperature differs from the UTSW calibration fit"
        )


def _external_ablation(
    run: _ExternalRun,
    role: str,
    ids: list[str],
    labels: np.ndarray,
    cohort: str,
) -> tuple[Path, str, dict[str, Any], dict[str, list[float]], dict[str, np.ndarray]]:
    """The R7 or R8 ``full`` rows on the external cohort, in `_ablation`'s shape."""
    from glioma_selective.evaluation.phase09_analysis import _single_model_scores

    entry = run.roles[role]
    external = _external_frames(run, role)["full"]
    run_dir, record = _load_run(entry["run_id"])
    internal = _validate_artifact(
        run_dir / "predictions.parquet", entry["run_id"], str(record["checkpoint_hash"])
    )
    combined = _combine(internal, external)
    other_ids, other_labels = _patient_roster(
        {"full": combined}, combined, None, cohort
    )
    if other_ids != ids or not np.array_equal(other_labels, labels):
        raise FreezeProvenanceError("ablation patients or labels differ from the run")
    arrays = _full_run_arrays(combined, ids, cohort)
    scores, errors = _single_model_scores(
        arrays["raw_p"], arrays["scaled_full"], labels
    )
    return run_dir, entry["sha256"], arrays, scores, errors


def analyze_external(
    run_id: str,
    external_run_id: str,
    manifest_path: Path,
    *,
    ablation_run_id: str | None = None,
    ablation_manifest_path: Path | None = None,
    cohort: str = "ucsf_pdgm",
    iterations: int = 2000,
    permutations: int = 10000,
    seed: int = 0,
) -> tuple[Path, Path]:
    """Write ``phase09_external_analysis.json`` and ``phase10_external_analysis.json``.

    ``run_id`` is the primary internal run (R2), the source of the UTSW
    calibration rows. ``external_run_id`` is the frozen external run scored under
    ``manifest_path``. The R7 and R8 comparisons come from a second frozen run
    (``ablation_run_id``, D-060) with its own signed manifest; without it block E
    is written as pending.
    """
    firewall.assert_external_eval_authorized(cohort)
    if iterations < 1000 or permutations < 1:
        raise ValueError("iterations must be at least 1000 and permutations positive")
    if (ablation_run_id is None) != (ablation_manifest_path is None):
        raise ValueError("ablation run id and manifest must be given together")
    run = _open_external_run(cohort, external_run_id, manifest_path)
    out09 = run.directory / "phase09_external_analysis.json"
    out10 = run.directory / "phase10_external_analysis.json"
    for target in (out09, out10):
        if target.exists() or target.with_name(target.name + ".sha256").exists():
            raise FileExistsError(f"{target.name} already exists")

    run_dir, record = _load_run(run_id)
    checkpoint = str(record["checkpoint_hash"])
    if run.roles[PRIMARY_ROLE]["run_id"] != run_id:
        raise FreezeProvenanceError("manifest primary run differs from run_id")
    internal_frames, _ = _load_condition_frames(run_id, run_dir, checkpoint)
    primary = _external_frames(run, PRIMARY_ROLE)
    frames = {c: _combine(internal_frames[c], primary[c]) for c in CONDITIONS}
    ids, labels = _patient_roster(frames, frames["full"], None, cohort)
    aligned, temperature, full_cal_scaled = _aligned_conditions(frames, ids, 30, cohort)
    _check_temperature(run, temperature)

    members = [primary] + [_external_frames(run, role) for role in ENSEMBLE_ROLES]
    for condition in CONDITIONS:
        for member in members[1:]:
            if not np.array_equal(_aligned_labels(member[condition], ids), labels):
                raise FreezeProvenanceError("ensemble member labels differ")
        aligned[condition]["member_matrix"] = np.column_stack(
            [_aligned_p(member[condition], ids) for member in members]
        )

    indices = bootstrap_indices(len(ids), iterations, seed)
    cells, absent, _hashes = _all_condition_cells(
        run_id, aligned, ids, None, indices, iterations, permutations, seed
    )
    m6 = _m6_cells(run, ids, labels, indices, iterations, permutations, seed)
    for condition, cell in m6.items():
        cells[condition]["M6"] = cell
    absent = [item for item in absent if item["mechanism"] != "M6"]
    cal_rows = internal_frames["full"]
    cal_rows = cal_rows[cal_rows["cohort"] == "utsw_calibration"]
    full_cal_labels = _aligned_values(cal_rows, sorted(cal_rows["patient_id"]))[2]
    conformal = _all_conformal_results(
        aligned, full_cal_scaled, full_cal_labels, iterations, seed
    )
    git_sha = _git_sha()
    provenance = {
        "run_id": run_id,
        "checkpoint_hash": checkpoint,
        "git_sha": git_sha,
        "conditions": list(CONDITIONS),
        "test_cohort": cohort,
        "test_patient_count": len(ids),
        "external_run_id": external_run_id,
        "freeze_manifest_sha256": run.manifest_digest,
        "full_temperature": temperature,
        "calibration": "UTSW calibration split only; nothing fitted on external rows",
    }
    document09 = {
        "schema": "phase09_analysis.v1",
        "provenance": provenance,
        "results_summary": _summary(
            run_id, checkpoint, git_sha, absent, iterations, permutations, seed, 30
        ),
        "conditions": cells,
        "conformal": conformal,
        "claims": _external_claims(cells, conformal),
    }

    # Phase 10 external statistics: blocks A, B, C, D and (second run) E.
    valid = _valid_class_draws(labels, indices)
    score_cells = {
        c: _condition_scores(c, aligned[c], run_id, ids, None, {}) for c in CONDITIONS
    }
    aurcs = _cell_aurcs(score_cells, indices)
    full_arrays = {
        **aligned["full"],
        "temperature": temperature,
        "logits": _aligned_values(
            frames["full"][frames["full"]["cohort"] == cohort], ids
        )[0],
    }
    runs: dict[str, Any] = {}
    runs["R2"], calibration = _run_metrics(
        run_id,
        run_dir,
        checkpoint,
        full_arrays,
        *score_cells["full"],
        indices,
        valid,
        aurcs["full", "M5"],
        include_segmentation=False,
    )
    comparisons = _internal_comparisons(aurcs, calibration, len(ids), cohort)
    comparisons["C1"] = _block_c(
        run_id, internal_frames, aurcs["full", "M5"], cohort, iterations, seed, len(ids)
    )
    ablation_run = (
        _open_external_run(cohort, ablation_run_id, ablation_manifest_path)
        if ablation_run_id is not None and ablation_manifest_path is not None
        else None
    )
    for name, offset in (("R7", 1), ("R8", 3)):
        if ablation_run is None:
            absent_row = {
                "status": "pending_external",
                "reason": "needs the second frozen run (D-060)",
            }
            runs[name] = dict(absent_row)
            comparisons[f"E{offset}"] = dict(absent_row)
            comparisons[f"E{offset + 1}"] = dict(absent_row)
            continue
        data = _external_ablation(
            ablation_run, ABLATION_ROLES[name], ids, labels, cohort
        )
        runs[name], auroc_row, aurc_row = _ablation_results(
            name,
            ablation_run.roles[ABLATION_ROLES[name]]["run_id"],
            offset,
            full_arrays,
            ids,
            labels,
            indices,
            valid,
            aurcs["full", "M5"],
            data=data,
            cohort_label=cohort,
            include_segmentation=False,
        )
        comparisons[f"E{offset}"] = auroc_row
        comparisons[f"E{offset + 1}"] = aurc_row
    document10 = {
        "schema": "phase10_external_analysis.v1",
        "provenance": {
            **provenance,
            "iterations": iterations,
            "seed": seed,
            "bootstrap": "one shared patient-index matrix per cohort",
            "ablation_external_run_id": ablation_run_id,
            "ablation_freeze_manifest_sha256": (
                ablation_run.manifest_digest if ablation_run else None
            ),
        },
        "confirmatory": comparisons,
        "family": [
            {
                "id": f"{cohort}:{key}",
                "status": row["status"],
                "p_value": row.get("p_value"),
            }
            for key, row in comparisons.items()
        ],
        "runs": runs,
    }
    return _write_report(out09, document09), _write_report(out10, document10)


def _block_c(
    run_id: str,
    internal_frames: dict[str, Any],
    external_aurc: Any,
    cohort: str,
    iterations: int,
    seed: int,
    n_external: int,
) -> dict[str, Any]:
    """AURC(M5, external) minus AURC(M5, UTSW), independent resamples (SAP 4)."""
    utsw_ids, _ = _patient_roster(internal_frames, internal_frames["full"], None)
    utsw_aligned, _t, _s = _aligned_conditions(internal_frames, utsw_ids, 30)
    scores, errors = _condition_scores(
        "full", utsw_aligned["full"], run_id, utsw_ids, None, {}
    )
    utsw_indices = bootstrap_indices(len(utsw_ids), iterations, seed)
    utsw = _estimate(_aurc, (np.asarray(scores["M5"]), errors["M5"]), utsw_indices)
    row = _difference(external_aurc, utsw, f"{cohort}:C1", n_external)
    row.update(
        method="unpaired_independent_resamples",
        n_reference=len(utsw_ids),
    )
    return row

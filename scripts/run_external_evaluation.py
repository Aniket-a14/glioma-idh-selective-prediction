#!/usr/bin/env python3
"""Freeze external predictions once, behind Gate E; print counts only."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# Match the existing freeze CLIs when executed as a script with PYTHONPATH=src.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from glioma_selective.data.dataset import IDHDataset
from glioma_selective.evaluation import firewall
from glioma_selective.evaluation.condition_sweep import (
    _score_condition_split,
    modality_channel_indices,
)
from glioma_selective.evaluation.conditions import load_condition_grid
from glioma_selective.evaluation.freeze import model_config_from_record
from glioma_selective.evaluation.freeze_manifest import git_state
from glioma_selective.evaluation.freeze_mc_dropout import (
    _load_record,
    _resolve_device,
    _write_exclusive,
)
from glioma_selective.leakage.cohort_manifest import (
    build_real_retained_rosters,
    verify_roster_digest,
)
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.models.segresnet import build_model
from glioma_selective.preprocessing.normalize import load_normalization_stats
from glioma_selective.tracking.predictions import write_prediction_artifact
from glioma_selective.training.checkpoint import load_model_weights
from glioma_selective.utils import paths

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
# Tests inject a stand-in factory here and register its name with the firewall.
_COHORT_DATASETS = {"ucsf_pdgm": (Cohort.UCSF_PDGM, IDHDataset)}


class FreezeMismatchError(ValueError):
    """A frozen input differs from the signed manifest; inference is refused."""


def _component(value: str) -> str:
    if not value or value in {".", ".."} or Path(value).name != value:
        raise ValueError("run ID and checkpoint role must be single path components")
    return value


def _resolve(value: str) -> Path:
    roots = {
        "repo": REPOSITORY_ROOT,
        "data": paths.data_root(),
        "artifacts": paths.artifact_root(),
    }
    # The conditions literal in freeze_spec.json uses a repository-relative path.
    root_name, relative = value.split(":", 1) if ":" in value else ("repo", value)
    if root_name not in roots or Path(relative).is_absolute():
        raise FreezeMismatchError("invalid frozen input path")
    root = roots[root_name].resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise FreezeMismatchError("frozen input path escapes its root")
    return target


def _check_hash(value: str, expected: str, field: str) -> Path:
    target = _resolve(value)
    if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
        raise FreezeMismatchError(f"{field} hash mismatch")
    return target


def _verify_inputs(manifest: dict[str, Any], cohort: str) -> tuple[Any, Any, Any]:
    """Verify every contract input before dataset construction or any writes."""
    try:
        for checkpoint in manifest["model_checkpoints"]:
            _component(checkpoint["role"])
            _check_hash(checkpoint["path"], checkpoint["sha256"], "checkpoint")
        for field in ("normalization_statistics", "exclusion_manifest"):
            entry = manifest[field]
            _check_hash(entry["path"], entry["sha256"], field)
        preprocessing = manifest["preprocessing"]
        _check_hash(
            preprocessing["config_path"],
            preprocessing["config_sha256"],
            "preprocessing",
        )
        conditions = manifest["missing_modality_conditions"]
        config = _check_hash(
            conditions["config"], conditions["config_sha256"], "conditions"
        )
        grid = load_condition_grid(config)
        if cohort not in conditions["cohorts"]:
            raise FreezeMismatchError("cohort is not frozen in the conditions literal")
        if [condition.id for condition in grid.modality_conditions] != conditions[
            "conditions"
        ]:
            raise FreezeMismatchError("conditions differ from the frozen literal")
        if conditions["m3_mc_dropout_passes"] != 30:
            raise FreezeMismatchError("frozen MC pass count differs from the contract")
        exclusions = json.loads(
            _resolve(manifest["exclusion_manifest"]["path"]).read_bytes()
        )
        roster_cohort, _factory = _COHORT_DATASETS[cohort]
        roster = build_real_retained_rosters(exclusions)[roster_cohort]
        post_qc = json.loads(
            (
                REPOSITORY_ROOT / "docs/research/manifests/cohort_manifest_post_qc.json"
            ).read_bytes()
        )
        verify_roster_digest(post_qc, roster_cohort, roster)
        sha, clean = git_state(REPOSITORY_ROOT)
        if (
            sha != manifest["code_commit_sha"]
            or not clean
            or manifest["git_tree_clean"] is not True
        ):
            raise FreezeMismatchError("code commit or clean tree mismatch")
        stats = load_normalization_stats(
            _resolve(manifest["normalization_statistics"]["path"])
        )
        return roster, grid, stats
    except FreezeMismatchError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise FreezeMismatchError("frozen input verification failed") from error


def run_external_evaluation(cohort: str, run_id: str, *, device: str = "auto") -> Path:
    """Check authorization and frozen inputs, then use the existing condition scorer.

    This driver freezes raw outputs. Temperature and conformal quantiles are copied
    from the signed manifest for downstream analysis; no fitting or metrics run here.
    """
    firewall.assert_external_eval_authorized(cohort)
    manifest_payload = firewall.freeze_manifest_path().read_bytes()
    manifest = json.loads(manifest_payload)
    manifest_hash = hashlib.sha256(manifest_payload).hexdigest()
    roster, grid, stats = _verify_inputs(manifest, cohort)
    roster_cohort, factory = _COHORT_DATASETS[cohort]
    output = paths.experiments_dir() / "external_frozen" / cohort / _component(run_id)
    if output.exists():
        raise FileExistsError("external frozen run already exists")
    # Validate all run records before reserving the write-once run directory.
    runs = []
    for entry in manifest["model_checkpoints"]:
        _directory, record = _load_record(entry["run_id"])
        if record["checkpoint_hash"] != entry["sha256"]:
            raise FreezeMismatchError("run record checkpoint mismatch")
        runs.append((entry, record))
    resolved_device = _resolve_device(device)
    output.mkdir(parents=True, exist_ok=False)
    counts: dict[str, int] = {}
    for entry, record in runs:
        model = build_model(model_config_from_record(record))
        load_model_weights(_resolve(entry["path"]), model)
        for index, condition in enumerate(grid.modality_conditions):
            zeroed = modality_channel_indices(condition.zeroed)
            dataset = factory(
                roster,
                stats=stats,
                seed=int(record["seed"]),
                augment=False,
                zero_channels=zeroed,
                cohort=roster_cohort,
            )
            rows = _score_condition_split(
                model,
                dataset,
                condition_id=condition.id,
                zeroed_indices=zeroed,
                device=resolved_device,
                passes=30,
                seed=10 * index,
                cohort=cohort,
            )
            if len(rows) != len(roster):
                raise FreezeMismatchError("scored cohort count differs from roster")
            counts[condition.id] = len(rows)
            write_prediction_artifact(
                rows,
                output / entry["role"] / f"{condition.id}.parquet",
                run_id=run_id,
                git_sha=manifest["code_commit_sha"],
                checkpoint_hash=entry["sha256"],
                freeze_manifest_sha256=manifest_hash,
            )
    post_sha, _clean = git_state(REPOSITORY_ROOT)
    if post_sha != manifest["code_commit_sha"]:
        raise FreezeMismatchError("post-run code commit mismatch")
    report = {
        "run_id": run_id,
        "cohort": cohort,
        "counts": counts,
        "git_sha": post_sha,
        "post_run_git_sha": post_sha,
        "git_sha_unchanged": True,
        "freeze_manifest_sha256": manifest_hash,
        "model_checkpoints": manifest["model_checkpoints"],
        "calibration_parameters": manifest["calibration_parameters"],
        "conformal": manifest["conformal"],
    }
    payload = (
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    _write_exclusive(output / "report.json", payload)
    _write_exclusive(
        output / "report.json.sha256",
        f"{hashlib.sha256(payload).hexdigest()}  report.json\n".encode(),
    )
    for condition, count in counts.items():
        print(f"rows[{cohort}:{condition}]={count}")
    return output


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, choices=tuple(_COHORT_DATASETS))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args(argv)
    run_external_evaluation(args.cohort, args.run_id, device=args.device)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

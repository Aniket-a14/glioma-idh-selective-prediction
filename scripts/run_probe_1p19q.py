#!/usr/bin/env python3
"""RQ4 exploratory 1p/19q frozen-encoder probe on a completed IDH run (T10.7, D-007).

Extracts the frozen model's pooled features for the UTSW train and internal-test
patients that carry a 1p/19q label, fits the pre-specified probe on the train
patients, and writes a descriptive report with a SHA-256 sidecar into the run
directory. Internal data only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for import_root in (REPOSITORY_ROOT, SOURCE_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

_LABELLED = {"codeleted": 1, "non_codeleted": 0}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True, help="completed IDH run ULID")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cpu")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--allow-sha-mismatch", action="store_true")
    return parser


def _labelled_ids(split: str) -> tuple[list[str], dict[str, int]]:
    from glioma_selective.data.dataset import load_split_patient_ids
    from glioma_selective.leakage.id_normalization import Cohort, normalize_identifier
    from glioma_selective.splits.stratified import read_utsw_split_labels

    labels = read_utsw_split_labels()
    kept: list[str] = []
    target: dict[str, int] = {}
    for patient_id in load_split_patient_ids(split):
        canonical = normalize_identifier(patient_id, Cohort.UTSW)
        label = labels.get(canonical)
        if label is None or label.one_p_nineteen_q not in _LABELLED:
            continue
        kept.append(patient_id)
        target[canonical] = _LABELLED[label.one_p_nineteen_q]
    return kept, target


def run_probe(
    run_id: str,
    *,
    device: str,
    batch_size: int,
    iterations: int,
    allow_sha_mismatch: bool,
) -> Path:
    from scripts.freeze_predictions import (
        _check_run,
        _load_record,
        _resolve_device,
        _write_exclusive,
    )

    from glioma_selective.data.dataset import IDHDataset
    from glioma_selective.evaluation.freeze import model_config_from_record
    from glioma_selective.evaluation.probe_1p19q import analyze_probe, extract_features
    from glioma_selective.leakage.id_normalization import Cohort, normalize_identifier
    from glioma_selective.models.segresnet import build_model
    from glioma_selective.training.checkpoint import load_model_weights
    from glioma_selective.training.run import _build_datasets

    run_dir, record = _load_record(run_id)
    out_dir = run_dir / "probe_1p19q"
    out_dir.mkdir(exist_ok=False)
    checkpoint_path = run_dir / "checkpoints" / "best.pt"
    current_sha, record_sha, checkpoint_hash = _check_run(
        record, checkpoint_path, allow_sha_mismatch=allow_sha_mismatch
    )
    resolved = _resolve_device(device)
    model = build_model(model_config_from_record(record))
    load_model_weights(checkpoint_path, model)
    model.to(resolved)
    seed = int(record["seed"])
    _train, calibration_dataset, _stats_path = _build_datasets(seed)

    extracted: dict[str, dict[str, Any]] = {}
    targets: dict[str, dict[str, int]] = {}
    for split in ("train", "internal_test"):
        ids, target = _labelled_ids(split)
        dataset = IDHDataset(
            ids,
            stats=calibration_dataset.stats,
            seed=seed,
            augment=False,
            zero_channels=(),
            storage=calibration_dataset.storage,
        )
        extracted[split] = extract_features(
            model, dataset, device=resolved, batch_size=batch_size
        )
        targets[split] = target
        print(f"{split}: {len(ids)} patients with a 1p/19q label", flush=True)

    def labels_for(split: str) -> np.ndarray:
        return np.asarray(
            [
                targets[split][normalize_identifier(pid, Cohort.UTSW)]
                for pid in extracted[split]["patient_ids"]
            ],
            dtype=np.int64,
        )

    train_y, test_y = labels_for("train"), labels_for("internal_test")
    np.savez_compressed(
        out_dir / "features.npz",
        train_features=extracted["train"]["features"],
        train_label=train_y,
        test_features=extracted["internal_test"]["features"],
        test_label=test_y,
        test_idh_logit=extracted["internal_test"]["idh_logit"],
        test_idh_label=extracted["internal_test"]["idh_label"],
    )
    report = dict(
        analyze_probe(
            extracted["train"]["features"],
            train_y,
            extracted["internal_test"]["features"],
            test_y,
            extracted["internal_test"]["idh_logit"],
            extracted["internal_test"]["idh_label"],
            iterations=iterations,
        )
    )
    report["provenance"] = {
        "run_id": run_id,
        "checkpoint_hash": checkpoint_hash,
        "git_sha": current_sha,
        "record_git_sha": record_sha,
        "cohort": "UTSW internal only; no external data",
    }
    payload = (
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    result_path = out_dir / "probe_1p19q.json"
    _write_exclusive(result_path, payload)
    digest = hashlib.sha256(payload).hexdigest()
    _write_exclusive(
        result_path.with_name(result_path.name + ".sha256"),
        f"{digest}  {result_path.name}\n".encode("ascii"),
    )
    return result_path


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.batch_size < 1 or args.iterations < 1000:
        raise SystemExit("batch size must be positive and iterations at least 1000")
    path = run_probe(
        args.run_id,
        device=args.device,
        batch_size=args.batch_size,
        iterations=args.iterations,
        allow_sha_mismatch=args.allow_sha_mismatch,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

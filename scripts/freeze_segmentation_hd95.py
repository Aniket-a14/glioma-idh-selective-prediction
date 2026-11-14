#!/usr/bin/env python3
"""Freeze auxiliary segmentation HD95 on calibration and internal-test UTSW."""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
for import_root in (REPOSITORY_ROOT, REPOSITORY_ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts import freeze_predictions  # noqa: E402

from glioma_selective.evaluation.freeze import (  # noqa: E402
    _SEGMENTATION_CHANNELS,
    model_config_from_record,
)
from glioma_selective.evaluation.hd95 import (  # noqa: E402
    classify_case,
    grid_diagonal_penalty,
    hd95,
    summarize_hd95,
)

SPACING = (2.0, 2.0, 2.0)
PENALTY = grid_diagonal_penalty((96, 96, 96), SPACING)


def _predict_split(
    model: Any, dataset: Any, *, device: Any, batch_size: int
) -> dict[str, Any]:
    """One deterministic forward pass per batch, preserving patient/channel order."""
    import torch

    from glioma_selective.training.determinism import deterministic_mode

    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    model.to(device)
    model.eval()
    outcomes: dict[str, list[dict[str, Any]]] = {
        channel: [] for channel in _SEGMENTATION_CHANNELS
    }
    missing = 0
    with deterministic_mode(), torch.no_grad():
        for offset in range(0, len(dataset), batch_size):
            samples = [
                dataset[i]
                for i in range(offset, min(offset + batch_size, len(dataset)))
            ]
            image = torch.stack([sample["image"] for sample in samples]).to(device)
            if image.ndim != 5 or image.shape[1] != 4:
                raise ValueError("prediction dataset must provide four MRI sequences")
            logits = getattr(model(image), "seg_logits", None)
            if logits is None:
                raise ValueError("model output seg_logits is None; HD95 unavailable")
            if logits.ndim != 5 or logits.shape[:2] != (len(samples), 3):
                raise ValueError("seg_logits must have shape (B, 3, D, H, W)")
            predicted = (torch.sigmoid(logits) > 0.5).cpu().numpy()
            for i, sample in enumerate(samples):
                if not bool(sample["has_seg"]):
                    missing += 1
                    continue
                truth = (sample["seg"] > 0.5).cpu().numpy()
                for c, channel in enumerate(_SEGMENTATION_CHANNELS):
                    pred, target = predicted[i, c], truth[c]
                    outcomes[channel].append(
                        {
                            "patient_id": sample["patient_id"],
                            "case": classify_case(pred, target),
                            "value": hd95(pred, target, SPACING),
                        }
                    )
    return {
        "per_channel": {
            channel: {
                **summarize_hd95(
                    [(row["case"], row["value"]) for row in rows], PENALTY
                ),
                "outcomes": rows,
            }
            for channel, rows in outcomes.items()
        },
        "n_without_segmentation": missing,
    }


def freeze_run(
    run_id: str, *, device: str = "auto", allow_sha_mismatch: bool = False
) -> Path:
    """Reuse prediction-freeze provenance and datasets; exclusively write S5.6."""
    from glioma_selective.data.dataset import IDHDataset, load_split_patient_ids
    from glioma_selective.models.segresnet import build_model
    from glioma_selective.training.checkpoint import load_model_weights
    from glioma_selective.training.run import _build_datasets

    run_dir, record = freeze_predictions._load_record(run_id)
    path = run_dir / "segmentation_hd95.json"
    sidecar = path.with_name(path.name + ".sha256")
    if path.exists() or sidecar.exists():
        raise FileExistsError("segmentation HD95 artifact or sidecar already exists")
    checkpoint = run_dir / "checkpoints" / "best.pt"
    current_sha, record_sha, checkpoint_hash = freeze_predictions._check_run(
        record, checkpoint, allow_sha_mismatch=allow_sha_mismatch
    )
    resolved = freeze_predictions._resolve_device(device)
    config = model_config_from_record(record)
    if not config.aux_segmentation and not config.two_stage:
        raise ValueError("model has no segmentation head; HD95 unavailable")
    model = build_model(config)
    load_model_weights(checkpoint, model)
    _train, calibration, _stats_path = _build_datasets(int(record["seed"]))
    internal = IDHDataset(
        load_split_patient_ids("internal_test"),
        stats=calibration.stats,
        seed=int(record["seed"]),
        augment=False,
        zero_channels=(),
        storage=calibration.storage,
    )
    training = cast(Mapping[str, Any], record["config"].get("training", {}))
    batch_size = int(training.get("batch_size", 1))
    document = {
        "run_id": run_id,
        "git_sha": current_sha,
        "checkpoint_hash": checkpoint_hash,
        "splits": {
            split: _predict_split(
                model, dataset, device=resolved, batch_size=batch_size
            )
            for split, dataset in (
                ("calibration", calibration),
                ("internal_test", internal),
            )
        },
    }
    if current_sha != record_sha:
        document["record_git_sha"] = record_sha
    payload = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    freeze_predictions._write_exclusive(path, payload)
    digest = hashlib.sha256(payload).hexdigest()
    freeze_predictions._write_exclusive(
        sidecar, f"{digest}  {path.name}\n".encode("ascii")
    )
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = freeze_predictions._parser()
    parser.description = __doc__
    args = parser.parse_args(argv)
    print(
        freeze_run(
            args.run_id, device=args.device, allow_sha_mismatch=args.allow_sha_mismatch
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

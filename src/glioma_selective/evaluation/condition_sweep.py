"""Freeze deterministic and head-only predictions for the six frozen conditions."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import nn

from glioma_selective.data.adapters._common import CORE_SEQUENCES
from glioma_selective.training.determinism import deterministic_mode

_SPLITS = (("calibration", "utsw_calibration"), ("internal_test", "utsw_internal_test"))


def modality_channel_indices(names: Sequence[str]) -> tuple[int, ...]:
    """Map frozen YAML modality names to the canonical image channel indices."""
    sequence_by_name = {sequence.name: sequence for sequence in CORE_SEQUENCES}
    unknown = set(names) - set(sequence_by_name)
    if unknown:
        raise ValueError(f"unknown modality names: {sorted(unknown)}")
    indices = tuple(CORE_SEQUENCES.index(sequence_by_name[name]) for name in names)
    # R-C05: the channel mapping is checked against the canonical channel order.
    for name, index in zip(names, indices, strict=True):
        assert CORE_SEQUENCES[index].name == name
    return indices


def _scalar_logit(output: Any) -> torch.Tensor:
    logits = output.logit
    if not isinstance(logits, torch.Tensor):
        raise ValueError("model output logit must be a tensor")
    if logits.ndim == 1:
        return logits
    if logits.ndim == 2 and logits.shape[1] == 1:
        return logits[:, 0]
    raise ValueError("model output logit must have shape (B,) or (B, 1)")


def _score_condition_split(
    model: nn.Module,
    dataset: Any,
    *,
    condition_id: str,
    zeroed_indices: Sequence[int],
    device: torch.device,
    passes: int,
    seed: int,
    cohort: str,
) -> list[dict[str, Any]]:
    from glioma_selective.uncertainty.mc_dropout import mc_dropout_probabilities

    generator = torch.Generator(device=device).manual_seed(seed)
    rows: list[dict[str, Any]] = []
    model.to(device)
    model.eval()
    with deterministic_mode(), torch.no_grad():
        for index in range(len(dataset)):
            sample = dataset[index]
            image = cast(torch.Tensor, sample["image"]).unsqueeze(0).to(device)
            if image.ndim != 5 or image.shape[1] != len(CORE_SEQUENCES):
                raise ValueError("prediction dataset must provide four MRI sequences")
            for channel in zeroed_indices:
                if not bool(torch.all(image[:, channel] == 0.0)):
                    raise ValueError("a zeroed modality channel is not exactly zero")
            present = [i for i in range(4) if i not in zeroed_indices]
            if present and bool(torch.all(image[:, present] == 0.0)):
                raise ValueError("all present modality channels are zero")
            logit = float(_scalar_logit(model(image)).detach().cpu().reshape(-1)[0])
            probability = float(torch.sigmoid(torch.tensor(logit, dtype=torch.float64)))
            draws = (
                mc_dropout_probabilities(
                    cast(Any, model), image, passes=passes, generator=generator
                )[0]
                .detach()
                .cpu()
                .tolist()
            )
            rows.append(
                {
                    "patient_id": cast(str, sample["patient_id"]),
                    "cohort": cohort,
                    "modality_condition": condition_id,
                    "p_hat": np.float32(probability),
                    "logit": np.float32(logit),
                    "label": int(cast(torch.Tensor, sample["label"]).item()),
                    "mc_dropout_samples": [np.float32(value) for value in draws],
                }
            )
    return rows


def _check_full_condition_matches_reference(
    condition_rows: Sequence[Mapping[str, Any]], reference: Any, cohort: str
) -> float:
    """Require the same patients and <=1e-4 p_hat difference for one split."""
    from glioma_selective.tracking.predictions import hash_patient_id

    expected = reference.loc[
        (reference["cohort"] == cohort) & (reference["modality_condition"] == "full")
    ].set_index("patient_id")
    actual = {
        hash_patient_id(str(row["patient_id"])): float(row["p_hat"])
        for row in condition_rows
    }
    if set(expected.index) != set(actual):
        raise ValueError(f"full {cohort} patient set differs from predictions.parquet")
    differences = [
        abs(actual[patient] - float(expected.loc[patient, "p_hat"]))
        for patient in actual
    ]
    maximum = max(differences, default=0.0)
    if maximum > 1e-4:
        raise ValueError(
            "full condition p_hat differs from predictions.parquet by more than 1e-4"
        )
    return maximum


def freeze_conditions(
    run_id: str,
    device: str = "cpu",
    passes: int = 30,
    seed: int = 0,
    allow_sha_mismatch: bool = False,
) -> Path:
    """Freeze six conditions over UTSW calibration and internal-test splits."""
    from omegaconf import OmegaConf
    from scripts.freeze_predictions import REPOSITORY_ROOT

    from glioma_selective.data.dataset import IDHDataset, load_split_patient_ids
    from glioma_selective.evaluation.conditions import load_condition_grid
    from glioma_selective.evaluation.freeze_mc_dropout import (
        _check_run,
        _load_record,
        _resolve_device,
        _write_exclusive,
    )
    from glioma_selective.models.segresnet import ModelConfig, build_model
    from glioma_selective.tracking.predictions import (
        read_prediction_artifact,
        write_prediction_artifact,
    )
    from glioma_selective.training.checkpoint import load_model_weights
    from glioma_selective.training.run import _build_datasets

    if passes < 1:
        raise ValueError("passes must be positive")
    run_dir, record = _load_record(run_id)
    conditions_dir = run_dir / "conditions"
    conditions_dir.mkdir(parents=True, exist_ok=False)
    checkpoint_path = run_dir / "checkpoints" / "best.pt"
    current_sha, record_sha, checkpoint_hash = _check_run(
        record, checkpoint_path, allow_sha_mismatch=allow_sha_mismatch
    )
    resolved_device = _resolve_device(device)
    model_config = OmegaConf.to_container(
        OmegaConf.load(REPOSITORY_ROOT / "configs" / "model" / "base.yaml"),
        resolve=True,
    )
    if not isinstance(model_config, Mapping):
        raise ValueError("base model configuration must be a mapping")
    model = build_model(ModelConfig.from_mapping(cast(Mapping[str, Any], model_config)))
    load_model_weights(checkpoint_path, model)
    model.to(resolved_device)

    _train, calibration_dataset, _stats_path = _build_datasets(int(record["seed"]))
    internal_ids = load_split_patient_ids("internal_test")
    grid = load_condition_grid()
    reference, reference_meta = read_prediction_artifact(
        run_dir / "predictions.parquet"
    )
    if (
        reference_meta.get("run_id") != run_id
        or reference_meta.get("checkpoint_hash") != checkpoint_hash
    ):
        raise ValueError("predictions.parquet provenance does not match the run")
    counts: Counter[str] = Counter()
    full_max_difference = 0.0
    condition_meta: dict[str, Any] = {}
    for condition_index, condition in enumerate(grid.modality_conditions):
        zeroed_indices = modality_channel_indices(condition.zeroed)
        condition_rows: list[dict[str, Any]] = []
        for split_index, (split_name, cohort) in enumerate(_SPLITS):
            base = (
                calibration_dataset
                if split_name == "calibration"
                else IDHDataset(
                    internal_ids,
                    stats=calibration_dataset.stats,
                    seed=int(record["seed"]),
                    augment=False,
                    zero_channels=(),
                    storage=calibration_dataset.storage,
                )
            )
            dataset = IDHDataset(
                base.patient_ids,
                stats=calibration_dataset.stats,
                seed=int(record["seed"]),
                augment=False,
                zero_channels=zeroed_indices,
                storage=calibration_dataset.storage,
            )
            split_rows = _score_condition_split(
                model,
                dataset,
                condition_id=condition.id,
                zeroed_indices=zeroed_indices,
                device=resolved_device,
                passes=passes,
                seed=seed + 10 * condition_index + split_index,
                cohort=cohort,
            )
            counts[f"{condition.id}:{cohort}"] = len(split_rows)
            if condition.id == "full":
                full_max_difference = max(
                    full_max_difference,
                    _check_full_condition_matches_reference(
                        split_rows, reference, cohort
                    ),
                )
            condition_rows.extend(split_rows)
        write_prediction_artifact(
            condition_rows,
            conditions_dir / f"{condition.id}.parquet",
            run_id=run_id,
            git_sha=current_sha,
            checkpoint_hash=checkpoint_hash,
            record_git_sha=record_sha if record_sha != current_sha else None,
        )
        condition_meta[condition.id] = {
            "zeroed_modalities": list(condition.zeroed),
            "zeroed_channel_indices": list(zeroed_indices),
        }

    document = {
        "run_id": run_id,
        "checkpoint_hash": checkpoint_hash,
        "git_sha": current_sha,
        "record_git_sha": record_sha if record_sha != current_sha else None,
        "passes": passes,
        "seed": seed,
        "device": str(resolved_device),
        "conditions": condition_meta,
        "full_p_hat_max_abs_difference": full_max_difference,
    }
    payload = (
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    _write_exclusive(conditions_dir / "conditions_meta.json", payload)
    _write_exclusive(
        conditions_dir / "conditions_meta.json.sha256",
        f"{hashlib.sha256(payload).hexdigest()}  conditions_meta.json\n".encode(
            "ascii"
        ),
    )
    print(f"device={resolved_device}")
    for key, count in counts.items():
        print(f"rows[{key}]={count}")
    return conditions_dir

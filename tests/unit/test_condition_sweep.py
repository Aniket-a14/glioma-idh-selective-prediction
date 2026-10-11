"""Synthetic checks for the frozen six-condition sweep."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import torch

from glioma_selective.data.adapters._common import CORE_SEQUENCES
from glioma_selective.evaluation.condition_sweep import (
    _check_full_condition_matches_reference,
    _score_condition_split,
    freeze_conditions,
    modality_channel_indices,
)
from glioma_selective.models.segresnet import IDHNet, ModelConfig, build_model
from glioma_selective.tracking.predictions import (
    hash_patient_id,
    read_prediction_artifact,
    write_prediction_artifact,
)


def test_names_map_to_canonical_channel_positions() -> None:
    names = ("T1", "T1CE", "T2", "FLAIR")
    assert modality_channel_indices(names) == tuple(
        CORE_SEQUENCES.index(next(seq for seq in CORE_SEQUENCES if seq.name == name))
        for name in names
    )
    assert modality_channel_indices(("T1", "T2")) == (0, 2)
    with pytest.raises(ValueError, match="unknown modality"):
        modality_channel_indices(("T1ce",))


def _model() -> IDHNet:
    torch.manual_seed(17)
    return build_model(ModelConfig(init_filters=8, head_hidden=8))


def test_condition_score_passes_zeroed_tensor_to_model_and_repeats() -> None:
    model = _model().eval()
    seen: list[torch.Tensor] = []
    hook = model.register_forward_pre_hook(
        lambda _module, inputs: seen.append(inputs[0].detach().clone())
    )

    class Dataset:
        def __len__(self) -> int:
            return 1

        def __getitem__(self, index: int) -> dict[str, Any]:
            del index
            image = torch.stack(
                [torch.full((16, 16, 16), float(i + 1)) for i in range(4)]
            )
            image[1].zero_()
            return {
                "image": image,
                "label": torch.tensor(1.0),
                "patient_id": "synthetic-id",
            }

    rows_one = _score_condition_split(
        model,
        Dataset(),
        condition_id="drop_t1ce",
        zeroed_indices=(1,),
        device=torch.device("cpu"),
        passes=4,
        seed=73,
        cohort="utsw_internal_test",
    )
    seen.clear()
    rows_two = _score_condition_split(
        model,
        Dataset(),
        condition_id="drop_t1ce",
        zeroed_indices=(1,),
        device=torch.device("cpu"),
        passes=4,
        seed=73,
        cohort="utsw_internal_test",
    )
    hook.remove()
    assert torch.equal(seen[0][:, 1], torch.zeros_like(seen[0][:, 1]))
    assert bool((seen[0][:, [0, 2, 3]] != 0).any())
    assert rows_one == rows_two
    assert len(rows_one[0]["mc_dropout_samples"]) == 4


def test_freeze_writes_all_six_artifacts_and_refuses_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from glioma_selective.data import dataset as dataset_module
    from glioma_selective.evaluation import freeze_mc_dropout
    from glioma_selective.training import checkpoint, run

    run_dir = tmp_path / "run"
    (run_dir / "checkpoints").mkdir(parents=True)
    (run_dir / "checkpoints" / "best.pt").write_bytes(b"weights")
    fake_record = {
        "run_id": "synthetic",
        "seed": 4,
        "checkpoint_hash": hashlib.sha256(b"weights").hexdigest(),
    }
    monkeypatch.setattr(
        freeze_mc_dropout, "_load_record", lambda _run_id: (run_dir, fake_record)
    )
    monkeypatch.setattr(
        freeze_mc_dropout,
        "_check_run",
        lambda *_a, **_kw: ("sha", "sha", fake_record["checkpoint_hash"]),
    )
    monkeypatch.setattr(checkpoint, "load_model_weights", lambda *_args: None)

    class FakeDataset:
        def __init__(
            self,
            ids: list[str],
            *,
            stats: object,
            seed: int,
            augment: bool,
            zero_channels: tuple[int, ...] = (),
            storage: object = None,
        ) -> None:
            self.patient_ids, self.stats, self.seed = tuple(ids), stats, seed
            self.augment, self.zero_channels, self.storage = (
                augment,
                zero_channels,
                storage,
            )

        def __len__(self) -> int:
            return len(self.patient_ids)

        def __getitem__(self, index: int) -> dict[str, Any]:
            image = torch.stack(
                [torch.full((16, 16, 16), float(i + 1)) for i in range(4)]
            )
            for channel in self.zero_channels:
                image[channel].zero_()
            return {
                "image": image,
                "label": torch.tensor(float(index % 2)),
                "patient_id": self.patient_ids[index],
            }

    base = FakeDataset(["cal-a", "cal-b"], stats=object(), seed=4, augment=False)
    monkeypatch.setattr(run, "_build_datasets", lambda _seed: (None, base, None))
    monkeypatch.setattr(dataset_module, "IDHDataset", FakeDataset)
    monkeypatch.setattr(
        dataset_module, "load_split_patient_ids", lambda _split: ["test-a", "test-b"]
    )

    def build(_config: object) -> IDHNet:
        return _model()

    monkeypatch.setattr("glioma_selective.models.segresnet.build_model", build)
    monkeypatch.setattr(
        "glioma_selective.models.segresnet.ModelConfig.from_mapping",
        lambda _values: ModelConfig(init_filters=8, head_hidden=8),
    )
    # Construct the reference full-input predictions with the same deterministic model.
    reference_model = _model().eval()
    ref_rows: list[dict[str, Any]] = []
    for cohort, ids in (
        ("utsw_calibration", base.patient_ids),
        ("utsw_internal_test", ("test-a", "test-b")),
    ):
        ds = FakeDataset(list(ids), stats=base.stats, seed=4, augment=False)
        with torch.no_grad():
            for i in range(len(ds)):
                sample = ds[i]
                logit = float(reference_model(sample["image"].unsqueeze(0)).logit[0])
                p = float(torch.sigmoid(torch.tensor(logit, dtype=torch.float64)))
                ref_rows.append(
                    {
                        "patient_id": sample["patient_id"],
                        "cohort": cohort,
                        "modality_condition": "full",
                        "logit": logit,
                        "p_hat": p,
                        "label": int(i % 2),
                    }
                )
    write_prediction_artifact(
        ref_rows,
        run_dir / "predictions.parquet",
        run_id="synthetic",
        git_sha="sha",
        checkpoint_hash=fake_record["checkpoint_hash"],
    )

    directory = freeze_conditions("synthetic", passes=3, seed=9)
    assert len(list(directory.glob("*.parquet"))) == 6
    for condition in (
        "full",
        "drop_t1",
        "drop_t1ce",
        "drop_t2",
        "drop_flair",
        "t1ce_flair_only",
    ):
        frame, metadata = read_prediction_artifact(directory / f"{condition}.parquet")
        assert metadata["run_id"] == "synthetic"
        assert set(frame["modality_condition"]) == {condition}
        assert all(len(samples) == 3 for samples in frame["mc_dropout_samples"])
    meta = json.loads((directory / "conditions_meta.json").read_text())
    assert meta["conditions"]["drop_t1ce"]["zeroed_channel_indices"] == [1]
    with pytest.raises(FileExistsError):
        freeze_conditions("synthetic", passes=3, seed=9)


def test_full_condition_probability_mismatch_is_rejected() -> None:
    import pandas as pd

    reference = pd.DataFrame(
        {
            "patient_id": [hash_patient_id("patient-id")],
            "cohort": ["utsw_internal_test"],
            "modality_condition": ["full"],
            "p_hat": [0.5],
        }
    )
    rows = [{"patient_id": "patient-id", "p_hat": 0.5002}]
    with pytest.raises(ValueError, match="more than 1e-4"):
        _check_full_condition_matches_reference(rows, reference, "utsw_internal_test")


def test_package_has_no_imputation_or_inpainting_entry_point() -> None:
    import importlib
    import inspect
    import pkgutil

    import glioma_selective

    offenders: list[str] = []
    for item in pkgutil.walk_packages(glioma_selective.__path__, "glioma_selective."):
        module = importlib.import_module(item.name)
        offenders.extend(
            f"{item.name}.{name}"
            for name, member in inspect.getmembers(module, inspect.isfunction)
            if "impute" in name.lower() or "inpaint" in name.lower()
        )
    assert offenders == []

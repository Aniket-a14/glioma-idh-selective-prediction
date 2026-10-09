from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from glioma_selective.evaluation import freeze_mc_dropout as freezer
from glioma_selective.models.segresnet import ModelConfig, build_model
from glioma_selective.tracking.predictions import read_prediction_artifact

RUN_ID = "01K6JQY7YGXSP6ZBZD3YF8QXPT"
CONFIG = ModelConfig(init_filters=8, head_hidden=8)


class TinyDataset(list[dict[str, Any]]):
    stats = object()
    storage = object()


def _dataset(prefix: str) -> TinyDataset:
    return TinyDataset(
        [
            {
                "patient_id": f"{prefix}-{i}",
                "image": torch.randn(
                    4,
                    16,
                    16,
                    16,
                    generator=torch.Generator().manual_seed(
                        i + (0 if prefix == "cal" else 20)
                    ),
                ),
                "label": torch.tensor(i % 2),
            }
            for i in range(4)
        ]
    )


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, seed: int = 0) -> Path:
    run_dir = tmp_path / RUN_ID
    (run_dir / "checkpoints").mkdir(parents=True)
    (run_dir / "checkpoints" / "best.pt").write_bytes(b"checkpoint")
    record = {
        "run_id": RUN_ID,
        "status": "completed",
        "git_dirty": False,
        "git_sha": "a" * 40,
        "checkpoint_hash": "c" * 64,
        "seed": seed,
    }
    (run_dir / "record.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(freezer, "_load_record", lambda _run_id: (run_dir, record))
    monkeypatch.setattr(
        freezer, "_check_run", lambda *_a, **_k: ("b" * 40, "a" * 40, "c" * 64)
    )
    monkeypatch.setattr(
        freezer,
        "_build_datasets",
        lambda _seed: (None, _dataset("cal"), None),
        raising=False,
    )
    import glioma_selective.training.run as training_run

    monkeypatch.setattr(
        training_run, "_build_datasets", lambda _seed: (None, _dataset("cal"), None)
    )
    import glioma_selective.data.dataset as dataset_module

    monkeypatch.setattr(
        dataset_module,
        "load_split_patient_ids",
        lambda _split: [f"test-{i}" for i in range(4)],
    )
    monkeypatch.setattr(
        dataset_module, "IDHDataset", lambda ids, **kwargs: _dataset("test")
    )
    import omegaconf

    monkeypatch.setattr(
        omegaconf.OmegaConf, "load", lambda _path: {"init_filters": 8, "head_hidden": 8}
    )
    monkeypatch.setattr(
        omegaconf.OmegaConf, "to_container", lambda config, **kwargs: config
    )
    import glioma_selective.models.segresnet as segresnet

    monkeypatch.setattr(segresnet, "build_model", lambda _config: _seeded_model())
    import glioma_selective.training.checkpoint as checkpoint

    monkeypatch.setattr(checkpoint, "load_model_weights", lambda _path, _model: None)
    return run_dir


def _seeded_model() -> torch.nn.Module:
    torch.manual_seed(10)
    return build_model(CONFIG)


def test_freeze_writes_t_samples_and_verified_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _setup(tmp_path, monkeypatch)
    path = freezer.freeze_mc_dropout(RUN_ID, passes=5)
    frame, metadata = read_prediction_artifact(path)
    assert len(frame) == 8
    assert all(len(row) == 5 for row in frame["mc_dropout_samples"])
    assert metadata["run_id"] == RUN_ID
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert (
        path.with_name(path.name + ".sha256").read_text() == f"{digest}  {path.name}\n"
    )
    meta = json.loads((run_dir / "mc_dropout_meta.json").read_text())
    assert meta == {
        "checkpoint_hash": "c" * 64,
        "device": "cpu",
        "passes": 5,
        "run_id": RUN_ID,
        "seed": 0,
    }


def test_freeze_is_seeded_differs_for_another_seed_and_refuses_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_dir = _setup(tmp_path / "first", monkeypatch)
    freezer.freeze_mc_dropout(RUN_ID, passes=8, seed=13)
    first, _ = read_prediction_artifact(first_dir / "mc_dropout.parquet")
    second_dir = _setup(tmp_path / "second", monkeypatch)
    freezer.freeze_mc_dropout(RUN_ID, passes=8, seed=13)
    again, _ = read_prediction_artifact(second_dir / "mc_dropout.parquet")
    assert np.array_equal(
        np.asarray(first["mc_dropout_samples"].tolist()),
        np.asarray(again["mc_dropout_samples"].tolist()),
    )
    third_dir = _setup(tmp_path / "third", monkeypatch)
    freezer.freeze_mc_dropout(RUN_ID, passes=8, seed=14)
    other, _ = read_prediction_artifact(third_dir / "mc_dropout.parquet")
    assert not np.array_equal(
        np.asarray(first["mc_dropout_samples"].tolist()),
        np.asarray(other["mc_dropout_samples"].tolist()),
    )
    with pytest.raises(FileExistsError, match="already exists"):
        freezer.freeze_mc_dropout(RUN_ID, passes=8, seed=13)


def test_frozen_point_prediction_matches_plain_eval_forward(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(tmp_path, monkeypatch)
    model = _seeded_model().eval()
    sample = _dataset("cal")[0]
    with torch.no_grad():
        logit = model(sample["image"].unsqueeze(0)).logit.reshape(-1)[0].item()
    path = freezer.freeze_mc_dropout(RUN_ID, passes=3)
    frame, _ = read_prediction_artifact(path)
    row = frame.loc[
        frame["patient_id"] == hashlib.sha256(b"cal-0").hexdigest()[:16]
    ].iloc[0]
    assert float(row["logit"]) == pytest.approx(logit, abs=1e-6)
    assert float(row["p_hat"]) == pytest.approx(1 / (1 + np.exp(-logit)), abs=1e-6)

"""S5.6 freezing on synthetic tensors and temporary run artifacts only."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import torch
from scripts import freeze_predictions
from scripts import freeze_segmentation_hd95 as cli
from torch import nn

from glioma_selective.data import dataset as datasets
from glioma_selective.models import segresnet
from glioma_selective.models.segresnet import ModelConfig, ModelOutput
from glioma_selective.training import checkpoint, run
from glioma_selective.utils import paths

RUN_ID = "01K6JQY7YGXSP6ZBZD3YF8QXPT"


class _Dataset(list[dict[str, Any]]):
    stats = object()
    storage = object()


def _samples() -> _Dataset:
    result = _Dataset()
    for i in range(5):
        truth = torch.zeros(3, 1, 1, 3)
        if i in (0, 1):
            truth[:, 0, 0, 0] = 1
        if i == 3:
            truth.fill_(0.5)  # The strict truth threshold excludes these voxels.
        result.append(
            {
                "patient_id": f"p{i}",
                "image": torch.full((4, 1, 1, 3), float(i)),
                "seg": truth,
                "has_seg": torch.tensor(i != 4),
            }
        )
    return result


class _Model(nn.Module):
    def __init__(self, *, no_head: bool = False) -> None:
        super().__init__()
        self.no_head = no_head
        self.batches: list[int] = []

    def forward(self, image: torch.Tensor) -> ModelOutput:
        assert not self.training and not torch.is_grad_enabled()
        assert torch.are_deterministic_algorithms_enabled()
        self.batches.append(len(image))
        logits = torch.zeros(len(image), 3, 1, 1, 3, device=image.device)
        for i, value in enumerate(image[:, 0, 0, 0, 0].tolist()):
            if value in (0, 2):
                logits[i, :, 0, 0, 1] = 1
        return ModelOutput(image[:, 0, 0, 0, 0], None if self.no_head else logits)


@pytest.fixture
def fake_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    directory = tmp_path / "experiments" / RUN_ID
    best = directory / "checkpoints" / "best.pt"
    best.parent.mkdir(parents=True)
    best.write_bytes(b"synthetic checkpoint")
    record = {
        "run_id": RUN_ID,
        "git_sha": "a" * 40,
        "git_dirty": False,
        "status": "completed",
        "checkpoint_hash": hashlib.sha256(best.read_bytes()).hexdigest(),
        "seed": 17,
        "config": {"model": {}, "training": {"batch_size": 2}},
    }
    monkeypatch.setattr(paths, "experiments_dir", lambda: directory.parent)
    monkeypatch.setattr(freeze_predictions, "_current_git_sha", lambda: "a" * 40)
    model = _Model()
    built: list[ModelConfig] = []
    loaded = []
    seeds = []
    split_calls = []
    dataset_calls = []
    calibration = _samples()

    def build(config: ModelConfig) -> _Model:
        built.append(config)
        return model

    def build_datasets(seed: int) -> tuple[None, _Dataset, None]:
        seeds.append(seed)
        return None, calibration, None

    def split_ids(split: str) -> list[str]:
        assert split == "internal_test"
        split_calls.append(split)
        return [f"p{i}" for i in range(5)]

    def internal(ids: list[str], **kwargs: Any) -> _Dataset:
        dataset_calls.append((ids, kwargs))
        return _samples()

    monkeypatch.setattr(segresnet, "build_model", build)
    monkeypatch.setattr(
        checkpoint, "load_model_weights", lambda p, m: loaded.append((p, m))
    )
    monkeypatch.setattr(run, "_build_datasets", build_datasets)
    monkeypatch.setattr(datasets, "load_split_patient_ids", split_ids)
    monkeypatch.setattr(datasets, "IDHDataset", internal)
    record_path = directory / "record.json"
    record_path.write_text(json.dumps(record))
    return {
        "directory": directory,
        "best": best,
        "record": record,
        "record_path": record_path,
        "model": model,
        "built": built,
        "loaded": loaded,
        "seeds": seeds,
        "split_calls": split_calls,
        "dataset_calls": dataset_calls,
        "calibration": calibration,
    }


@pytest.mark.parametrize(
    "model_config",
    [
        {},
        {"tumour_aware_pooling": False},
        {"two_stage": True},
        {"two_stage": True, "aux_segmentation": False, "tumour_aware_pooling": False},
    ],
)
def test_freeze_rebuilds_record_and_writes_both_splits(
    fake_run: dict[str, Any], model_config: dict[str, Any]
) -> None:
    f = fake_run
    f["record"]["config"]["model"] = model_config
    f["record_path"].write_text(json.dumps(f["record"]))
    previous = torch.are_deterministic_algorithms_enabled()
    path = cli.freeze_run(RUN_ID, device="cpu")
    assert torch.are_deterministic_algorithms_enabled() == previous
    document = json.loads(path.read_bytes())
    assert document["run_id"] == RUN_ID
    assert document["git_sha"] == f["record"]["git_sha"]
    assert document["checkpoint_hash"] == f["record"]["checkpoint_hash"]
    assert f["built"] == [ModelConfig.from_mapping(model_config)]
    assert f["loaded"] == [(f["best"], f["model"])]
    assert f["seeds"] == [17] and f["split_calls"] == ["internal_test"]
    _, kwargs = f["dataset_calls"][0]
    assert kwargs == {
        "stats": f["calibration"].stats,
        "seed": 17,
        "augment": False,
        "zero_channels": (),
        "storage": f["calibration"].storage,
    }
    assert f["model"].batches == [2, 2, 1, 2, 2, 1]
    assert set(document["splits"]) == {"calibration", "internal_test"}
    for split in document["splits"].values():
        assert split["n_without_segmentation"] == 1
        assert set(split["per_channel"]) == {"enhancing", "necrotic_core", "oedema"}
        for channel in split["per_channel"].values():
            assert channel["outcomes"] == [
                {"patient_id": "p0", "case": "evaluable", "value": 2.0},
                {"patient_id": "p1", "case": "missed", "value": None},
                {"patient_id": "p2", "case": "false", "value": None},
                {"patient_id": "p3", "case": "both_empty", "value": None},
            ]
            assert channel["primary"]["mean"] == 2
            assert channel["n_patients"] == 4
            assert [channel[k] for k in ("missed", "false", "both_empty")] == [1, 1, 1]
            assert channel["brats_penalty"]["mean"] == pytest.approx(
                (2 + 2 * cli.PENALTY) / 4
            )
    assert path.with_name(path.name + ".sha256").read_text() == (
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
    )
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        cli.freeze_run(RUN_ID, device="cpu")
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "filename", ["segmentation_hd95.json", "segmentation_hd95.json.sha256"]
)
def test_either_existing_file_refuses_before_model_loading(
    fake_run: dict[str, Any], filename: str
) -> None:
    path = fake_run["directory"] / filename
    path.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        cli.freeze_run(RUN_ID, device="cpu")
    assert path.read_bytes() == b"keep" and fake_run["built"] == []


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("status", "running", "status=completed"),
        ("git_dirty", True, "git_dirty=false"),
        ("checkpoint_hash", "f" * 64, "checkpoint_hash"),
        ("git_sha", "b" * 40, "current git SHA"),
    ],
)
def test_provenance_refused(
    fake_run: dict[str, Any], field: str, value: Any, message: str
) -> None:
    record = {**fake_run["record"], field: value}
    fake_run["record_path"].write_text(json.dumps(record))
    with pytest.raises(ValueError, match=message):
        cli.freeze_run(RUN_ID, device="cpu")
    assert fake_run["built"] == []
    assert not (fake_run["directory"] / "segmentation_hd95.json").exists()


def test_allow_sha_mismatch_records_both(
    fake_run: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(freeze_predictions, "_current_git_sha", lambda: "b" * 40)
    document = json.loads(
        cli.freeze_run(RUN_ID, device="cpu", allow_sha_mismatch=True).read_bytes()
    )
    assert document["git_sha"] == "b" * 40 and document["record_git_sha"] == "a" * 40


def test_missing_head_errors_without_artifact(fake_run: dict[str, Any]) -> None:
    fake_run["model"].no_head = True
    with pytest.raises(ValueError, match="seg_logits is None"):
        cli.freeze_run(RUN_ID, device="cpu")
    assert not (fake_run["directory"] / "segmentation_hd95.json").exists()


def test_no_segmentation_head_in_config_refused_before_datasets(
    fake_run: dict[str, Any],
) -> None:
    fake_run["record"]["config"]["model"] = {
        "aux_segmentation": False,
        "tumour_aware_pooling": False,
    }
    fake_run["record_path"].write_text(json.dumps(fake_run["record"]))
    with pytest.raises(ValueError, match="no segmentation head"):
        cli.freeze_run(RUN_ID, device="cpu")
    assert fake_run["built"] == [] and fake_run["seeds"] == []


def test_all_missing_segmentations_excluded() -> None:
    samples = _samples()
    for sample in samples:
        sample["has_seg"] = torch.tensor(False)
    result = cli._predict_split(_Model(), samples, device="cpu", batch_size=2)
    assert result["n_without_segmentation"] == 5
    for channel in result["per_channel"].values():
        assert channel["outcomes"] == [] and channel["n_patients"] == 0
        assert channel["primary"]["mean"] is None


def test_exclusive_helper_will_not_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "freeze.json"
    freeze_predictions._write_exclusive(path, b"first")
    with pytest.raises(FileExistsError):
        freeze_predictions._write_exclusive(path, b"second")
    assert path.read_bytes() == b"first"


def test_cli_help_and_arguments(
    fake_run: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["--run-id", RUN_ID, "--device", "cpu"]) == 0
    assert Path(capsys.readouterr().out.strip()).is_file()
    for flag in ("--split", "--cohort"):
        with pytest.raises(SystemExit):
            cli.main(["--run-id", RUN_ID, flag, "external"])
    result = subprocess.run(
        [sys.executable, str(Path(cli.__file__)), "--help"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": ""},
    )
    assert all(
        flag in result.stdout
        for flag in ("--run-id", "--device", "--allow-sha-mismatch")
    )

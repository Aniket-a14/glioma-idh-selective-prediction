"""Run configuration and the authorization gate of the training entry point."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import torch
from omegaconf import OmegaConf

from glioma_selective.training.loop import TrainConfig
from glioma_selective.training.run import RunSpec, train_run, training_config_for

TRAINING_YAML = (
    Path(__file__).resolve().parent.parent.parent / "configs/training/base.yaml"
)


def test_training_yaml_equals_the_dataclass_defaults() -> None:
    raw = OmegaConf.to_container(OmegaConf.load(TRAINING_YAML), resolve=True)
    assert isinstance(raw, dict)
    assert TrainConfig(**raw) == TrainConfig()  # type: ignore[arg-type]


def test_r1_config_has_no_modality_dropout_and_r2_has() -> None:
    assert training_config_for(RunSpec(label="r1")).modality_dropout is False
    r2 = training_config_for(RunSpec(label="r2", modality_dropout=True, seed=3))
    assert r2.modality_dropout is True
    assert r2.seed == 3


def test_only_the_named_fields_change() -> None:
    base = TrainConfig()
    config = training_config_for(RunSpec(label="pilot", max_epochs=2, seed=5))
    assert config == replace(base, max_epochs=2, seed=5)


def test_a_run_without_a_valid_authorization_report_is_refused(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    report.write_text(json.dumps({"authorized": False, "results": []}))
    with pytest.raises(ValueError, match="not authorized"):
        train_run(
            RunSpec(label="r1"), authorization_report=report, device=torch.device("cpu")
        )


def test_a_missing_report_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="could not read"):
        train_run(
            RunSpec(label="r1"),
            authorization_report=tmp_path / "nope.json",
            device=torch.device("cpu"),
        )


def _capture_updates(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    from glioma_selective.training import run as run_module

    calls: list[dict[str, object]] = []

    def record(run_id: str, **fields: object) -> None:
        calls.append({"run_id": run_id, **fields})

    monkeypatch.setattr(run_module, "update_run_record", record)
    return calls


def test_a_completed_run_stamps_its_end_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from glioma_selective.training import run as run_module

    calls = _capture_updates(monkeypatch)
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "checkpoints" / "best.pt").write_bytes(b"weights")
    state = SimpleNamespace(
        history=[{"calibration_auroc": 0.5}, {"calibration_auroc": 0.9}],
        best_epoch=1,
        best_value=0.4,
    )
    result = SimpleNamespace(state=state, stopped_early=True)
    run_module._record_completion(
        "RUN",
        result,
        tmp_path,
        tmp_path / "train.log",  # type: ignore[arg-type]
    )
    (call,) = calls
    assert call["status"] == "completed"
    end_time = str(call["end_time_utc"])
    assert end_time.endswith("Z") and "T" in end_time
    assert call["metrics"]["best_epoch"] == 1  # type: ignore[index]


def test_a_failed_run_stamps_its_end_time(monkeypatch: pytest.MonkeyPatch) -> None:
    from glioma_selective.training import run as run_module

    calls = _capture_updates(monkeypatch)
    run_module._record_failure("RUN", RuntimeError("boom"))
    (call,) = calls
    assert call["status"] == "failed"
    assert "boom" in str(call["failure_reason"])
    assert str(call["end_time_utc"]).endswith("Z")

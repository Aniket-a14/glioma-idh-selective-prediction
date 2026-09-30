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

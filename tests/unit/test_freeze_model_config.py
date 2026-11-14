"""Freezers rebuild the network from the run record, not from base.yaml (D-051)."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from glioma_selective.evaluation.freeze import model_config_from_record
from glioma_selective.models.segresnet import ModelConfig
from glioma_selective.training.variants import VARIANTS, model_config_for

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("variant", VARIANTS)
def test_record_config_round_trips_every_variant(variant: str) -> None:
    expected = model_config_for(variant)
    record = {"config": {"model": asdict(expected)}}
    assert model_config_from_record(record) == expected


def test_whole_brain_record_is_not_rebuilt_as_the_base_model() -> None:
    record = {"config": {"model": asdict(model_config_for("whole_brain"))}}
    assert model_config_from_record(record).tumour_aware_pooling is False
    assert model_config_from_record(record) != ModelConfig()


def test_record_written_before_the_two_stage_field_still_loads() -> None:
    legacy = asdict(ModelConfig())
    del legacy["two_stage"]
    assert model_config_from_record({"config": {"model": legacy}}) == ModelConfig()


@pytest.mark.parametrize(
    "record", [{}, {"config": {}}, {"config": {"model": "x"}}, {"config": None}]
)
def test_record_without_a_model_config_is_an_error(record: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="config.model"):
        model_config_from_record(record)


@pytest.mark.parametrize(
    "path",
    [
        "scripts/freeze_predictions.py",
        "src/glioma_selective/evaluation/freeze_mc_dropout.py",
        "src/glioma_selective/evaluation/condition_sweep.py",
    ],
)
def test_freezers_do_not_read_the_shipped_base_model_config(path: str) -> None:
    source = (ROOT / path).read_text(encoding="utf-8")
    assert "base.yaml" not in source
    assert "model_config_from_record" in source

"""Config-composition round-trip test for the Hydra skeleton (T00.7).

Verifies the decision recorded in docs/research/DECISION_LOG.md D-013 is
actually mechanically sound: configs/config.yaml composes every declared
group's base.yaml without error, and the composed config survives a
YAML-dump-and-reload round trip unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

CONFIGS_DIR = Path(__file__).resolve().parent.parent.parent / "configs"

GROUPS = (
    "data",
    "preprocessing",
    "model",
    "training",
    "calibration",
    "selective",
    "evaluation",
)


@pytest.fixture()
def composed_config():
    with initialize_config_dir(config_dir=str(CONFIGS_DIR), version_base="1.3"):
        yield compose(config_name="config", overrides=["experiment_name=test"])


# Groups whose base.yaml still holds only the Hydra placeholder. A group leaves this
# tuple when its phase gives it real content (model, training: Phase 06).
PLACEHOLDER_GROUPS = (
    "data",
    "preprocessing",
    "calibration",
    "selective",
    "evaluation",
)


def test_every_group_composes(composed_config) -> None:
    for group in GROUPS:
        assert group in composed_config
    for group in PLACEHOLDER_GROUPS:
        assert composed_config[group]["_placeholder"] is True
    for group in ("model", "training"):
        assert "_placeholder" not in composed_config[group]


def test_root_level_fields_present(composed_config) -> None:
    assert composed_config.experiment_name == "test"
    assert composed_config.seed == 0
    assert composed_config.machine  # defaults to local-mac via oc.env resolver


def test_round_trip_through_yaml(composed_config) -> None:
    dumped = OmegaConf.to_yaml(composed_config)
    reloaded = OmegaConf.create(dumped)
    assert OmegaConf.to_container(reloaded, resolve=True) == OmegaConf.to_container(
        composed_config, resolve=True
    )


def test_every_group_directory_has_a_base_config() -> None:
    for group in GROUPS:
        base = CONFIGS_DIR / group / "base.yaml"
        assert base.is_file(), f"missing {base}"

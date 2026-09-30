"""Tests for the frozen evaluation-condition grid."""

from collections.abc import Callable
from pathlib import Path

import pytest
from omegaconf import DictConfig, OmegaConf

from glioma_selective.evaluation.conditions import (
    ConditionGrid,
    enumerate_cells,
    load_condition_grid,
)

CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs/evaluation/conditions.yaml"


def _write_variant(
    tmp_path: Path, name: str, mutate: Callable[[DictConfig], None]
) -> Path:
    config = OmegaConf.load(CONFIG_PATH)
    mutate(config)
    path = tmp_path / f"{name}.yaml"
    OmegaConf.save(config, path)
    return path


def _drop_first_modality_condition(config: DictConfig) -> None:
    del config.modality_conditions[0]


def _drop_first_cohort(config: DictConfig) -> None:
    del config.cohorts[0]


def _drop_first_mechanism(config: DictConfig) -> None:
    del config.mechanisms[0]


def _duplicate_modality_id(config: DictConfig) -> None:
    config.modality_conditions[1].id = config.modality_conditions[0].id


def _add_unknown_modality(config: DictConfig) -> None:
    config.modality_conditions[0].present.append("ADC")


def _overlap_present_and_zeroed(config: DictConfig) -> None:
    config.modality_conditions[1].present.append("T1")


def _leave_modality_unaccounted(config: DictConfig) -> None:
    config.modality_conditions[1].zeroed = []


def _remove_primary(config: DictConfig) -> None:
    config.mechanisms[4].primary = False


def _add_second_primary(config: DictConfig) -> None:
    config.mechanisms[0].primary = True


@pytest.fixture
def grid() -> ConditionGrid:
    return load_condition_grid(CONFIG_PATH)


def test_grid_counts_and_cells(grid: ConditionGrid) -> None:
    cells = enumerate_cells(grid)

    assert len(grid.modality_conditions) == 6
    assert len(grid.cohorts) == 3
    assert len(grid.mechanisms) == 6
    assert len(grid.modality_conditions) * len(grid.cohorts) == 18
    assert len(cells) == 108
    assert len({cell.cell_id for cell in cells}) == 108
    assert cells[0].cell_id == "M1__full__utsw_internal_test"
    assert cells[-1].cell_id == "M6__t1ce_flair_only__egd"


def test_default_path_and_order_are_deterministic() -> None:
    first = enumerate_cells(load_condition_grid())
    second = enumerate_cells(load_condition_grid())

    assert first == second


def test_egd_is_unavailable_with_blocker(grid: ConditionGrid) -> None:
    egd = next(cohort for cohort in grid.cohorts if cohort.id == "egd")

    assert egd.available is False
    assert egd.blocked_on == "D-018 EGD data-use agreement"


def test_only_m5_is_primary(grid: ConditionGrid) -> None:
    primary = tuple(mechanism.id for mechanism in grid.mechanisms if mechanism.primary)

    assert primary == ("M5",)


@pytest.mark.parametrize(
    ("condition_id", "modality"),
    [
        ("drop_t1", "T1"),
        ("drop_t1ce", "T1CE"),
        ("drop_t2", "T2"),
        ("drop_flair", "FLAIR"),
    ],
)
def test_each_drop_condition_zeroes_its_named_modality(
    grid: ConditionGrid, condition_id: str, modality: str
) -> None:
    condition = next(
        item for item in grid.modality_conditions if item.id == condition_id
    )

    assert condition.zeroed == (modality,)


def test_t1ce_flair_only_zeroes_t1_and_t2(grid: ConditionGrid) -> None:
    condition = next(
        item for item in grid.modality_conditions if item.id == "t1ce_flair_only"
    )

    assert condition.zeroed == ("T1", "T2")


@pytest.mark.parametrize(
    ("name", "mutate", "message"),
    [
        ("modality-count", _drop_first_modality_condition, "modality_conditions"),
        ("cohort-count", _drop_first_cohort, "cohorts"),
        ("mechanism-count", _drop_first_mechanism, "mechanisms"),
        ("duplicate-id", _duplicate_modality_id, "ids must be unique"),
        ("unknown-modality", _add_unknown_modality, "unknown modalities"),
        ("overlap", _overlap_present_and_zeroed, "must not overlap"),
        ("incomplete-cover", _leave_modality_unaccounted, "cover all four"),
        ("no-primary", _remove_primary, "exactly one mechanism"),
        ("two-primary", _add_second_primary, "exactly one mechanism"),
    ],
)
def test_invalid_grid_is_rejected(
    tmp_path: Path,
    name: str,
    mutate: Callable[[DictConfig], None],
    message: str,
) -> None:
    path = _write_variant(tmp_path, name, mutate)

    with pytest.raises(ValueError, match=message):
        load_condition_grid(path)


def test_conditions_config_does_not_mention_impute() -> None:
    assert "impute" not in CONFIG_PATH.read_text(encoding="utf-8").lower()

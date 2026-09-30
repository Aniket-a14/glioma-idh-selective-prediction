"""Load the frozen evaluation conditions and enumerate their result cells."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from omegaconf import OmegaConf

_MODALITIES = frozenset({"T1", "T1CE", "T2", "FLAIR"})
_EXPECTED_COUNTS = {
    "modality_conditions": 6,
    "cohorts": 3,
    "mechanisms": 6,
}


@dataclass(frozen=True)
class ModalityCondition:
    """A named combination of real and zeroed MRI modalities."""

    id: str
    label: str
    present: tuple[str, ...]
    zeroed: tuple[str, ...]


@dataclass(frozen=True)
class Cohort:
    """A cohort and its availability for the evaluation grid."""

    id: str
    role: str
    available: bool
    blocked_on: str | None = None


@dataclass(frozen=True)
class Mechanism:
    """An evaluation mechanism and its training and primary-result flags."""

    id: str
    name: str
    selective: bool
    needs_own_training_run: bool
    primary: bool
    note: str | None = None


@dataclass(frozen=True)
class Cell:
    """One mechanism evaluated for one modality condition and cohort."""

    mechanism_id: str
    modality_id: str
    cohort_id: str

    @property
    def cell_id(self) -> str:
        """Stable identifier for this result cell."""
        return f"{self.mechanism_id}__{self.modality_id}__{self.cohort_id}"


@dataclass(frozen=True)
class ConditionGrid:
    """Validated evaluation dimensions in their declared file order."""

    modality_conditions: tuple[ModalityCondition, ...]
    cohorts: tuple[Cohort, ...]
    mechanisms: tuple[Mechanism, ...]


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{context} keys must be strings")
    return cast(Mapping[str, object], value)


def _sequence(value: object, context: str) -> Sequence[object]:
    if not isinstance(value, list | tuple):
        raise ValueError(f"{context} must be a list")
    return value


def _string(value: object, context: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string")
    return value


def _boolean(value: object, context: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{context} must be a boolean")
    return value


def _optional_string(mapping: Mapping[str, object], key: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    return _string(value, key)


def _unique_ids(items: Sequence[object], context: str) -> None:
    ids = tuple(
        _string(_mapping(item, context).get("id"), f"{context}.id") for item in items
    )
    if len(ids) != len(set(ids)):
        raise ValueError(f"{context} ids must be unique")


def _modality_tuple(value: object, context: str) -> tuple[str, ...]:
    values = tuple(_string(modality, context) for modality in _sequence(value, context))
    unknown = set(values) - _MODALITIES
    if unknown:
        raise ValueError(f"{context} contains unknown modalities: {sorted(unknown)}")
    if len(values) != len(set(values)):
        raise ValueError(f"{context} contains duplicate modalities")
    return values


def _parse_modality_condition(value: object) -> ModalityCondition:
    item = _mapping(value, "modality condition")
    present = _modality_tuple(item.get("present"), "present")
    zeroed = _modality_tuple(item.get("zeroed"), "zeroed")
    if set(present) & set(zeroed):
        raise ValueError("present and zeroed modalities must not overlap")
    if set(present) | set(zeroed) != _MODALITIES:
        raise ValueError("present and zeroed modalities must cover all four modalities")
    return ModalityCondition(
        id=_string(item.get("id"), "modality condition.id"),
        label=_string(item.get("label"), "modality condition.label"),
        present=present,
        zeroed=zeroed,
    )


def _parse_cohort(value: object) -> Cohort:
    item = _mapping(value, "cohort")
    return Cohort(
        id=_string(item.get("id"), "cohort.id"),
        role=_string(item.get("role"), "cohort.role"),
        available=_boolean(item.get("available"), "cohort.available"),
        blocked_on=_optional_string(item, "blocked_on"),
    )


def _parse_mechanism(value: object) -> Mechanism:
    item = _mapping(value, "mechanism")
    return Mechanism(
        id=_string(item.get("id"), "mechanism.id"),
        name=_string(item.get("name"), "mechanism.name"),
        selective=_boolean(item.get("selective"), "mechanism.selective"),
        needs_own_training_run=_boolean(
            item.get("needs_own_training_run"), "mechanism.needs_own_training_run"
        ),
        primary=_boolean(item.get("primary"), "mechanism.primary"),
        note=_optional_string(item, "note"),
    )


def load_condition_grid(path: Path | None = None) -> ConditionGrid:
    """Load and validate the evaluation grid from a YAML file.

    With no path, the config is resolved relative to this package's repository.
    """
    config_path = (
        path
        if path is not None
        else Path(__file__).resolve().parents[3]
        / "configs"
        / "evaluation"
        / "conditions.yaml"
    )
    loaded = OmegaConf.load(config_path)
    raw = cast(object, OmegaConf.to_container(loaded, resolve=True))
    config = _mapping(raw, "condition grid")

    parsed: dict[str, tuple[object, ...]] = {}
    for key, expected_count in _EXPECTED_COUNTS.items():
        values = _sequence(config.get(key), key)
        if len(values) != expected_count:
            raise ValueError(f"{key} must contain exactly {expected_count} entries")
        _unique_ids(values, key)
        parsed[key] = tuple(values)

    modality_conditions = tuple(
        _parse_modality_condition(item) for item in parsed["modality_conditions"]
    )
    cohorts = tuple(_parse_cohort(item) for item in parsed["cohorts"])
    mechanisms = tuple(_parse_mechanism(item) for item in parsed["mechanisms"])
    primary_count = sum(mechanism.primary for mechanism in mechanisms)
    if primary_count != 1:
        raise ValueError("exactly one mechanism must be primary")

    return ConditionGrid(
        modality_conditions=modality_conditions,
        cohorts=cohorts,
        mechanisms=mechanisms,
    )


def enumerate_cells(grid: ConditionGrid) -> tuple[Cell, ...]:
    """Enumerate cells in cohort, modality, then mechanism file order."""
    return tuple(
        Cell(
            mechanism_id=mechanism.id,
            modality_id=modality.id,
            cohort_id=cohort.id,
        )
        for cohort in grid.cohorts
        for modality in grid.modality_conditions
        for mechanism in grid.mechanisms
    )

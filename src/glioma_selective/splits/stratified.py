"""Patient-level, IDH-stratified UTSW split construction."""

from __future__ import annotations

import csv
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
from omegaconf import OmegaConf

from glioma_selective.data.metadata import default_metadata_specs
from glioma_selective.leakage.id_normalization import Cohort, normalize_identifier

__all__ = [
    "SplitConfig",
    "SplitLabels",
    "load_split_config",
    "read_utsw_split_labels",
    "stratified_patient_split",
]

SPLIT_NAMES = ("train", "calibration", "internal_test")
IDH_CLASSES = ("mutant", "wildtype")


@dataclass(frozen=True)
class SplitConfig:
    """Fixed seed and proportions for a patient-level split."""

    seed: int
    train: float
    calibration: float
    internal_test: float
    stratify_on: str

    def validate(self) -> None:
        """Reject unsupported split definitions before randomization."""
        proportions = (self.train, self.calibration, self.internal_test)
        if any(not math.isfinite(value) or value < 0 for value in proportions):
            raise ValueError("split proportions must be finite and non-negative")
        if not math.isclose(sum(proportions), 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("split proportions must sum to 1")
        if any(value <= 0 for value in proportions):
            raise ValueError("each split proportion must be greater than zero")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            raise ValueError("split seed must be an integer")
        if self.stratify_on != "idh":
            raise ValueError("splits must be stratified on IDH")

    @property
    def proportions(self) -> dict[str, float]:
        """Return proportions in manifest split order."""
        return {
            "train": self.train,
            "calibration": self.calibration,
            "internal_test": self.internal_test,
        }


@dataclass(frozen=True)
class SplitLabels:
    """The IDH and exploratory 1p/19q labels for one UTSW patient."""

    idh: str
    one_p_nineteen_q: str


def _object_mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be a mapping")
    return cast(Mapping[str, object], value)


def _proportion(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("split proportions must be numeric")
    return float(value)


def load_split_config(path: Path) -> SplitConfig:
    """Load and validate split settings from the caller-selected YAML file."""
    raw_value: object = cast(object, OmegaConf.to_container(OmegaConf.load(path)))
    raw = _object_mapping(raw_value, "split config")
    expected_keys = {
        "seed",
        "train",
        "calibration",
        "internal_test",
        "stratify_on",
    }
    if set(raw) != expected_keys:
        raise ValueError("split config must contain exactly the documented fields")
    seed = raw["seed"]
    stratify_on = raw["stratify_on"]
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("split seed must be an integer")
    if not isinstance(stratify_on, str):
        raise ValueError("stratify_on must be a string")
    config = SplitConfig(
        seed=seed,
        train=_proportion(raw["train"]),
        calibration=_proportion(raw["calibration"]),
        internal_test=_proportion(raw["internal_test"]),
        stratify_on=stratify_on,
    )
    config.validate()
    return config


def _idh_class(value: str) -> str:
    normalized = "".join(
        character for character in value.casefold() if character.isalnum()
    )
    if normalized in {"mutated", "mutant", "idhmutated", "idhmutant"}:
        return "mutant"
    if normalized in {"wildtype", "idhwildtype", "wt"}:
        return "wildtype"
    raise ValueError("UTSW metadata contains an unsupported IDH category")


def _one_p_nineteen_q_class(value: str) -> str:
    normalized = "".join(
        character for character in value.casefold() if character.isalnum()
    )
    if normalized in {"", "na", "n/a"}:
        return "unlabeled"
    if normalized == "codeleted":
        return "codeleted"
    if normalized == "noncodeleted":
        return "non_codeleted"
    raise ValueError("UTSW metadata contains an unsupported 1p/19q category")


def read_utsw_split_labels(metadata_path: Path | None = None) -> dict[str, SplitLabels]:
    """Read UTSW labels, canonicalizing IDs and never opening other cohorts."""
    utsw_spec = next(
        spec for spec in default_metadata_specs() if spec.cohort == "UTSW-Glioma"
    )
    source = metadata_path if metadata_path is not None else utsw_spec.path
    labels: dict[str, SplitLabels] = {}
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=utsw_spec.delimiter)
        required = {utsw_spec.identifier_column, "IDH", "1p19Q CODEL"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("UTSW metadata is missing required split label columns")
        for row in reader:
            raw_id = row.get(utsw_spec.identifier_column)
            raw_idh = row.get("IDH")
            raw_one_p_nineteen_q = row.get("1p19Q CODEL")
            if not raw_id or raw_idh is None or raw_one_p_nineteen_q is None:
                raise ValueError("UTSW metadata contains an incomplete split label row")
            if raw_idh.strip().casefold() in {"", "na", "n/a"}:
                continue
            try:
                patient_id = normalize_identifier(raw_id, Cohort.UTSW)
            except ValueError as error:
                raise ValueError(
                    "UTSW metadata contains an invalid patient ID"
                ) from error
            if patient_id in labels:
                raise ValueError(
                    "UTSW metadata contains duplicate canonical patient IDs"
                )
            labels[patient_id] = SplitLabels(
                idh=_idh_class(raw_idh),
                one_p_nineteen_q=_one_p_nineteen_q_class(raw_one_p_nineteen_q),
            )
    return labels


def stratified_patient_split(
    roster: Sequence[str],
    labels: Mapping[str, SplitLabels],
    config: SplitConfig,
    *,
    excluded_ids: Sequence[str] = (),
) -> dict[str, tuple[str, ...]]:
    """Split canonical patient IDs within IDH classes using one PCG64 stream."""
    config.validate()
    if len(set(roster)) != len(roster):
        raise ValueError("split roster contains duplicate patient IDs")
    excluded = set(excluded_ids)
    retained = tuple(patient_id for patient_id in roster if patient_id not in excluded)
    if any(patient_id not in labels for patient_id in retained):
        raise ValueError("split roster contains an unlabeled patient")
    if any(labels[patient_id].idh not in IDH_CLASSES for patient_id in retained):
        raise ValueError("split roster contains an unsupported IDH class")

    rng = np.random.Generator(np.random.PCG64(config.seed))
    assigned: dict[str, list[str]] = {name: [] for name in SPLIT_NAMES}
    for idh_class in IDH_CLASSES:
        class_ids = sorted(
            patient_id for patient_id in retained if labels[patient_id].idh == idh_class
        )
        calibration_count = round(config.calibration * len(class_ids))
        test_count = round(config.internal_test * len(class_ids))
        train_count = len(class_ids) - calibration_count - test_count
        counts = (train_count, calibration_count, test_count)
        if any(count == 0 for count in counts):
            raise ValueError(
                f"IDH class {idh_class} is too small to populate every split"
            )
        shuffled = np.asarray(class_ids, dtype=str)
        rng.shuffle(shuffled)
        boundaries = (train_count, train_count + calibration_count)
        assigned["train"].extend(shuffled[: boundaries[0]].tolist())
        assigned["calibration"].extend(shuffled[boundaries[0] : boundaries[1]].tolist())
        assigned["internal_test"].extend(shuffled[boundaries[1] :].tolist())

    result = {name: tuple(sorted(assigned[name])) for name in SPLIT_NAMES}
    split_sets = [set(result[name]) for name in SPLIT_NAMES]
    if any(
        split_sets[left] & split_sets[right]
        for left in range(3)
        for right in range(left + 1, 3)
    ):
        raise RuntimeError("patient-level split produced overlapping IDs")
    if set().union(*split_sets) != set(retained):
        raise RuntimeError("patient-level split does not cover the retained roster")
    return result


def split_summary(
    splits: Mapping[str, Sequence[str]], labels: Mapping[str, SplitLabels]
) -> dict[str, object]:
    """Return count-only IDH and 1p/19q summaries for each split."""
    result: dict[str, object] = {}
    for split_name in SPLIT_NAMES:
        rows = [labels[patient_id] for patient_id in splits[split_name]]
        idh_counts = Counter(row.idh for row in rows)
        one_p_nineteen_q_counts = Counter(row.one_p_nineteen_q for row in rows)
        result[split_name] = {
            "count": len(rows),
            "idh": {key: idh_counts[key] for key in IDH_CLASSES},
            "1p/19q": dict(sorted(one_p_nineteen_q_counts.items())),
        }
    return result

"""Synthetic tests for patient-level IDH stratified splits and serialization."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import cast

import pytest
from scripts.make_splits import _freeze_split_manifest
from scripts.make_splits import main as make_splits_main

from glioma_selective.splits import (
    SplitConfig,
    SplitLabels,
    sha256_file,
    stratified_patient_split,
    verify_split_manifest,
    write_split_manifest,
)
from glioma_selective.splits import freeze as freeze_module


def _synthetic_labels(
    mutant_count: int = 10, wildtype_count: int = 30
) -> dict[str, SplitLabels]:
    labels: dict[str, SplitLabels] = {}
    for index in range(mutant_count):
        patient_id = f"UTSW-BT{index + 1:04d}"
        labels[patient_id] = SplitLabels(
            "mutant", "codeleted" if index % 2 == 0 else "unlabeled"
        )
    for index in range(wildtype_count):
        patient_id = f"UTSW-BT{index + mutant_count + 1:04d}"
        labels[patient_id] = SplitLabels(
            "wildtype", "non_codeleted" if index % 3 else "unlabeled"
        )
    return labels


def _config(seed: int = 20260930) -> SplitConfig:
    return SplitConfig(
        seed=seed,
        train=0.6,
        calibration=0.2,
        internal_test=0.2,
        stratify_on="idh",
    )


def test_hand_worked_10_mutant_30_wildtype_split_is_stratified() -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)
    splits = stratified_patient_split(roster, labels, _config())

    # Hand calculation: per class n_cal=round(0.2*n), n_test=round(0.2*n),
    # then train is the remainder: 10 -> 2/2/6 and 30 -> 6/6/18.
    assert {name: len(splits[name]) for name in splits} == {
        "train": 24,
        "calibration": 8,
        "internal_test": 8,
    }
    assert {
        name: {
            idh_class: sum(
                labels[patient_id].idh == idh_class for patient_id in splits[name]
            )
            for idh_class in ("mutant", "wildtype")
        }
        for name in splits
    } == {
        "train": {"mutant": 6, "wildtype": 18},
        "calibration": {"mutant": 2, "wildtype": 6},
        "internal_test": {"mutant": 2, "wildtype": 6},
    }


def test_split_is_disjoint_covers_roster_and_has_only_roster_ids() -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)
    splits = stratified_patient_split(roster, labels, _config())
    split_sets = {name: set(ids) for name, ids in splits.items()}

    for left, right in combinations(split_sets, 2):
        assert split_sets[left].isdisjoint(split_sets[right])
    union = set().union(*split_sets.values())
    assert union == set(roster)
    assert union <= set(roster)


def test_split_is_deterministic_and_a_different_seed_changes_assignment() -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)

    first = stratified_patient_split(roster, labels, _config())
    repeated = stratified_patient_split(roster, labels, _config())
    different = stratified_patient_split(roster, labels, _config(seed=20260931))

    assert first == repeated
    assert first != different


def test_excluded_patient_never_appears_in_any_split() -> None:
    labels = _synthetic_labels(mutant_count=11)
    roster = tuple(labels)
    excluded_id = "UTSW-BT0001"

    splits = stratified_patient_split(
        roster, labels, _config(), excluded_ids=(excluded_id,)
    )

    assert all(excluded_id not in split_ids for split_ids in splits.values())
    assert set().union(*(set(ids) for ids in splits.values())) == set(roster) - {
        excluded_id
    }


def test_manifest_is_byte_deterministic_and_verifies_exact_file_bytes(
    tmp_path: Path,
) -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)
    config = _config()
    splits = stratified_patient_split(roster, labels, config)
    exclusion_path = tmp_path / "exclusions.json"
    exclusion_path.write_text('{"exclusions": []}\n', encoding="utf-8")
    output_path = tmp_path / "first" / "splits.json"
    second_output_path = tmp_path / "second" / "splits.json"

    write_split_manifest(output_path, splits, labels, config, exclusion_path, roster)
    first_bytes = output_path.read_bytes()
    write_split_manifest(
        second_output_path, splits, labels, config, exclusion_path, roster
    )

    assert second_output_path.read_bytes() == first_bytes
    expected_hash = sha256_file(output_path)
    verify_split_manifest(output_path, expected_hash)
    output_path.write_bytes(first_bytes[:-1] + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        verify_split_manifest(output_path, expected_hash)


def test_freeze_writes_manifest_and_checksum_once(tmp_path: Path) -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)
    config = _config()
    splits = stratified_patient_split(roster, labels, config)
    exclusion_path = tmp_path / "exclusions.json"
    exclusion_path.write_text('{"exclusions": []}\n', encoding="utf-8")
    manifest_dir = tmp_path / "manifests"

    digest = _freeze_split_manifest(
        manifest_dir, splits, labels, config, exclusion_path, roster
    )

    manifest_path = manifest_dir / "splits.json"
    sidecar_path = manifest_dir / "splits.json.sha256"
    first_manifest = manifest_path.read_bytes()
    first_sidecar = sidecar_path.read_bytes()
    assert first_sidecar == f"{sha256_file(manifest_path)}  splits.json\n".encode(
        "ascii"
    )
    assert digest == sha256_file(manifest_path)
    verify_split_manifest(manifest_path, digest)

    with pytest.raises(FileExistsError, match="decision-log entry"):
        _freeze_split_manifest(
            manifest_dir, splits, labels, config, exclusion_path, roster
        )
    assert manifest_path.read_bytes() == first_manifest
    assert sidecar_path.read_bytes() == first_sidecar


def test_write_split_manifest_requires_opt_in_to_overwrite(tmp_path: Path) -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)
    first_config = _config()
    first_splits = stratified_patient_split(roster, labels, first_config)
    second_config = _config(seed=20261001)
    second_splits = stratified_patient_split(roster, labels, second_config)
    exclusion_path = tmp_path / "exclusions.json"
    exclusion_path.write_text('{"exclusions": []}\n', encoding="utf-8")
    manifest_path = tmp_path / "splits.json"

    write_split_manifest(
        manifest_path, first_splits, labels, first_config, exclusion_path, roster
    )
    original = manifest_path.read_bytes()
    with pytest.raises(FileExistsError):
        write_split_manifest(
            manifest_path, second_splits, labels, second_config, exclusion_path, roster
        )
    assert manifest_path.read_bytes() == original

    write_split_manifest(
        manifest_path,
        second_splits,
        labels,
        second_config,
        exclusion_path,
        roster,
        overwrite=True,
    )
    assert manifest_path.read_bytes() != original


def test_write_split_manifest_removes_temporary_file_after_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)
    config = _config()
    splits = stratified_patient_split(roster, labels, config)
    exclusion_path = tmp_path / "exclusions.json"
    exclusion_path.write_text('{"exclusions": []}\n', encoding="utf-8")
    manifest_path = tmp_path / "splits.json"

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(freeze_module.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated replace failure"):
        write_split_manifest(
            manifest_path, splits, labels, config, exclusion_path, roster
        )

    assert not manifest_path.exists()
    assert list(tmp_path.glob(".splits.json.*.tmp")) == []


def test_freeze_and_dry_run_are_rejected_together() -> None:
    with pytest.raises(SystemExit) as error:
        make_splits_main(["--freeze", "--dry-run"])

    assert error.value.code == 2


def test_manifest_matches_phase_05_regression_shape_and_assertions(
    tmp_path: Path,
) -> None:
    labels = _synthetic_labels()
    roster = tuple(labels)
    config = _config()
    splits = stratified_patient_split(roster, labels, config)
    exclusion_path = tmp_path / "exclusions.json"
    exclusion_path.write_text('{"exclusions": []}\n', encoding="utf-8")
    manifest_path = tmp_path / "splits.json"
    write_split_manifest(manifest_path, splits, labels, config, exclusion_path, roster)

    document = cast(
        dict[str, object], json.loads(manifest_path.read_text(encoding="utf-8"))
    )
    split_mapping = cast(dict[str, list[str]], document["splits"])
    expected_names = {"train", "calibration", "internal_test"}
    assert set(split_mapping) == expected_names
    split_sets: dict[str, set[str]] = {}
    for split_name, patient_ids in split_mapping.items():
        assert isinstance(patient_ids, list)
        assert all(isinstance(patient_id, str) for patient_id in patient_ids)
        assert patient_ids == sorted(patient_ids)
        split_sets[split_name] = set(patient_ids)
    for left, right in combinations(sorted(split_sets), 2):
        assert split_sets[left].isdisjoint(split_sets[right])
    all_split_ids = set().union(*split_sets.values())
    assert all_split_ids == set(roster)
    assert all_split_ids <= set(roster)

    assert document["manifest_version"] == 1
    assert document["seed"] == config.seed
    assert document["proportions"] == config.proportions
    assert document["stratify_on"] == "idh"
    assert document["source_exclusion_manifest_sha256"] == sha256_file(exclusion_path)
    summary = cast(dict[str, object], document["summary"])
    assert summary["population_count"] == len(roster)
    summary_splits = cast(dict[str, dict[str, object]], summary["splits"])
    assert set(summary_splits) == expected_names
    assert summary_splits["train"]["idh"] == {"mutant": 6, "wildtype": 18}
    assert summary_splits["calibration"]["idh"] == {"mutant": 2, "wildtype": 6}
    assert summary_splits["internal_test"]["idh"] == {"mutant": 2, "wildtype": 6}
    assert set(summary_splits["train"]["1p/19q"]) <= {
        "codeleted",
        "non_codeleted",
        "unlabeled",
    }


def test_invalid_proportions_are_rejected() -> None:
    labels = _synthetic_labels()
    invalid = SplitConfig(1, 0.6, 0.2, 0.3, "idh")

    with pytest.raises(ValueError, match="sum to 1"):
        stratified_patient_split(tuple(labels), labels, invalid)


def test_roster_patient_without_an_idh_label_is_rejected() -> None:
    labels = _synthetic_labels()
    roster = (*labels, "UTSW-BT9999")

    with pytest.raises(ValueError, match="unlabeled patient"):
        stratified_patient_split(roster, labels, _config())


def test_idh_class_too_small_to_populate_each_split_is_rejected() -> None:
    labels = _synthetic_labels(mutant_count=1, wildtype_count=30)

    with pytest.raises(ValueError, match="too small to populate every split"):
        stratified_patient_split(tuple(labels), labels, _config())

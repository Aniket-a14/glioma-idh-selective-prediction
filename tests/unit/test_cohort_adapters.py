"""Synthetic tests for the Phase 02 cohort adapter skeletons."""

from __future__ import annotations

from pathlib import Path

import pytest

from glioma_selective.data.adapters import (
    CanonicalSequence,
    SequenceIdentificationUnavailable,
    egd,
    ucsf_pdgm,
    utsw,
)


def _touch(directory: Path, filename: str) -> None:
    file_path = directory / filename
    file_path.write_bytes(b"synthetic fixture")


def test_utsw_discovery_and_sequence_identification_for_ten_patients(
    tmp_path: Path,
) -> None:
    root = tmp_path / "utsw"
    expected = {
        "brain_t1.nii.gz": CanonicalSequence.T1,
        "brain_t1ce.nii.gz": CanonicalSequence.T1CE,
        "brain_t2.nii.gz": CanonicalSequence.T2,
        "brain_flair.nii.gz": CanonicalSequence.FLAIR,
    }
    for index in range(1, 11):
        patient_directory = root / f"TEST-UTSW-{index:04d}"
        patient_directory.mkdir(parents=True)
        for filename in expected:
            _touch(patient_directory, filename)
        _touch(patient_directory, "brain_t1_ants.nii.gz")
        _touch(patient_directory, "tumorseg_manual_correction.nii.gz")

    inventories = utsw.discover_files(root)

    assert len(inventories) == 10
    assert [inventory.patient_id for inventory in inventories] == [
        f"TEST-UTSW-{index:04d}" for index in range(1, 11)
    ]
    for inventory in inventories:
        assert inventory.has_complete_core_sequences
        assert dict(inventory.sequence_files) == {
            sequence: inventory.files[
                next(
                    index
                    for index, file_path in enumerate(inventory.files)
                    if file_path.name == filename
                )
            ]
            for filename, sequence in expected.items()
        }
        assert len(inventory.files) == 6


def test_utsw_missing_sequence_is_reported_without_substitution(
    tmp_path: Path,
) -> None:
    patient_directory = tmp_path / "utsw" / "TEST-0001"
    patient_directory.mkdir(parents=True)
    _touch(patient_directory, "brain_t1.nii.gz")
    _touch(patient_directory, "brain_t1ce.nii.gz")
    _touch(patient_directory, "brain_t2_ants.nii.gz")

    inventory = utsw.discover_files(tmp_path / "utsw")[0]

    assert inventory.sequence_files == {
        CanonicalSequence.T1: patient_directory / "brain_t1.nii.gz",
        CanonicalSequence.T1CE: patient_directory / "brain_t1ce.nii.gz",
    }
    assert inventory.missing_sequences == (
        CanonicalSequence.T2,
        CanonicalSequence.FLAIR,
    )
    assert not inventory.has_complete_core_sequences


def test_ucsf_discovery_maps_ten_patients_and_ignores_bias_variants(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ucsf_pdgm"
    expected = {
        "_T1.nii.gz": CanonicalSequence.T1,
        "_T1c.nii.gz": CanonicalSequence.T1CE,
        "_T2.nii.gz": CanonicalSequence.T2,
        "_FLAIR.nii.gz": CanonicalSequence.FLAIR,
    }
    for index in range(1, 11):
        patient_directory = root / f"TEST-UCSF-{index:04d}_nifti"
        patient_directory.mkdir(parents=True)
        prefix = f"TEST-UCSF-{index:04d}"
        for suffix in expected:
            _touch(patient_directory, f"{prefix}{suffix}")
        for suffix in expected:
            _touch(patient_directory, f"{prefix}{suffix[:-7]}_bias.nii.gz")
        _touch(patient_directory, f"{prefix}_ADC.nii.gz")

    inventories = ucsf_pdgm.discover_files(root)

    assert len(inventories) == 10
    for inventory in inventories:
        assert inventory.has_complete_core_sequences
        prefix = inventory.patient_id.removesuffix("_nifti")
        assert {
            sequence: file_path.name
            for sequence, file_path in inventory.sequence_files.items()
        } == {
            CanonicalSequence.T1: f"{prefix}_T1.nii.gz",
            CanonicalSequence.T1CE: f"{prefix}_T1c.nii.gz",
            CanonicalSequence.T2: f"{prefix}_T2.nii.gz",
            CanonicalSequence.FLAIR: f"{prefix}_FLAIR.nii.gz",
        }
        assert len(inventory.files) == 9


def test_egd_discovery_has_the_same_inventory_shape_without_guessing_names(
    tmp_path: Path,
) -> None:
    root = tmp_path / "egd"
    for index in range(1, 11):
        (root / f"TEST-EGD-{index:04d}").mkdir(parents=True)

    inventories = egd.discover_files(root)

    assert len(inventories) == 10
    assert all(inventory.files == () for inventory in inventories)
    assert all(inventory.missing_sequences for inventory in inventories)


def test_egd_sequence_identification_fails_closed_until_inventory_is_available() -> (
    None
):
    with pytest.raises(SequenceIdentificationUnavailable):
        egd.identify_sequence(Path())

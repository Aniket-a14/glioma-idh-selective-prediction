"""Synthetic coverage for Phase 04 T04.1 discovery."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from glioma_selective.data.adapters import (
    CanonicalSequence,
    SequenceIdentificationUnavailable,
)
from glioma_selective.preprocessing.discovery import (
    build_geometry_report,
    discover_cases,
    inspect_volume_geometry,
)


def _write_volume(path: Path, *, affine: np.ndarray | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(
        np.zeros((4, 4, 4), dtype=np.float32),
        np.eye(4) if affine is None else affine,
    )
    nib.save(image, path)


def _write_utsw_case(
    root: Path,
    patient_id: str,
    *,
    missing: set[CanonicalSequence] | None = None,
) -> Path:
    missing = missing or set()
    patient_directory = root / patient_id
    filenames = {
        CanonicalSequence.T1: "brain_t1.nii.gz",
        CanonicalSequence.T1CE: "brain_t1ce.nii.gz",
        CanonicalSequence.T2: "brain_t2.nii.gz",
        CanonicalSequence.FLAIR: "brain_flair.nii.gz",
    }
    for sequence, filename in filenames.items():
        if sequence not in missing:
            _write_volume(patient_directory / filename)
    for filename in (
        "tumorseg_FeTS.nii.gz",
        "tumorseg_manual_correction.nii.gz",
        "rtumorseg_manual_correction.nii.gz",
    ):
        _write_volume(patient_directory / filename)
    return patient_directory


def _write_ucsf_case(root: Path, patient_id: str) -> Path:
    patient_directory = root / f"{patient_id}_nifti"
    suffixes = {
        CanonicalSequence.T1: "_T1.nii.gz",
        CanonicalSequence.T1CE: "_T1c.nii.gz",
        CanonicalSequence.T2: "_T2.nii.gz",
        CanonicalSequence.FLAIR: "_FLAIR.nii.gz",
    }
    for _sequence, suffix in suffixes.items():
        _write_volume(patient_directory / f"{patient_id}{suffix}")
    for role in (
        "tumor_segmentation",
        "brain_segmentation",
        "brain_parenchyma_segmentation",
    ):
        _write_volume(patient_directory / f"{patient_id}_{role}.nii.gz")
    return patient_directory


def test_utsw_discovery_normalizes_ids_and_keeps_missing_sequence_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path / "utsw"
    _write_utsw_case(root, "BT0001")
    _write_utsw_case(root, "BT0002", missing={CanonicalSequence.T2})

    cases = discover_cases("UTSW-Glioma", root=root)

    assert [case.patient_id for case in cases] == ["UTSW-BT0001", "UTSW-BT0002"]
    assert cases[0].sequence_files[CanonicalSequence.T1].name == "brain_t1.nii.gz"
    assert cases[1].missing_sequences == (CanonicalSequence.T2,)
    assert CanonicalSequence.T2 not in cases[1].sequence_files
    assert CanonicalSequence.T2 not in cases[1].geometries


def test_ucsf_discovery_selects_baseline_and_discovers_all_segmentation_roles(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ucsf_pdgm"
    baseline = _write_ucsf_case(root, "UCSF-PDGM-0001")
    _write_ucsf_case(root, "UCSF-PDGM-0001_FU016d")

    cases = discover_cases("ucsf_pdgm", root=root)

    assert len(cases) == 1
    case = cases[0]
    assert case.patient_id == "UCSF-PDGM-0001"
    assert case.source_directory == baseline
    assert set(case.segmentation_files) == {
        "tumor_segmentation",
        "brain_segmentation",
        "brain_parenchyma_segmentation",
    }
    assert not hasattr(case, "selected_segmentation")
    assert set(case.sequence_files) == set(CanonicalSequence)


def test_retained_filter_is_exact_and_absent_patient_raises(tmp_path: Path) -> None:
    root = tmp_path / "utsw"
    _write_utsw_case(root, "BT0001")
    _write_utsw_case(root, "BT0002")

    selected = discover_cases("utsw", root=root, retained_patient_ids=("BT0002",))
    assert [case.patient_id for case in selected] == ["UTSW-BT0002"]

    with pytest.raises(ValueError, match="absent"):
        discover_cases("utsw", root=root, retained_patient_ids=("BT9999",))


def test_egd_fails_closed_with_sequence_identification_error(tmp_path: Path) -> None:
    with pytest.raises(SequenceIdentificationUnavailable):
        discover_cases("egd", root=tmp_path / "egd")


def test_geometry_report_is_aggregate_only_and_counts_segmentation_roles(
    tmp_path: Path,
) -> None:
    root = tmp_path / "utsw"
    _write_utsw_case(root, "BT0001")
    _write_utsw_case(
        root,
        "BT0002",
        missing={CanonicalSequence.FLAIR},
    )
    cases = discover_cases("utsw", root=root)

    report = build_geometry_report(cases)
    serialized = json.dumps(report, sort_keys=True)

    assert report["schema_version"] == 1
    assert "BT0001" not in serialized
    assert str(root) not in serialized
    utsw_report = report["cohorts"]["utsw"]
    assert utsw_report["case_count"] == 2
    assert utsw_report["cases_with_four_identical_affines"] == 1
    assert utsw_report["cases_with_any_missing_sequence"] == 1
    assert utsw_report["segmentation_role_counts"] == {
        "rtumorseg_manual_correction": 2,
        "tumorseg_FeTS": 2,
        "tumorseg_manual_correction": 2,
    }
    assert utsw_report["sequences"]["T1"]["distinct_affine_hash_count"] == 1
    assert utsw_report["sequences"]["FLAIR"]["geometry_counts"][0]["case_count"] == 1


def test_truncated_gzip_after_nifti_header_is_geometry_readable(tmp_path: Path) -> None:
    complete = tmp_path / "complete.nii.gz"
    _write_volume(complete)
    with gzip.open(complete, "rb") as handle:
        header_only = handle.read(352)
    truncated = tmp_path / "header_only.nii.gz"
    with gzip.open(truncated, "wb") as handle:
        handle.write(header_only)

    geometry = inspect_volume_geometry(truncated)

    assert geometry.shape == (4, 4, 4)
    assert geometry.spacing == (1.0, 1.0, 1.0)
    assert geometry.orientation == "RAS"
    assert geometry.dtype == "float32"

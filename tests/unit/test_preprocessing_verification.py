"""Synthetic tests for Phase 04 preprocessing verification."""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.discovery import CaseRecord
from glioma_selective.preprocessing.verification import (
    ExpectedGrid,
    VerificationThresholds,
    build_verification_report,
    verify_case,
)

_SEQUENCE_NAMES = {
    CanonicalSequence.T1: "t1",
    CanonicalSequence.T1CE: "t1ce",
    CanonicalSequence.T2: "t2",
    CanonicalSequence.FLAIR: "flair",
}


def _write_volume(
    path: Path,
    values: np.ndarray,
    *,
    affine: np.ndarray | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(
        values.astype(np.float32),
        np.eye(4, dtype=np.float64) if affine is None else affine,
    )
    nib.save(image, path)


def _case(
    root: Path,
    *,
    t1ce: np.ndarray,
    other_mask: np.ndarray | None = None,
    affine_by_sequence: dict[CanonicalSequence, np.ndarray] | None = None,
    segmentation_shape: tuple[int, int, int] | None = None,
) -> CaseRecord:
    affine_by_sequence = affine_by_sequence or {}
    sequence_files: dict[CanonicalSequence, Path] = {}
    shape = t1ce.shape
    for sequence in CORE_SEQUENCES:
        values = t1ce if sequence is CanonicalSequence.T1CE else other_mask
        if values is None:
            values = t1ce
        path = root / f"{_SEQUENCE_NAMES[sequence]}.nii.gz"
        _write_volume(path, values, affine=affine_by_sequence.get(sequence))
        sequence_files[sequence] = path

    segmentation_files: dict[str, Path] = {}
    segmentation_values = np.zeros(
        segmentation_shape or shape,
        dtype=np.float32,
    )
    segmentation_values.flat[0] = 1
    segmentation_path = root / "tumorseg_FeTS.nii.gz"
    _write_volume(segmentation_path, segmentation_values)
    segmentation_files["tumorseg_FeTS"] = segmentation_path
    return CaseRecord(
        cohort=Cohort.UTSW,
        patient_id="UTSW-SYNTHETIC",
        source_directory=root,
        sequence_files=sequence_files,
        geometries={},
        segmentation_files=segmentation_files,
    )


def _expected(shape: tuple[int, int, int]) -> ExpectedGrid:
    return ExpectedGrid(shape=shape, spacing=(1.0, 1.0, 1.0), input_orientation="RAS")


def _thresholds() -> VerificationThresholds:
    return VerificationThresholds(
        min_cross_sequence_mask_dice=0.99,
        min_brain_fraction=0.05,
        max_brain_fraction=0.35,
    )


def test_clean_case_is_verified_passthrough_and_report_is_aggregate_only(
    tmp_path: Path,
) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    values[:4, :4, :4] = 1
    result = verify_case(
        _case(tmp_path, t1ce=values), _expected(values.shape), _thresholds()
    )

    assert result.status == "verified-passthrough"
    assert result.brain_voxel_fraction == 0.125
    assert result.cross_sequence_dice == {
        sequence.value: 1.0 for sequence in CORE_SEQUENCES
    }
    assert result.segmentation_inside_brain_fraction == {"tumorseg_FeTS": 1.0}
    report = build_verification_report([result])
    serialized = json.dumps(report, sort_keys=True)
    assert "UTSW-SYNTHETIC" not in serialized
    assert str(tmp_path) not in serialized
    assert report["cohorts"]["utsw"]["pass_count"] == 1


def test_all_zero_volume_is_corrupt(tmp_path: Path) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    result = verify_case(
        _case(tmp_path, t1ce=values), _expected(values.shape), _thresholds()
    )

    assert result.status == "failed"
    assert result.failure_categories == ("corrupt",)
    assert result.checks["T1ce.readable"].failure_category == "corrupt"


def test_skullstrip_bounds_report_over_and_under(tmp_path: Path) -> None:
    over = np.ones((8, 8, 8), dtype=np.float32)
    over_result = verify_case(
        _case(tmp_path / "over", t1ce=over), _expected(over.shape), _thresholds()
    )
    assert over_result.failure_categories == ("skullstrip-over",)

    under = np.zeros((8, 8, 8), dtype=np.float32)
    under[0, 0, 0] = 1
    under_result = verify_case(
        _case(tmp_path / "under", t1ce=under), _expected(under.shape), _thresholds()
    )
    assert under_result.failure_categories == ("skullstrip-under",)


def test_mask_disagreement_is_registration_failure(tmp_path: Path) -> None:
    t1ce = np.zeros((8, 8, 8), dtype=np.float32)
    t1ce[:4, :4, :4] = 1
    other = np.zeros_like(t1ce)
    other[4:, 4:, 4:] = 1
    result = verify_case(
        _case(tmp_path, t1ce=t1ce, other_mask=other),
        _expected(t1ce.shape),
        _thresholds(),
    )

    assert result.failure_categories == ("registration-failed",)
    assert result.cross_sequence_dice["T1"] == 0.0


def test_affine_mismatch_is_orientation_failure(tmp_path: Path) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    values[:4, :4, :4] = 1
    shifted = np.eye(4, dtype=np.float64)
    shifted[0, 3] = 2
    result = verify_case(
        _case(
            tmp_path,
            t1ce=values,
            affine_by_sequence={CanonicalSequence.T2: shifted},
        ),
        _expected(values.shape),
        _thresholds(),
    )

    assert result.failure_categories == ("orientation-wrong",)
    assert result.checks["cross_sequence.affine"].passed is False


def test_segmentation_shape_mismatch_is_caught_without_inside_gate(
    tmp_path: Path,
) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    values[:4, :4, :4] = 1
    result = verify_case(
        _case(tmp_path, t1ce=values, segmentation_shape=(7, 8, 8)),
        _expected(values.shape),
        _thresholds(),
    )

    assert result.failure_categories == ("orientation-wrong",)
    alignment = result.checks["segmentation.tumorseg_FeTS.alignment"]
    assert alignment.passed is False
    assert "segmentation.tumorseg_FeTS.inside_brain_fraction" in result.checks

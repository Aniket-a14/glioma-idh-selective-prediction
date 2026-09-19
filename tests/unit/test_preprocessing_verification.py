"""Synthetic tests for Phase 04 preprocessing verification."""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

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
    segmentation_values: np.ndarray | None = None,
    segmentation_affine: np.ndarray | None = None,
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
    if segmentation_values is None:
        segmentation_values = np.zeros(
            segmentation_shape or shape,
            dtype=np.float32,
        )
        segmentation_values.flat[0] = 1
    segmentation_path = root / "tumorseg_FeTS.nii.gz"
    _write_volume(segmentation_path, segmentation_values, affine=segmentation_affine)
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
    return VerificationThresholds()


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
    segmentation = result.segmentation_findings["tumorseg_FeTS"]
    assert segmentation.readable is True
    assert segmentation.empty is False
    assert segmentation.grid_matches_t1ce is True
    assert segmentation.inside_brain_fraction == 1.0
    assert segmentation.dice_self == 1.0
    report = build_verification_report([result])
    serialized = json.dumps(report, sort_keys=True)
    assert "UTSW-SYNTHETIC" not in serialized
    assert str(tmp_path) not in serialized
    assert report["schema_version"] == 2
    assert report["cohorts"]["utsw"]["pass_count"] == 1
    assert report["cohorts"]["utsw"]["borderline_count"] == 0
    assert report["cohorts"]["utsw"]["failed_count"] == 0
    assert report["cohorts"]["utsw"]["segmentation"]["tumorseg_FeTS"] == {
        "readable": 1,
        "empty": 0,
        "grid_matches_t1ce": 1,
        "inside_brain_fraction_distribution": {
            "min": 1.0,
            "p1": 1.0,
            "median": 1.0,
            "p99": 1.0,
            "max": 1.0,
        },
    }


def test_all_zero_volume_is_corrupt(tmp_path: Path) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    result = verify_case(
        _case(tmp_path, t1ce=values), _expected(values.shape), _thresholds()
    )

    assert result.status == "failed"
    assert result.failure_categories == ("corrupt",)
    assert result.checks["T1ce.readable"].failure_category == "corrupt"


def test_skullstrip_bounds_name_physical_conditions(tmp_path: Path) -> None:
    skull_retained = np.ones((8, 8, 8), dtype=np.float32)
    over_result = verify_case(
        _case(tmp_path / "skull-retained", t1ce=skull_retained),
        _expected(skull_retained.shape),
        _thresholds(),
    )
    assert over_result.failure_categories == ("skullstrip-under",)

    brain_removed = np.zeros((8, 8, 8), dtype=np.float32)
    brain_removed[0, 0, 0] = 1
    under_result = verify_case(
        _case(tmp_path / "brain-removed", t1ce=brain_removed),
        _expected(brain_removed.shape),
        _thresholds(),
    )
    assert under_result.failure_categories == ("skullstrip-over",)


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


def test_segmentation_shape_mismatch_is_informational_only(
    tmp_path: Path,
) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    values[:4, :4, :4] = 1
    result = verify_case(
        _case(tmp_path, t1ce=values, segmentation_shape=(7, 8, 8)),
        _expected(values.shape),
        _thresholds(),
    )

    assert result.status == "verified-passthrough"
    assert result.failure_categories == ()
    finding = result.segmentation_findings["tumorseg_FeTS"]
    assert finding.readable is True
    assert finding.empty is False
    assert finding.grid_matches_t1ce is False
    assert finding.inside_brain_fraction is None


def test_empty_segmentation_is_not_corrupt_and_has_no_inside_fraction(
    tmp_path: Path,
) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    values[:4, :4, :4] = 1
    result = verify_case(
        _case(
            tmp_path,
            t1ce=values,
            segmentation_values=np.zeros_like(values),
        ),
        _expected(values.shape),
        _thresholds(),
    )

    finding = result.segmentation_findings["tumorseg_FeTS"]
    assert result.status == "verified-passthrough"
    assert result.failure_categories == ()
    assert finding.readable is True
    assert finding.empty is True
    assert finding.grid_matches_t1ce is True
    assert finding.inside_brain_fraction is None
    assert finding.dice_self == 1.0


def test_borderline_dice_is_sent_to_visual_qc_without_failure(
    tmp_path: Path,
) -> None:
    t1ce = np.zeros((10, 10, 25), dtype=np.float32)
    t1ce.flat[:625] = 1
    other = t1ce.copy()
    other.flat[:7] = 0
    other.flat[625:632] = 1

    result = verify_case(
        _case(tmp_path, t1ce=t1ce, other_mask=other),
        _expected(t1ce.shape),
        _thresholds(),
    )

    assert result.status == "verified-borderline"
    assert result.failure_categories == ()
    assert result.cross_sequence_dice["T1"] == pytest.approx(0.9888)
    assert "T1.cross_sequence_mask_dice" in result.borderline_checks
    assert result.checks["T1.cross_sequence_mask_dice"].passed is True
    assert result.checks["T1.cross_sequence_mask_dice"].borderline is True
    report = build_verification_report([result])
    cohort_report = report["cohorts"]["utsw"]
    assert cohort_report["pass_count"] == 0
    assert cohort_report["borderline_count"] == 1
    assert cohort_report["failed_count"] == 0
    assert (
        cohort_report["borderline_counts_by_check"]["T1.cross_sequence_mask_dice"] == 1
    )


def test_dice_below_fail_threshold_is_registration_failure(tmp_path: Path) -> None:
    t1ce = np.zeros((8, 8, 8), dtype=np.float32)
    t1ce[:4, :4, :4] = 1
    other = np.zeros_like(t1ce)
    other[4:, 4:, 4:] = 1
    result = verify_case(
        _case(tmp_path, t1ce=t1ce, other_mask=other),
        _expected(t1ce.shape),
        _thresholds(),
    )

    assert result.status == "failed"
    assert result.failure_categories == ("registration-failed",)


def test_unreadable_segmentation_does_not_change_case_status(tmp_path: Path) -> None:
    values = np.zeros((8, 8, 8), dtype=np.float32)
    values[:4, :4, :4] = 1
    case = _case(tmp_path, t1ce=values)
    segmentation_path = case.segmentation_files["tumorseg_FeTS"]
    segmentation_path.write_bytes(b"not a NIfTI file")

    result = verify_case(case, _expected(values.shape), _thresholds())

    assert result.status == "verified-passthrough"
    assert result.failure_categories == ()
    finding = result.segmentation_findings["tumorseg_FeTS"]
    assert finding.readable is False
    assert finding.empty is None
    assert finding.grid_matches_t1ce is None
    assert finding.inside_brain_fraction is None
    assert finding.dice_self is None


def test_threshold_ordering_is_validated() -> None:
    with pytest.raises(ValueError, match="borderline mask Dice"):
        VerificationThresholds(
            min_cross_sequence_mask_dice=0.996,
            borderline_cross_sequence_mask_dice=0.995,
        )
    with pytest.raises(ValueError, match="brain-fraction borderline"):
        VerificationThresholds(
            min_brain_fraction=0.09,
            borderline_min_brain_fraction=0.08,
        )

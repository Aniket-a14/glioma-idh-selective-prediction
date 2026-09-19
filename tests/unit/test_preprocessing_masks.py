"""Unit tests for D-028 segmentation target selection and alignment."""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from glioma_selective.data.adapters._common import CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.cache import StageCache
from glioma_selective.preprocessing.discovery import CaseRecord, inspect_volume_geometry
from glioma_selective.preprocessing.masks import (
    SegmentationTarget,
    build_mask_report,
    inspect_segmentation_target,
    remap_labels,
    run_mask_stage,
    select_segmentation_file,
)


def _write_nifti(path: Path, data: np.ndarray, affine: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(data, affine), path)


def _case(
    root: Path,
    *,
    cohort: Cohort = Cohort.UTSW,
    mask: np.ndarray | None = None,
    mask_affine: np.ndarray | None = None,
    t1ce_affine: np.ndarray | None = None,
    include_fets: bool = True,
) -> CaseRecord:
    affine = np.diag([1.0, 1.0, 1.0, 1.0])
    shape = (4, 5, 6)
    t1ce_path = root / "brain_t1ce.nii.gz"
    _write_nifti(
        t1ce_path,
        np.zeros(shape, dtype=np.float32),
        t1ce_affine if t1ce_affine is not None else affine,
    )
    segmentation_files: dict[str, Path] = {}
    if mask is not None:
        role = "tumorseg_FeTS" if cohort is Cohort.UTSW else "tumor_segmentation"
        mask_path = root / f"{role}.nii.gz"
        _write_nifti(
            mask_path,
            mask,
            mask_affine if mask_affine is not None else affine,
        )
        segmentation_files[role] = mask_path
    if include_fets and cohort is Cohort.UTSW and mask is None:
        manual_path = root / "tumorseg_manual_correction.nii.gz"
        _write_nifti(manual_path, np.ones(shape, dtype=np.uint8), affine)
        segmentation_files["tumorseg_manual_correction"] = manual_path
    return CaseRecord(
        cohort=cohort,
        patient_id="synthetic-patient",
        source_directory=root,
        sequence_files={CanonicalSequence.T1CE: t1ce_path},
        geometries={CanonicalSequence.T1CE: inspect_volume_geometry(t1ce_path)},
        segmentation_files=segmentation_files,
    )


def test_remap_labels_uses_the_brat_convention() -> None:
    result = remap_labels(np.array([[0, 1, 2, 4]], dtype=np.int16))
    np.testing.assert_array_equal(result, np.array([[0, 1, 2, 3]], dtype=np.uint8))
    assert result.dtype == np.uint8


@pytest.mark.parametrize("label", [3, 5])
def test_remap_labels_names_each_stray_label(label: int) -> None:
    with pytest.raises(ValueError, match=str(label)):
        remap_labels(np.array([0, label], dtype=np.int16))


def test_selects_only_the_decided_target_roles(tmp_path: Path) -> None:
    utsw_case = _case(tmp_path / "utsw", mask=np.ones((4, 5, 6), dtype=np.uint8))
    assert (
        select_segmentation_file(utsw_case)
        == utsw_case.segmentation_files["tumorseg_FeTS"]
    )

    ucsf_case = _case(
        tmp_path / "ucsf",
        cohort=Cohort.UCSF_PDGM,
        mask=np.ones((4, 5, 6), dtype=np.uint8),
        include_fets=False,
    )
    assert (
        select_segmentation_file(ucsf_case)
        == ucsf_case.segmentation_files["tumor_segmentation"]
    )


def test_manual_correction_is_never_a_fallback(tmp_path: Path) -> None:
    case = _case(tmp_path / "manual-only", mask=None)
    assert select_segmentation_file(case) is None
    target = inspect_segmentation_target(case)
    assert target.has_segmentation is False
    assert target.class_voxel_counts == {}


def test_empty_mask_is_kept_but_has_no_segmentation(tmp_path: Path) -> None:
    case = _case(tmp_path / "empty", mask=np.zeros((4, 5, 6), dtype=np.uint8))
    target = inspect_segmentation_target(case)
    assert target.has_segmentation is False
    assert target.class_voxel_counts == {0: 120}
    assert target.grid_matches_t1ce is True


def test_inspection_detects_grid_mismatch_and_stage_refuses_it(tmp_path: Path) -> None:
    case = _case(
        tmp_path / "mismatch",
        mask=np.zeros((4, 5, 6), dtype=np.uint8),
        mask_affine=np.diag([1.0, 1.0, 2.0, 1.0]),
    )
    target = inspect_segmentation_target(case)
    assert target.grid_matches_t1ce is False
    with pytest.raises(ValueError, match="grid"):
        run_mask_stage(StageCache(tmp_path / "cache"), case, {})


def test_stage_reorients_losslessly_and_writes_exact_integer_labels(
    tmp_path: Path,
) -> None:
    mask = np.zeros((4, 5, 6), dtype=np.int16)
    mask[0, 1, 2] = 4
    mask[2, 3, 4] = 1
    affine = np.array(
        [
            [0.0, 1.0, 0.0, 10.0],
            [-1.0, 0.0, 0.0, 20.0],
            [0.0, 0.0, 1.0, 30.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    case = _case(
        tmp_path / "stage",
        mask=mask,
        mask_affine=affine,
        t1ce_affine=affine,
    )
    output_path = run_mask_stage(StageCache(tmp_path / "cache"), case, {})
    output = nib.load(output_path)
    values = np.asarray(output.dataobj)
    assert nib.aff2axcodes(output.affine) == ("R", "A", "S")
    assert output.get_data_dtype() == np.dtype(np.uint8)
    assert set(np.unique(values)) <= {0, 1, 2, 3}
    assert np.array_equal(np.argwhere(values == 3), [[1, 3, 2]])
    assert np.array_equal(np.argwhere(values == 1), [[3, 1, 4]])


def test_stage_reuses_cache_and_recomputes_when_input_changes(tmp_path: Path) -> None:
    mask = np.zeros((4, 5, 6), dtype=np.uint8)
    mask[1, 2, 3] = 1
    case = _case(tmp_path / "cache-case", mask=mask)
    cache = StageCache(tmp_path / "cache")
    first = run_mask_stage(cache, case, {})
    first_bytes = first.read_bytes()
    second = run_mask_stage(cache, case, {})
    assert second == first
    assert second.read_bytes() == first_bytes

    mask_path = case.segmentation_files["tumorseg_FeTS"]
    changed = mask.copy()
    changed[3, 4, 5] = 4
    _write_nifti(mask_path, changed, np.eye(4))
    third = run_mask_stage(cache, case, {})
    assert third != first
    assert set(np.unique(np.asarray(nib.load(third).dataobj))) == {0, 1, 3}


def test_mask_report_is_aggregate_only(tmp_path: Path) -> None:
    utsw = _case(
        tmp_path / "report-utsw",
        mask=np.array(
            [[[0, 1], [2, 4]]],
            dtype=np.uint8,
        ),
    )
    ucsf = _case(
        tmp_path / "report-ucsf",
        cohort=Cohort.UCSF_PDGM,
        mask=np.zeros((1, 2, 2), dtype=np.uint8),
        include_fets=False,
    )
    report = build_mask_report(
        [inspect_segmentation_target(utsw), inspect_segmentation_target(ucsf)]
    )
    assert report["cohorts"]["utsw"]["cases"] == 1  # type: ignore[index]
    assert report["cohorts"]["utsw"]["observed_label_sets"] == {  # type: ignore[index]
        "0,1,2,4": 1
    }
    assert report["cohorts"]["ucsf_pdgm"]["has_segmentation"] == {  # type: ignore[index]
        "true": 0,
        "false": 1,
    }
    serialized = json.dumps(report)
    assert "synthetic-patient" not in serialized
    assert str(tmp_path) not in serialized


def test_segmentation_target_is_frozen() -> None:
    target = SegmentationTarget(
        Cohort.UTSW,
        "synthetic",
        True,
        {0: 2},
        True,
    )
    with pytest.raises((AttributeError, TypeError)):
        target.has_segmentation = False  # type: ignore[misc]

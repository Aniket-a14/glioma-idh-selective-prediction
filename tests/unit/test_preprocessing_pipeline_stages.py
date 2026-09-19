"""Unit tests for the resumable Phase 04 pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import nibabel as nib
import numpy as np
import pytest
import scripts.run_preprocessing as run_script

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing import discovery, n4, pipeline
from glioma_selective.preprocessing.status import PreprocessingStatusManifest
from glioma_selective.preprocessing.verification import (
    CaseVerification,
    FailureCategory,
)


def _verification(
    patient_id: str,
    *,
    status: str = "verified-passthrough",
    qc_reasons: tuple[str, ...] = (),
) -> CaseVerification:
    del qc_reasons
    return CaseVerification(
        cohort=Cohort.UTSW,
        patient_id=patient_id,
        status=status,
        checks={},
        failure_categories=cast(tuple[FailureCategory, ...], ()),
        borderline_checks=(),
        brain_voxel_fraction=None,
        cross_sequence_dice={},
        segmentation_findings={},
    )


def _make_case(
    root: Path, patient_id: str, *, shape: tuple[int, int, int] = (8, 8, 8)
) -> discovery.CaseRecord:
    case_root = root / patient_id
    case_root.mkdir(parents=True)
    affine = np.diag([-1.0, -1.0, 1.0, 1.0])
    values = np.zeros(shape, dtype=np.float32)
    margin = 2
    values[margin:-margin, margin:-margin, margin:-margin] = 2.0
    mask = np.zeros(shape, dtype=np.uint8)
    mask[
        margin + 1 : -margin + 1, margin + 1 : -margin + 1, margin + 1 : -margin + 1
    ] = 1
    sequence_files: dict[CanonicalSequence, Path] = {}
    for index, sequence in enumerate(CORE_SEQUENCES):
        volume = values.copy()
        volume[2:6, 2:6, 2:6] += np.float32(index * 0.25)
        path = case_root / f"{sequence.value}.nii.gz"
        nib.save(nib.Nifti1Image(volume, affine), path)
        sequence_files[sequence] = path
    mask_path = case_root / "tumorseg_FeTS.nii.gz"
    nib.save(nib.Nifti1Image(mask, affine), mask_path)
    return discovery.CaseRecord(
        cohort=Cohort.UTSW,
        patient_id=patient_id,
        source_directory=case_root,
        sequence_files=sequence_files,
        geometries={},
        segmentation_files={"tumorseg_FeTS": mask_path},
    )


def _setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    patient_ids: tuple[str, ...],
    *,
    shape: tuple[int, int, int] = (8, 8, 8),
) -> tuple[dict[str, discovery.CaseRecord], Path, Path, Path]:
    input_root = tmp_path / "inputs"
    cases = {
        patient_id: _make_case(input_root, patient_id, shape=shape)
        for patient_id in patient_ids
    }

    def discover(
        cohort: Cohort | str,
        *,
        retained_patient_ids: object = None,
        root: Path | None = None,
    ) -> tuple[discovery.CaseRecord, ...]:
        del root
        assert Cohort(cohort) is Cohort.UTSW
        assert retained_patient_ids is not None
        return tuple(cases[patient_id] for patient_id in sorted(retained_patient_ids))

    monkeypatch.setattr(pipeline.discovery, "discover_cases", discover)
    status_path = tmp_path / "manifests" / "preprocessing_status.json"
    outputs_path = tmp_path / "manifests" / "preprocessing_outputs.json"
    cache_root = tmp_path / "processed"
    monkeypatch.setattr(
        pipeline.paths, "private_data_dir", lambda: tmp_path / "private"
    )
    PreprocessingStatusManifest.from_verification(
        tuple(_verification(patient_id) for patient_id in patient_ids)
    ).save(status_path)
    return cases, cache_root, status_path, outputs_path


def _fast_n4(
    image: nib.Nifti1Image, params: n4.N4Parameters, *, n_threads: int
) -> nib.Nifti1Image:
    del params, n_threads
    return nib.Nifti1Image(
        np.asarray(image.dataobj, dtype=np.float32), np.asarray(image.affine)
    )


def test_case_runs_end_to_end_and_report_has_no_identity_or_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cases, cache_root, status_path, outputs_path = _setup(
        tmp_path, monkeypatch, ("case-a",)
    )
    params = n4.N4Parameters(
        shrink_factor=1, max_iterations=(1, 1, 1), histogram_bins=16
    )
    result = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
        n4_params=params,
    )

    assert result.exit_code == 0
    assert result.cohorts["utsw"]["cases_processed"] == 1
    assert result.cohorts["utsw"]["volumes_computed"] == 4
    assert result.cohorts["utsw"]["masks_computed"] == 1
    output_index = json.loads(outputs_path.read_text(encoding="utf-8"))
    output = output_index["utsw"]["case-a"]
    assert output["has_segmentation"] is True
    for sequence in CORE_SEQUENCES:
        volume_path = (
            cache_root
            / "volume"
            / output[sequence.value][:2]
            / output[sequence.value]
            / "volume.nii.gz"
        )
        image = nib.load(volume_path)
        assert nib.aff2axcodes(image.affine) == ("R", "A", "S")
        assert image.shape == (8, 8, 8)
        assert image.get_data_dtype() == np.dtype(np.float32)
        array = np.asarray(image.dataobj)
        assert np.all(array[array != 0] > 0)
        assert np.all(array[0] == 0)

    loaded_status = PreprocessingStatusManifest.load(status_path)
    case_status = loaded_status.cases[("utsw", "case-a")]
    assert case_status.stages["n4"].state == "done"
    assert case_status.stages["reorient"].state == "done"
    assert case_status.stages["mask"].state == "done"

    assert capsys.readouterr().out == ""
    assert "case-a" not in json.dumps(result.to_dict())
    assert str(tmp_path) not in json.dumps(result.to_dict())
    assert cases["case-a"].patient_id == "case-a"


def test_case_with_negative_t2_voxels_preserves_them_through_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases, cache_root, status_path, outputs_path = _setup(
        tmp_path, monkeypatch, ("case-a",), shape=(16, 16, 16)
    )
    t2_path = cases["case-a"].sequence_files[CanonicalSequence.T2]
    t2_image = nib.load(t2_path)
    t2_values = np.asarray(t2_image.dataobj, dtype=np.float32)
    negative_indices = ((5, 5, 5), (6, 6, 6), (7, 7, 7))
    for index in negative_indices:
        t2_values[index] = -1.0
    nib.save(nib.Nifti1Image(t2_values, t2_image.affine), t2_path)

    result = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
        n4_params=n4.N4Parameters(
            shrink_factor=2, max_iterations=(1, 1, 1), histogram_bins=16
        ),
    )

    assert result.exit_code == 0
    output_index = json.loads(outputs_path.read_text(encoding="utf-8"))
    t2_key = output_index["utsw"]["case-a"][CanonicalSequence.T2.value]
    t2_output = nib.load(cache_root / "volume" / t2_key[:2] / t2_key / "volume.nii.gz")
    output_values = np.asarray(t2_output.dataobj)
    assert t2_output.get_data_dtype() == np.dtype(np.float32)
    assert np.all(np.isfinite(output_values))
    assert np.count_nonzero(output_values == 0.0) == output_values.size - 12**3
    assert np.count_nonzero(output_values < 0) == len(negative_indices)
    assert np.all(np.signbit(output_values[output_values < 0]))


def test_excluded_case_is_skipped_and_failing_volume_does_not_stop_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases, cache_root, status_path, outputs_path = _setup(
        tmp_path, monkeypatch, ("case-a", "case-b", "case-excluded")
    )
    manifest = PreprocessingStatusManifest.load(status_path)
    manifest = manifest.merge_verification(
        (_verification("case-excluded", status="failed"),)
    ).record_exclusion("utsw", "case-excluded", "corrupt")
    manifest.save(status_path)

    calls = 0

    def fail_first(
        image: nib.Nifti1Image, params: n4.N4Parameters, *, n_threads: int
    ) -> nib.Nifti1Image:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("synthetic volume failure")
        return _fast_n4(image, params, n_threads=n_threads)

    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", fail_first)
    result = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
    )

    assert result.exit_code == 1
    counts = result.cohorts["utsw"]
    assert counts["skipped_excluded"] == 1
    assert counts["failed"] == 1
    assert counts["cases_processed"] == 1
    assert json.loads(outputs_path.read_text(encoding="utf-8"))["utsw"].keys() == {
        "case-b"
    }
    failed_status = PreprocessingStatusManifest.load(status_path).cases[
        ("utsw", "case-a")
    ]
    assert failed_status.stages["n4"].state == "failed"
    assert failed_status.stages["reorient"].state == "failed"
    assert failed_status.stages["mask"].state == "done"
    assert cases["case-excluded"].patient_id == "case-excluded"


def test_failures_are_aggregated_and_private_log_is_replaced_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cases, cache_root, status_path, outputs_path = _setup(
        tmp_path, monkeypatch, ("case-a", "case-b")
    )
    private_dir = tmp_path / "private"
    monkeypatch.setattr(pipeline.paths, "private_data_dir", lambda: private_dir)
    case_b_mask = cases["case-b"].segmentation_files["tumorseg_FeTS"]
    changed_mask_bytes = bytearray(case_b_mask.read_bytes())
    changed_mask_bytes[4] ^= 1
    case_b_mask.write_bytes(changed_mask_bytes)

    volume_calls = 0

    def fail_first_volume(
        image: nib.Nifti1Image, params: n4.N4Parameters, *, n_threads: int
    ) -> nib.Nifti1Image:
        nonlocal volume_calls
        volume_calls += 1
        if volume_calls == 1:
            raise RuntimeError("volume detail /private/case-a")
        return _fast_n4(image, params, n_threads=n_threads)

    original_mask_stage = pipeline.masks.run_mask_stage

    def fail_case_b_mask(
        cache: object, case: discovery.CaseRecord, params: object = None
    ) -> Path:
        if case.patient_id == "case-b":
            raise ValueError("mask detail /private/case-b")
        return original_mask_stage(cache, case, params)

    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", fail_first_volume)
    monkeypatch.setattr(pipeline.masks, "run_mask_stage", fail_case_b_mask)
    arguments = [
        "--cohort",
        "utsw",
        "--cache-root",
        str(cache_root),
        "--status-path",
        str(status_path),
        "--outputs-path",
        str(outputs_path),
    ]
    assert run_script.main(arguments) == 1
    printed = capsys.readouterr().out
    report = json.loads(printed)
    reasons = report["cohorts"]["utsw"]["failure_reasons"]
    assert reasons == {
        "mask": {"ValueError": 1},
        "volume:T1": {"RuntimeError": 1},
    }
    assert "case-a" not in printed
    assert "case-b" not in printed
    assert "volume detail" not in printed
    assert "mask detail" not in printed
    assert str(tmp_path) not in printed

    failure_log = private_dir / "preprocessing_failures.json"
    failures = json.loads(failure_log.read_text(encoding="utf-8"))
    assert failures == [
        {
            "canonical_id": "case-a",
            "cohort": "utsw",
            "exception_class": "RuntimeError",
            "message": "volume detail /private/case-a",
            "stage": "volume:T1",
        },
        {
            "canonical_id": "case-b",
            "cohort": "utsw",
            "exception_class": "ValueError",
            "message": "mask detail /private/case-b",
            "stage": "mask",
        },
    ]

    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", _fast_n4)
    monkeypatch.setattr(pipeline.masks, "run_mask_stage", original_mask_stage)
    assert run_script.main(arguments) == 0
    clean_printed = capsys.readouterr().out
    clean_report = json.loads(clean_printed)
    assert clean_report["cohorts"]["utsw"]["failure_reasons"] == {}
    assert json.loads(failure_log.read_text(encoding="utf-8")) == []


def test_cli_dry_run_writes_nothing_and_prints_counts_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _cases, cache_root, status_path, outputs_path = _setup(
        tmp_path, monkeypatch, ("case-a",)
    )
    private_dir = tmp_path / "private"
    monkeypatch.setattr(pipeline.paths, "private_data_dir", lambda: private_dir)
    result = run_script.main(
        [
            "--cohort",
            "utsw",
            "--cache-root",
            str(cache_root),
            "--status-path",
            str(status_path),
            "--outputs-path",
            str(outputs_path),
            "--dry-run",
        ]
    )

    assert result == 0
    printed = capsys.readouterr().out
    assert "case-a" not in printed
    assert str(tmp_path) not in printed
    assert not outputs_path.exists()
    assert not cache_root.exists()
    assert not (private_dir / "preprocessing_failures.json").exists()
    assert (
        PreprocessingStatusManifest.load(status_path)
        .cases[("utsw", "case-a")]
        .stages["mask"]
        .state
        == "pending"
    )

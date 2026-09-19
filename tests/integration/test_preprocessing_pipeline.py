"""Integration tests for pipeline reuse, interruption, and invalidation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

import nibabel as nib
import numpy as np
import pytest

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing import discovery, n4, pipeline
from glioma_selective.preprocessing.status import PreprocessingStatusManifest
from glioma_selective.preprocessing.verification import (
    CaseVerification,
    FailureCategory,
)


def _case(root: Path, patient_id: str) -> discovery.CaseRecord:
    case_root = root / patient_id
    case_root.mkdir(parents=True)
    affine = np.diag([-1.0, -1.0, 1.0, 1.0])
    values = np.zeros((8, 8, 8), dtype=np.float32)
    values[2:6, 2:6, 2:6] = 2.0 + np.float32(int(patient_id[-1]) * 0.1)
    mask = np.zeros((8, 8, 8), dtype=np.uint8)
    mask[3:5, 3:5, 3:5] = 1
    sequences: dict[CanonicalSequence, Path] = {}
    for index, sequence in enumerate(CORE_SEQUENCES):
        volume = values.copy()
        volume[2:6, 2:6, 2:6] += np.float32(index * 0.25)
        volume_path = case_root / f"{sequence.value}.nii.gz"
        nib.save(nib.Nifti1Image(volume, affine), volume_path)
        sequences[sequence] = volume_path
    mask_path = case_root / "tumorseg_FeTS.nii.gz"
    nib.save(nib.Nifti1Image(mask, affine), mask_path)
    return discovery.CaseRecord(
        cohort=Cohort.UTSW,
        patient_id=patient_id,
        source_directory=case_root,
        sequence_files=sequences,
        geometries={},
        segmentation_files={"tumorseg_FeTS": mask_path},
    )


def _verification(patient_id: str) -> CaseVerification:
    return CaseVerification(
        cohort=Cohort.UTSW,
        patient_id=patient_id,
        status="verified-passthrough",
        checks={},
        failure_categories=cast(tuple[FailureCategory, ...], ()),
        borderline_checks=(),
        brain_voxel_fraction=None,
        cross_sequence_dice={},
        segmentation_findings={},
    )


def _setup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    patient_ids: tuple[str, ...] = ("case-0", "case-1", "case-2", "case-3"),
) -> tuple[dict[str, discovery.CaseRecord], Path, Path, Path]:
    input_root = tmp_path / "inputs"
    cases = {patient_id: _case(input_root, patient_id) for patient_id in patient_ids}

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
        tuple(_verification(patient_id) for patient_id in cases)
    ).save(status_path)
    return cases, cache_root, status_path, outputs_path


def _fast_n4(
    image: nib.Nifti1Image, params: n4.N4Parameters, *, n_threads: int
) -> nib.Nifti1Image:
    del params, n_threads
    return nib.Nifti1Image(
        np.asarray(image.dataobj, dtype=np.float32), np.asarray(image.affine)
    )


@pytest.mark.integration
def test_unit_and_integration_pipeline_modules_collect_together() -> None:
    repository_root = Path(__file__).parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "tests/unit/test_preprocessing_pipeline_stages.py",
            "tests/integration/test_preprocessing_pipeline.py",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.integration
def test_pipeline_resumes_and_invalidates_only_changed_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases, cache_root, status_path, outputs_path = _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", _fast_n4)
    n4_calls = 0
    mask_calls = 0
    original_mask_stage = pipeline.masks.run_mask_stage

    def counted_n4(
        image: nib.Nifti1Image, params: n4.N4Parameters, *, n_threads: int
    ) -> nib.Nifti1Image:
        nonlocal n4_calls
        n4_calls += 1
        return _fast_n4(image, params, n_threads=n_threads)

    def counted_mask(
        cache: object, case: discovery.CaseRecord, params: object = None
    ) -> Path:
        nonlocal mask_calls
        mask_calls += 1
        return original_mask_stage(cache, case, params)

    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", counted_n4)
    monkeypatch.setattr(pipeline.masks, "run_mask_stage", counted_mask)
    first = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
    )
    first_outputs = json.loads(outputs_path.read_text(encoding="utf-8"))
    assert first.exit_code == 0
    assert n4_calls == 16
    assert mask_calls == 4

    second = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
    )
    assert second.exit_code == 0
    assert n4_calls == 16
    assert mask_calls == 4
    assert second.cohorts["utsw"]["volumes_computed"] == 0
    assert second.cohorts["utsw"]["masks_computed"] == 0

    changed_params = n4.N4Parameters(
        shrink_factor=1, max_iterations=(2, 1, 1), histogram_bins=16
    )
    third = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
        n4_params=changed_params,
    )
    changed_outputs = json.loads(outputs_path.read_text(encoding="utf-8"))
    assert third.exit_code == 0
    assert n4_calls == 32
    assert mask_calls == 4
    for patient_id in cases:
        for sequence in CORE_SEQUENCES:
            assert (
                first_outputs["utsw"][patient_id][sequence.value]
                != changed_outputs["utsw"][patient_id][sequence.value]
            )
        assert (
            first_outputs["utsw"][patient_id]["mask"]
            == changed_outputs["utsw"][patient_id]["mask"]
        )

    mask_path = cases["case-2"].segmentation_files["tumorseg_FeTS"]
    changed_mask_bytes = bytearray(mask_path.read_bytes())
    # Change the gzip member timestamp bytes without changing the NIfTI data.
    changed_mask_bytes[4] ^= 1
    mask_path.write_bytes(changed_mask_bytes)
    fourth = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
        n4_params=changed_params,
    )
    touched_outputs = json.loads(outputs_path.read_text(encoding="utf-8"))
    assert fourth.exit_code == 0
    assert n4_calls == 32
    assert mask_calls == 5
    assert (
        touched_outputs["utsw"]["case-2"]["mask"]
        != changed_outputs["utsw"]["case-2"]["mask"]
    )
    for patient_id, case in cases.items():
        for sequence in CORE_SEQUENCES:
            output_key = touched_outputs["utsw"][patient_id][sequence.value]
            image = nib.load(
                cache_root / "volume" / output_key[:2] / output_key / "volume.nii.gz"
            )
            assert image.shape == (8, 8, 8)
            assert nib.aff2axcodes(image.affine) == ("R", "A", "S")
        assert case.patient_id == patient_id


@pytest.mark.integration
def test_excluded_outputs_are_pruned_without_deleting_cache_or_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _cases, cache_root, status_path, outputs_path = _setup(
        tmp_path, monkeypatch, ("case-0", "case-1")
    )
    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", _fast_n4)

    first = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
    )
    assert first.exit_code == 0
    first_outputs = json.loads(outputs_path.read_text(encoding="utf-8"))
    excluded_output = first_outputs["utsw"]["case-1"]
    before_dry_run = outputs_path.read_bytes()

    manifest = PreprocessingStatusManifest.load(status_path).record_exclusion(
        "utsw", "case-1", "corrupt"
    )
    manifest.save(status_path)

    dry_run = pipeline.run_pipeline(
        "utsw",
        limit=1,
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
        dry_run=True,
    )
    assert dry_run.exit_code == 0
    assert dry_run.cohorts["utsw"]["skipped_excluded"] == 1
    assert dry_run.cohorts["utsw"]["outputs_pruned"] == 1
    assert outputs_path.read_bytes() == before_dry_run

    pruned = pipeline.run_pipeline(
        "utsw",
        limit=1,
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
    )
    assert pruned.exit_code == 0
    assert pruned.cohorts["utsw"]["outputs_pruned"] == 1
    assert pruned.to_dict()["cohorts"]["utsw"]["outputs_pruned"] == 1
    assert json.loads(outputs_path.read_text(encoding="utf-8"))["utsw"].keys() == {
        "case-0"
    }

    for sequence in CORE_SEQUENCES:
        volume_key = excluded_output[sequence.value]
        assert (
            cache_root / "volume" / volume_key[:2] / volume_key / "volume.nii.gz"
        ).is_file()
    mask_key = excluded_output["mask"]
    assert (cache_root / "mask" / mask_key[:2] / mask_key / "mask.nii.gz").is_file()

    excluded_status = PreprocessingStatusManifest.load(status_path).cases[
        ("utsw", "case-1")
    ]
    assert excluded_status.visual_qc == "failed"
    assert excluded_status.stages["n4"].state == "done"
    assert excluded_status.stages["reorient"].state == "done"
    assert excluded_status.stages["mask"].state == "done"

    second = pipeline.run_pipeline(
        "utsw",
        limit=1,
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
    )
    assert second.exit_code == 0
    assert second.cohorts["utsw"]["outputs_pruned"] == 0


@pytest.mark.integration
def test_interrupted_run_leaves_no_partial_entry_and_restarts_from_saved_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _cases, cache_root, status_path, outputs_path = _setup(tmp_path, monkeypatch)
    calls = 0

    def interrupt_on_third_case(
        image: nib.Nifti1Image, params: n4.N4Parameters, *, n_threads: int
    ) -> nib.Nifti1Image:
        nonlocal calls
        calls += 1
        if calls == 9:
            raise KeyboardInterrupt
        return _fast_n4(image, params, n_threads=n_threads)

    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", interrupt_on_third_case)
    with pytest.raises(KeyboardInterrupt):
        pipeline.run_pipeline(
            "utsw",
            cache_root=cache_root,
            status_path=status_path,
            outputs_path=outputs_path,
            n_threads=1,
        )

    saved_outputs = json.loads(outputs_path.read_text(encoding="utf-8"))
    assert set(saved_outputs["utsw"]) == {"case-0", "case-1"}
    assert not list(cache_root.rglob("*.tmp"))
    assert len(list(cache_root.joinpath("volume").rglob("volume.nii.gz"))) == 8

    restart_n4_calls = 0
    restart_mask_calls = 0

    def restart_n4(
        image: nib.Nifti1Image, params: n4.N4Parameters, *, n_threads: int
    ) -> nib.Nifti1Image:
        nonlocal restart_n4_calls
        restart_n4_calls += 1
        return _fast_n4(image, params, n_threads=n_threads)

    original_mask_stage = pipeline.masks.run_mask_stage

    def restart_mask(
        cache: object, case: discovery.CaseRecord, params: object = None
    ) -> Path:
        nonlocal restart_mask_calls
        restart_mask_calls += 1
        return original_mask_stage(cache, case, params)

    monkeypatch.setattr(pipeline.n4, "correct_bias_nifti", restart_n4)
    monkeypatch.setattr(pipeline.masks, "run_mask_stage", restart_mask)
    result = pipeline.run_pipeline(
        "utsw",
        cache_root=cache_root,
        status_path=status_path,
        outputs_path=outputs_path,
        n_threads=1,
    )

    assert result.exit_code == 0
    assert restart_n4_calls == 8
    assert restart_mask_calls == 2
    assert len(list(cache_root.rglob("*.tmp"))) == 0

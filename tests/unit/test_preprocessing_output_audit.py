"""Synthetic tests for the Phase 04 output audit."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from glioma_selective.leakage.cohort_manifest import (
    ROSTER_CONSTRUCTION,
    compute_roster_sha256,
)
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.cache import StageCache
from glioma_selective.preprocessing.output_audit import audit_preprocessing_outputs
from glioma_selective.preprocessing.verification import ExpectedGrid

Shape = tuple[int, int, int]
Mutator = Callable[
    [dict[str, np.ndarray], np.ndarray], tuple[dict[str, np.ndarray], np.ndarray]
]


def _write(path: Path, values: np.ndarray, affine: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = nib.Nifti1Image(values, affine)
    nib.save(image, path)


def _make_fixture(
    tmp_path: Path,
    *,
    mutator: Mutator | None = None,
    roster_id: str = "UTSW-BT0001",
    patient_id: str = "UTSW-BT0001",
) -> tuple[Path, Path, Path, Path]:
    shape: Shape = (16, 16, 16)
    affine = np.eye(4, dtype=np.float64)
    values = np.zeros(shape, dtype=np.float32)
    values[2:10, 2:10, 2:10] = 1.0
    volumes = {sequence: values.copy() for sequence in ("T1", "T1ce", "T2", "FLAIR")}
    mask = np.zeros(shape, dtype=np.int16)
    mask[3:6, 3:6, 3:6] = 1
    if mutator is not None:
        volumes, mask = mutator(volumes, mask)

    cache_root = tmp_path / "cache"
    source = tmp_path / "source"
    cache = StageCache(cache_root)
    output_entry: dict[str, object] = {"has_segmentation": True}
    for index, sequence in enumerate(("T1", "T1ce", "T2", "FLAIR")):
        input_directory = source / f"volume-{sequence}"
        input_directory.mkdir(parents=True)
        volume_path = input_directory / "volume.nii.gz"
        volume_affine = affine
        _write(volume_path, volumes[sequence], volume_affine)
        key = f"volume-key-{index}"
        cache.put("volume", key, input_directory)
        output_entry[sequence] = key
    mask_directory = source / "mask"
    _write(mask_directory / "mask.nii.gz", mask, affine)
    mask_key = "mask-key"
    cache.put("mask", mask_key, mask_directory)
    output_entry["mask"] = mask_key

    outputs_path = tmp_path / "preprocessing_outputs.json"
    outputs_path.write_text(
        json.dumps({"utsw": {patient_id: output_entry}}), encoding="utf-8"
    )
    manifest_path = tmp_path / "cohort_manifest_post_qc.json"
    digest = compute_roster_sha256((roster_id,), Cohort.UTSW)
    manifest_path.write_text(
        json.dumps(
            {
                "cohorts": {
                    "utsw": {
                        "retained_patient_count": 1,
                        "roster_sha256": digest,
                        "roster_construction": ROSTER_CONSTRUCTION,
                    },
                    "ucsf_pdgm": {
                        "retained_patient_count": 0,
                        "roster_sha256": compute_roster_sha256((), Cohort.UCSF_PDGM),
                        "roster_construction": ROSTER_CONSTRUCTION,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "audit.json"
    failures_path = tmp_path / "private" / "failures.json"
    return outputs_path, manifest_path, output_path, failures_path


def _run(
    tmp_path: Path,
    *,
    mutator: Mutator | None = None,
    roster_id: str = "UTSW-BT0001",
) -> dict[str, object]:
    outputs, manifest, output, failures = _make_fixture(
        tmp_path, mutator=mutator, roster_id=roster_id
    )
    return audit_preprocessing_outputs(
        outputs_path=outputs,
        cohort_manifest_path=manifest,
        output_path=output,
        failures_path=failures,
        cache_root=tmp_path / "cache",
        expected=ExpectedGrid(shape=(16, 16, 16), input_orientation="RAS"),
    )


def test_clean_outputs_pass_and_report_is_aggregate_only(tmp_path: Path) -> None:
    report = _run(tmp_path)
    assert report["passed"] is True
    cohort = report["cohorts"]["utsw"]
    assert cohort["case_count"] == 1
    assert cohort["volumes_checked"] == 4
    assert cohort["roster_digest_match"] is True
    assert cohort["mask_summary"]["minimum_mask_in_footprint_fraction"] == 1.0
    assert "UTSW-BT0001" not in json.dumps(report)


@pytest.mark.parametrize(
    "name,mutator",
    [
        (
            "wrong_dtype",
            lambda volumes, mask: (
                {**volumes, "T1": volumes["T1"].astype(np.int16)},
                mask,
            ),
        ),
        (
            "wrong_shape",
            lambda volumes, mask: ({**volumes, "T2": volumes["T2"][:-1]}, mask),
        ),
        (
            "nan",
            lambda volumes, mask: (
                {
                    **volumes,
                    "FLAIR": np.where(
                        np.indices(volumes["FLAIR"].shape).sum(axis=0) == 0,
                        np.nan,
                        volumes["FLAIR"],
                    ).astype(np.float32),
                },
                mask,
            ),
        ),
        (
            "too_many_negatives",
            lambda volumes, mask: (
                {
                    **volumes,
                    "T1ce": np.where(
                        volumes["T1ce"] != 0,
                        -1.0,
                        volumes["T1ce"],
                    ).astype(np.float32),
                },
                mask,
            ),
        ),
        (
            "footprint_dice",
            lambda volumes, mask: (
                {
                    **volumes,
                    "T1": np.pad(volumes["T1"][2:, 2:, 2:], ((0, 2), (0, 2), (0, 2))),
                },
                mask,
            ),
        ),
        (
            "illegal_label",
            lambda volumes, mask: (
                volumes,
                (mask + np.where(mask != 0, 4, 0)).astype(np.int16),
            ),
        ),
        (
            "segmentation_mismatch",
            lambda volumes, mask: (volumes, np.zeros_like(mask)),
        ),
        (
            "mask_outside",
            lambda volumes, mask: _mask_with_outside_voxel(volumes, mask),
        ),
    ],
)
def test_each_voxel_or_label_failure_is_reported(
    tmp_path: Path, name: str, mutator: Mutator
) -> None:
    del name
    report = _run(tmp_path, mutator=mutator)
    assert report["passed"] is False


def _mask_with_outside_voxel(
    volumes: dict[str, np.ndarray], mask: np.ndarray
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    mutated = mask.copy()
    mutated[0, 0, 0] = 1
    return volumes, mutated


def test_roster_digest_mismatch_is_reported(tmp_path: Path) -> None:
    report = _run(tmp_path, roster_id="UTSW-BT0002")
    assert report["passed"] is False
    assert report["cohorts"]["utsw"]["roster_digest_match"] is False


def test_missing_cache_entry_is_reported(tmp_path: Path) -> None:
    outputs, manifest, output, failures = _make_fixture(tmp_path)
    payload = json.loads(outputs.read_text(encoding="utf-8"))
    payload["utsw"]["UTSW-BT0001"]["T2"] = "missing-key"
    outputs.write_text(json.dumps(payload), encoding="utf-8")
    report = audit_preprocessing_outputs(
        outputs_path=outputs,
        cohort_manifest_path=manifest,
        output_path=output,
        failures_path=failures,
        cache_root=tmp_path / "cache",
        expected=ExpectedGrid(shape=(16, 16, 16), input_orientation="RAS"),
    )
    assert report["passed"] is False
    assert failures.exists()
    assert "UTSW-BT0001" in failures.read_text(encoding="utf-8")


def test_clean_audit_clears_previous_failure_log(tmp_path: Path) -> None:
    outputs, manifest, output, failures = _make_fixture(tmp_path)
    clean_payload = json.loads(outputs.read_text(encoding="utf-8"))
    failed_payload = json.loads(json.dumps(clean_payload))
    failed_payload["utsw"]["UTSW-BT0001"]["T2"] = "missing-key"
    outputs.write_text(json.dumps(failed_payload), encoding="utf-8")

    failed_report = audit_preprocessing_outputs(
        outputs_path=outputs,
        cohort_manifest_path=manifest,
        output_path=output,
        failures_path=failures,
        cache_root=tmp_path / "cache",
        expected=ExpectedGrid(shape=(16, 16, 16), input_orientation="RAS"),
    )
    assert failed_report["passed"] is False
    assert json.loads(failures.read_text(encoding="utf-8"))["failures"]

    outputs.write_text(json.dumps(clean_payload), encoding="utf-8")
    clean_report = audit_preprocessing_outputs(
        outputs_path=outputs,
        cohort_manifest_path=manifest,
        output_path=output,
        failures_path=failures,
        cache_root=tmp_path / "cache",
        expected=ExpectedGrid(shape=(16, 16, 16), input_orientation="RAS"),
    )
    assert clean_report["passed"] is True
    assert json.loads(failures.read_text(encoding="utf-8")) == {"failures": []}


def test_wrong_orientation_and_affine_mismatch_are_caught(tmp_path: Path) -> None:
    outputs, manifest, output, failures = _make_fixture(tmp_path)
    cache = StageCache(tmp_path / "cache")
    directory = tmp_path / "wrong-affine"
    affine = np.eye(4, dtype=np.float64)
    affine[0, 0] = -1
    values = np.zeros((16, 16, 16), dtype=np.float32)
    values[2:10, 2:10, 2:10] = 1
    _write(directory / "volume.nii.gz", values, affine)
    cache.put("volume", "wrong-affine-key", directory)
    payload = json.loads(outputs.read_text(encoding="utf-8"))
    payload["utsw"]["UTSW-BT0001"]["T1"] = "wrong-affine-key"
    outputs.write_text(json.dumps(payload), encoding="utf-8")
    report = audit_preprocessing_outputs(
        outputs_path=outputs,
        cohort_manifest_path=manifest,
        output_path=output,
        failures_path=failures,
        cache_root=tmp_path / "cache",
        expected=ExpectedGrid(shape=(16, 16, 16), input_orientation="RAS"),
    )
    assert report["passed"] is False
    checks = report["cohorts"]["utsw"]["checks"]
    assert checks["volume_geometry"]["failed"] == 1
    assert checks["cross_volume_affine_shape"]["failed"] == 1


def test_mask_on_a_different_grid_is_caught(tmp_path: Path) -> None:
    outputs, manifest, output, failures = _make_fixture(tmp_path)
    cache = StageCache(tmp_path / "cache")
    directory = tmp_path / "wrong-mask-grid"
    affine = np.eye(4, dtype=np.float64)
    affine[1, 3] = 2.0
    mask = np.zeros((16, 16, 16), dtype=np.int16)
    mask[3:6, 3:6, 3:6] = 1
    _write(directory / "mask.nii.gz", mask, affine)
    cache.put("mask", "wrong-mask-key", directory)
    payload = json.loads(outputs.read_text(encoding="utf-8"))
    payload["utsw"]["UTSW-BT0001"]["mask"] = "wrong-mask-key"
    outputs.write_text(json.dumps(payload), encoding="utf-8")
    report = audit_preprocessing_outputs(
        outputs_path=outputs,
        cohort_manifest_path=manifest,
        output_path=output,
        failures_path=failures,
        cache_root=tmp_path / "cache",
        expected=ExpectedGrid(shape=(16, 16, 16), input_orientation="RAS"),
    )
    assert report["passed"] is False
    assert report["cohorts"]["utsw"]["checks"]["mask_properties"]["failed"] == 1

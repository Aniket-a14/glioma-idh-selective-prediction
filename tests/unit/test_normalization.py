"""T04.6 normalization: statistics come from the frozen UTSW train split only."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest
import scripts.fit_normalization_stats as script

from glioma_selective.data.adapters._common import CORE_SEQUENCES
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.normalize import (
    NormalizationStats,
    PatientMoments,
    combine_moments,
    fit_normalization_stats,
    load_normalization_stats,
    normalize_volume,
    patient_moments,
    write_normalization_stats,
)

# Hand-worked: patient A brain voxels {2, 4, 6}, patient B brain voxel {10}.
# Pooled {2, 4, 6, 10}: mean 5.5, squared deviations 12.25 + 2.25 + 0.25 + 20.25 = 35,
# population variance 35 / 4 = 8.75, std = sqrt(8.75).
VOLUME_A = np.array([0, 2, 4, 0, 6], dtype=np.float32)
VOLUME_B = np.array([0, 10, 0, 0], dtype=np.float32)
POOLED_MEAN = 5.5
POOLED_STD = math.sqrt(8.75)


def _write_manifest(directory: Path, train: list[str], *, sidecar: bool = True) -> Path:
    document = {
        "splits": {
            "train": train,
            "calibration": ["UTSW-BT0900"],
            "internal_test": ["UTSW-BT0901"],
        }
    }
    path = directory / "splits.json"
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
    if sidecar:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        (directory / "splits.json.sha256").write_text(f"{digest}  splits.json\n")
    return path


def _moments() -> dict[str, dict[str, PatientMoments]]:
    a, b = patient_moments(VOLUME_A), patient_moments(VOLUME_B)
    names = [sequence.value for sequence in CORE_SEQUENCES]
    return {
        "UTSW-BT0001": {name: a for name in names},
        "UTSW-BT0002": {name: b for name in names},
    }


def _fit(tmp_path: Path) -> NormalizationStats:
    manifest = _write_manifest(tmp_path, ["UTSW-BT0001", "UTSW-BT0002"])
    return fit_normalization_stats(
        _moments(), cohort=Cohort.UTSW, split_name="train", split_manifest_path=manifest
    )


def test_patient_moments_match_hand_values_and_ignore_background() -> None:
    moments = patient_moments(VOLUME_A)
    assert (moments.n, moments.mean, moments.m2) == (3, 4.0, 8.0)


def test_combine_moments_matches_hand_values_in_either_order() -> None:
    a, b = patient_moments(VOLUME_A), patient_moments(VOLUME_B)
    for pooled in (combine_moments([a, b]), combine_moments([b, a])):
        assert pooled.n == 4
        assert math.isclose(pooled.mean, POOLED_MEAN)
        assert math.isclose(pooled.m2, 35.0)


def test_combine_moments_matches_numpy_on_random_patients() -> None:
    rng = np.random.default_rng(3)
    volumes = [rng.normal(300, 80, size=(6, 7, 5)).astype(np.float32) for _ in range(5)]
    pooled = combine_moments([patient_moments(volume) for volume in volumes])
    every = np.concatenate([volume.ravel() for volume in volumes]).astype(np.float64)
    assert pooled.n == every.size
    assert math.isclose(pooled.mean, every.mean(), rel_tol=1e-12)
    assert math.isclose(math.sqrt(pooled.m2 / pooled.n), every.std(), rel_tol=1e-12)


def test_patient_moments_rejects_empty_brain_and_non_finite_values() -> None:
    with pytest.raises(ValueError):
        patient_moments(np.zeros((3, 3), dtype=np.float32))
    with pytest.raises(ValueError):
        patient_moments(np.array([1.0, np.nan], dtype=np.float32))


def test_fit_records_provenance_and_hand_statistics(tmp_path: Path) -> None:
    stats = _fit(tmp_path)
    manifest = tmp_path / "splits.json"
    assert stats.fit_cohort == Cohort.UTSW.value
    assert stats.fit_split == "train"
    assert stats.patient_count == 2
    assert (
        stats.split_manifest_sha256 == hashlib.sha256(manifest.read_bytes()).hexdigest()
    )
    for modality in stats.modalities.values():
        assert math.isclose(modality.mean, POOLED_MEAN)
        assert math.isclose(modality.std, POOLED_STD)
        assert modality.voxel_count == 4


def test_fit_refuses_any_cohort_or_split_but_utsw_train(tmp_path: Path) -> None:
    manifest = _write_manifest(tmp_path, ["UTSW-BT0001", "UTSW-BT0002"])
    for cohort, split in (
        (Cohort.UCSF_PDGM, "train"),
        (Cohort.UTSW, "calibration"),
        (Cohort.UTSW, "internal_test"),
    ):
        with pytest.raises(ValueError, match="UTSW training split"):
            fit_normalization_stats(
                _moments(),
                cohort=cohort,
                split_name=split,
                split_manifest_path=manifest,
            )


def test_fit_refuses_patients_that_differ_from_the_frozen_train_roster(
    tmp_path: Path,
) -> None:
    manifest = _write_manifest(tmp_path, ["UTSW-BT0001", "UTSW-BT0002"])
    extra = dict(_moments())
    extra["UTSW-BT0900"] = extra["UTSW-BT0001"]  # a calibration patient
    missing = {"UTSW-BT0001": _moments()["UTSW-BT0001"]}
    for wrong in (extra, missing):
        with pytest.raises(ValueError, match="frozen UTSW training roster"):
            fit_normalization_stats(
                wrong,
                cohort=Cohort.UTSW,
                split_name="train",
                split_manifest_path=manifest,
            )


def test_fit_refuses_a_manifest_that_is_not_frozen(tmp_path: Path) -> None:
    unfrozen = _write_manifest(tmp_path, ["UTSW-BT0001", "UTSW-BT0002"], sidecar=False)
    with pytest.raises(ValueError, match="not frozen"):
        fit_normalization_stats(
            _moments(),
            cohort=Cohort.UTSW,
            split_name="train",
            split_manifest_path=unfrozen,
        )
    _write_manifest(tmp_path, ["UTSW-BT0001", "UTSW-BT0002"])
    unfrozen.write_text(unfrozen.read_text().replace("0900", "0902"))
    with pytest.raises(ValueError, match="frozen SHA-256"):
        fit_normalization_stats(
            _moments(),
            cohort=Cohort.UTSW,
            split_name="train",
            split_manifest_path=unfrozen,
        )


def test_normalize_volume_matches_hand_formula_and_keeps_background_zero(
    tmp_path: Path,
) -> None:
    stats = _fit(tmp_path)
    out = normalize_volume(VOLUME_A, "T1", stats)
    assert out.dtype == np.float32
    assert out[0] == 0 and out[3] == 0
    for index, raw in ((1, 2.0), (2, 4.0), (4, 6.0)):
        assert math.isclose(
            float(out[index]), (raw - POOLED_MEAN) / POOLED_STD, rel_tol=1e-6
        )


def test_normalize_volume_never_changes_the_input_array(tmp_path: Path) -> None:
    stats = _fit(tmp_path)
    volume = np.array([0, 2, 4, 0, 6], dtype=np.float32)
    snapshot = volume.copy()
    normalize_volume(volume, "T1", stats)
    assert np.array_equal(volume, snapshot)


def test_training_data_is_standardized_to_mean_zero_and_std_one(tmp_path: Path) -> None:
    stats = _fit(tmp_path)
    brain = np.concatenate(
        [
            normalize_volume(volume, "FLAIR", stats)[volume != 0]
            for volume in (VOLUME_A, VOLUME_B)
        ]
    ).astype(np.float64)
    assert math.isclose(brain.mean(), 0.0, abs_tol=1e-6)
    assert math.isclose(brain.std(), 1.0, rel_tol=1e-6)


def test_applying_to_a_held_out_volume_uses_train_statistics_and_recomputes_nothing(
    tmp_path: Path,
) -> None:
    stats = _fit(tmp_path)
    before = json.dumps(
        {name: vars(m) for name, m in stats.modalities.items()},
        sort_keys=True,
    )
    held_out = np.array([0, 1000, 2000, 0, 3000], dtype=np.float32)
    out = normalize_volume(held_out, "T2", stats)
    expected = (held_out[held_out != 0].astype(np.float64) - POOLED_MEAN) / POOLED_STD
    assert np.allclose(out[held_out != 0], expected, rtol=1e-5)
    after = json.dumps(
        {name: vars(m) for name, m in stats.modalities.items()},
        sort_keys=True,
    )
    assert before == after


def test_no_clipping_of_extreme_intensities(tmp_path: Path) -> None:
    stats = _fit(tmp_path)
    huge = np.array([0, 1.0e6], dtype=np.float32)
    out = normalize_volume(huge, "T1ce", stats)
    assert math.isclose(float(out[1]), (1.0e6 - POOLED_MEAN) / POOLED_STD, rel_tol=1e-5)


def test_stats_file_is_byte_deterministic_never_overwritten_and_hash_checked(
    tmp_path: Path,
) -> None:
    stats = _fit(tmp_path)
    first = write_normalization_stats(tmp_path / "one.json", stats)
    second = write_normalization_stats(tmp_path / "two.json", stats)
    assert first.read_bytes() == second.read_bytes()
    with pytest.raises(FileExistsError):
        write_normalization_stats(first, stats)
    digest = hashlib.sha256(first.read_bytes()).hexdigest()
    assert load_normalization_stats(first, expected_sha256=digest) == stats
    with pytest.raises(ValueError, match="SHA-256"):
        load_normalization_stats(first, expected_sha256="0" * 64)
    assert not list(tmp_path.glob(".*.tmp"))


def test_load_rejects_statistics_not_fitted_on_utsw_train(tmp_path: Path) -> None:
    stats = _fit(tmp_path)
    path = write_normalization_stats(tmp_path / "s.json", stats)
    document = json.loads(path.read_text())
    document["fit_cohort"] = Cohort.UCSF_PDGM.value
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="UTSW training split"):
        load_normalization_stats(path)


def test_cli_refuses_any_other_fitting_cohort_or_split() -> None:
    for argv in (["--cohort", "ucsf_pdgm"], ["--split", "calibration"]):
        with pytest.raises(SystemExit) as raised:
            script.main(argv)
        assert raised.value.code == 2

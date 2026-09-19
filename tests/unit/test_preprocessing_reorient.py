"""Synthetic tests for the Phase 04 common orientation and spacing stage."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from glioma_selective.preprocessing import reorient as reorient_module
from glioma_selective.preprocessing.cache import StageCache
from glioma_selective.preprocessing.reorient import (
    ReorientParameters,
    reorient_volume,
    run_reorient_stage,
)


def _lps_affine(spacing: float = 1.0) -> np.ndarray:
    affine = np.diag((-spacing, -spacing, spacing, 1.0))
    affine[:3, 3] = (10.0, 20.0, 30.0)
    return affine


def _image(
    data: np.ndarray, *, spacing: float = 1.0, lps: bool = True
) -> nib.Nifti1Image:
    affine = _lps_affine(spacing) if lps else np.diag((spacing,) * 3 + (1.0,))
    return nib.Nifti1Image(data, affine)


def test_parameters_validate_and_serialize() -> None:
    params = ReorientParameters()
    assert params.as_cache_params() == {
        "target_orientation": "RAS",
        "target_spacing": [1.0, 1.0, 1.0],
        "spacing_tolerance_mm": 1e-4,
        "is_mask": False,
    }
    with pytest.raises(ValueError, match="target_orientation"):
        ReorientParameters(target_orientation="LPS")
    with pytest.raises(ValueError, match="target_spacing"):
        ReorientParameters(target_spacing=(1.0, 1.0))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="target_spacing"):
        ReorientParameters(target_spacing=(1.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="spacing_tolerance"):
        ReorientParameters(spacing_tolerance_mm=-1.0)
    with pytest.raises(TypeError, match="is_mask"):
        ReorientParameters(is_mask=1)  # type: ignore[arg-type]


def test_observed_nibabel_lps_to_ras_behavior_is_pinned() -> None:
    data = np.arange(3 * 4 * 5, dtype=np.int16).reshape(3, 4, 5)
    affine = _lps_affine()
    image = nib.Nifti1Image(data, affine)
    image.set_qform(affine, code=2)
    image.set_sform(affine, code=3)

    canonical = nib.as_closest_canonical(image)

    assert canonical.shape == (3, 4, 5)
    assert nib.aff2axcodes(canonical.affine) == ("R", "A", "S")
    assert canonical.get_data_dtype() == np.dtype(np.int16)
    np.testing.assert_array_equal(np.asarray(canonical.dataobj), data[::-1, ::-1, :])
    assert canonical.header["qform_code"] == 0
    assert canonical.header["sform_code"] == 2
    np.testing.assert_allclose(canonical.get_qform(), canonical.affine)
    np.testing.assert_allclose(canonical.get_sform(), canonical.affine)
    assert np.isnan(canonical.header["scl_slope"])
    assert np.isnan(canonical.header["scl_inter"])


@pytest.mark.parametrize("dtype", [np.dtype(np.int16), np.dtype(np.float32)])
def test_lps_marker_is_losslessly_reoriented_and_dtype_preserved(
    dtype: np.dtype[np.generic],
) -> None:
    data = np.zeros((5, 6, 7), dtype=dtype)
    data[1, 4, 2] = dtype.type(17)
    source = _image(data)

    result = reorient_volume(source, ReorientParameters())

    assert result.resampled is False
    assert result.applied_axis_flips == (0, 1)
    assert nib.aff2axcodes(result.image.affine) == ("R", "A", "S")
    assert result.image.get_data_dtype() == dtype
    np.testing.assert_array_equal(np.asarray(result.image.dataobj), data[::-1, ::-1, :])


def test_already_ras_input_is_unchanged() -> None:
    data = np.arange(5 * 6 * 7, dtype=np.float32).reshape(5, 6, 7)
    affine = np.diag((1.0, 1.0, 1.0, 1.0))
    affine[:3, 3] = (-8.0, 4.0, 2.0)
    source = nib.Nifti1Image(data, affine)

    result = reorient_volume(source, ReorientParameters())

    assert result.resampled is False
    assert result.applied_axis_flips == ()
    np.testing.assert_array_equal(np.asarray(result.image.dataobj), data)
    np.testing.assert_array_equal(result.image.affine, affine)


def test_two_mm_image_is_resampled_once_to_target_spacing() -> None:
    source = _image(
        np.arange(5 * 6 * 7, dtype=np.float32).reshape(5, 6, 7),
        spacing=2.0,
        lps=False,
    )

    result = reorient_volume(source, ReorientParameters())

    assert result.resampled is True
    assert result.image.shape == (9, 11, 13)
    np.testing.assert_allclose(result.image.header.get_zooms()[:3], (1.0, 1.0, 1.0))
    np.testing.assert_allclose(
        (np.asarray(source.shape) - 1) * np.asarray(source.header.get_zooms()[:3]),
        (np.asarray(result.image.shape) - 1)
        * np.asarray(result.image.header.get_zooms()[:3]),
    )


def test_matching_spacing_is_not_resampled_and_is_exact() -> None:
    data = np.arange(5 * 6 * 7, dtype=np.int16).reshape(5, 6, 7)
    source = _image(data)

    result = reorient_volume(source, ReorientParameters())

    assert result.resampled is False
    np.testing.assert_array_equal(np.asarray(result.image.dataobj), data[::-1, ::-1, :])


@pytest.mark.parametrize("spacing", [1.0, 2.0])
def test_mask_labels_remain_integer_values_on_both_paths(spacing: float) -> None:
    data = np.zeros((5, 6, 7), dtype=np.int16)
    data[1:3, 2:4, 3:5] = 1
    data[3:5, 4:6, 1:3] = 4
    source = _image(data, spacing=spacing)

    result = reorient_volume(source, ReorientParameters(is_mask=True))

    assert result.image.get_data_dtype() == np.dtype(np.int16)
    assert set(np.unique(np.asarray(result.image.dataobj))) <= {0, 1, 4}
    if spacing == 1.0:
        np.testing.assert_array_equal(
            np.asarray(result.image.dataobj), data[::-1, ::-1, :]
        )


def test_cached_stage_reuses_and_recomputes_on_parameter_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.nii.gz"
    nib.save(_image(np.ones((5, 6, 7), dtype=np.float32)), input_path)
    cache = StageCache(tmp_path / "cache")
    calls = 0
    original = reorient_module.reorient_volume

    def counted(
        image: nib.Nifti1Image, params: ReorientParameters
    ) -> reorient_module.ReorientResult:
        nonlocal calls
        calls += 1
        return original(image, params)

    monkeypatch.setattr(reorient_module, "reorient_volume", counted)
    first = run_reorient_stage(cache, input_path, ReorientParameters())
    second = run_reorient_stage(cache, input_path, ReorientParameters())
    changed = run_reorient_stage(
        cache,
        input_path,
        ReorientParameters(spacing_tolerance_mm=1e-3),
    )

    assert first == second
    assert changed != first
    assert calls == 2
    assert (first / "volume.nii.gz").is_file()


def test_non_three_dimensional_input_is_rejected() -> None:
    source = nib.Nifti1Image(np.zeros((4, 5, 6, 1), dtype=np.float32), np.eye(4))

    with pytest.raises(ValueError, match="three-dimensional"):
        reorient_volume(source, ReorientParameters())

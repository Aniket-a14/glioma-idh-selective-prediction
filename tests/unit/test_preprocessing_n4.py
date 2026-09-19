"""Synthetic unit coverage for the Phase 04 N4 stage."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
import SimpleITK as sitk

from glioma_selective.preprocessing.cache import StageCache
from glioma_selective.preprocessing.n4 import (
    N4Parameters,
    correct_bias,
    correct_bias_nifti,
    run_n4_stage,
)
from glioma_selective.preprocessing.resample import nifti_to_sitk, sitk_to_nifti


def _bias_phantom() -> tuple[sitk.Image, np.ndarray, np.ndarray]:
    shape = (32, 32, 32)
    z, y, x = np.indices(shape)
    tissue_a = (x >= 5) & (x < 16) & (y >= 5) & (y < 27) & (z >= 5) & (z < 27)
    tissue_b = (x >= 16) & (x < 27) & (y >= 5) & (y < 27) & (z >= 5) & (z < 27)
    phantom = np.zeros(shape, dtype=np.float32)
    phantom[tissue_a] = 100.0
    phantom[tissue_b] = 200.0
    bias = 0.65 + 0.7 * x / (shape[2] - 1)
    image = sitk.GetImageFromArray(phantom * bias)
    return image, tissue_a, tissue_b


def _small_params() -> N4Parameters:
    return N4Parameters(
        shrink_factor=2,
        max_iterations=(10, 10, 10),
        histogram_bins=50,
    )


def test_n4_parameters_validate_and_serialize() -> None:
    params = N4Parameters()
    assert params.shrink_factor == 4
    assert params.max_iterations == (50, 50, 50)
    assert params.as_cache_params() == {
        "shrink_factor": 4,
        "max_iterations": [50, 50, 50],
        "convergence_threshold": 1e-3,
        "histogram_bins": 200,
    }
    with pytest.raises(ValueError, match="shrink_factor"):
        N4Parameters(shrink_factor=0)
    with pytest.raises(ValueError, match="max_iterations"):
        N4Parameters(max_iterations=(1, 2))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="convergence_threshold"):
        N4Parameters(convergence_threshold=0)
    with pytest.raises(ValueError, match="histogram_bins"):
        N4Parameters(histogram_bins=1)


def test_bias_correction_reduces_within_tissue_cv_and_keeps_background_zero() -> None:
    image, tissue_a, tissue_b = _bias_phantom()
    before = sitk.GetArrayFromImage(image)
    corrected = correct_bias(image, params=_small_params(), n_threads=2)
    after = sitk.GetArrayFromImage(corrected)

    before_cv = [
        float(np.std(before[tissue]) / np.mean(before[tissue]))
        for tissue in (tissue_a, tissue_b)
    ]
    after_cv = [
        float(np.std(after[tissue]) / np.mean(after[tissue]))
        for tissue in (tissue_a, tissue_b)
    ]
    assert before_cv == pytest.approx([0.0815, 0.0635], abs=0.005)
    assert after_cv == pytest.approx([0.0044, 0.0057], abs=0.003)
    assert all(
        after < before for before, after in zip(before_cv, after_cv, strict=True)
    )
    assert np.all(after[~(tissue_a | tissue_b)] == 0.0)
    assert corrected.GetPixelID() == sitk.sitkFloat32
    assert corrected.GetSize() == image.GetSize()
    assert corrected.GetSpacing() == image.GetSpacing()


def test_bias_correction_allows_negative_masked_intensity() -> None:
    values = np.zeros((16, 16, 16), dtype=np.float32)
    values[2:14, 2:14, 2:14] = 2.0
    negative_indices = ((5, 5, 5), (6, 6, 6), (7, 7, 7))
    negative_values = (-1.0, -2.0, -0.5)
    for index, value in zip(negative_indices, negative_values, strict=True):
        values[index] = value
    image = sitk.GetImageFromArray(values)
    params = N4Parameters(shrink_factor=2, max_iterations=(1, 1, 1), histogram_bins=32)

    corrected = correct_bias(image, params=params, n_threads=1)
    result = sitk.GetArrayFromImage(corrected)

    assert corrected.GetPixelID() == sitk.sitkFloat32
    assert np.all(np.isfinite(result))
    assert np.all(result[values == 0] == 0.0)
    assert np.all(np.signbit(result[values < 0]))

    full_image = sitk.Cast(image, sitk.sitkFloat32)
    full_mask = sitk.Cast(full_image != 0, sitk.sitkUInt8)
    shrunk_image = sitk.Shrink(full_image, [2, 2, 2])
    estimation_mask = sitk.Cast(full_mask & (full_image > 0), sitk.sitkUInt8)
    shrunk_estimation_mask = sitk.Shrink(estimation_mask, [2, 2, 2])
    reference_filter = sitk.N4BiasFieldCorrectionImageFilter()
    reference_filter.SetMaximumNumberOfIterations(params.max_iterations)
    reference_filter.SetConvergenceThreshold(params.convergence_threshold)
    reference_filter.SetNumberOfHistogramBins(params.histogram_bins)
    reference_filter.SetNumberOfWorkUnits(1)
    reference_filter.Execute(shrunk_image, shrunk_estimation_mask)
    log_field = sitk.GetArrayFromImage(
        reference_filter.GetLogBiasFieldAsImage(full_image)
    )
    expected_negative = values[values < 0] / np.exp(log_field[values < 0])
    np.testing.assert_allclose(
        result[values < 0], expected_negative, rtol=1e-5, atol=1e-6
    )


def test_bias_correction_rejects_image_with_no_positive_estimation_voxel() -> None:
    image = sitk.GetImageFromArray(-np.ones((16, 16, 16), dtype=np.float32))
    with pytest.raises(ValueError, match="mask contains no positive voxel"):
        correct_bias(
            image,
            params=N4Parameters(
                shrink_factor=2, max_iterations=(1, 1, 1), histogram_bins=32
            ),
        )


def test_bias_correction_rejects_empty_mask() -> None:
    image = sitk.GetImageFromArray(np.zeros((16, 16, 16), dtype=np.float32))
    with pytest.raises(
        ValueError, match="mask must contain at least one non-zero voxel"
    ):
        correct_bias(
            image,
            params=N4Parameters(
                shrink_factor=2, max_iterations=(1, 1, 1), histogram_bins=32
            ),
        )


def test_bias_correction_rejects_non_finite_image() -> None:
    values = np.ones((16, 16, 16), dtype=np.float32)
    values[5, 5, 5] = np.nan
    with pytest.raises(ValueError, match="image contains non-finite voxels"):
        correct_bias(
            sitk.GetImageFromArray(values),
            params=N4Parameters(
                shrink_factor=2, max_iterations=(1, 1, 1), histogram_bins=32
            ),
        )


def test_bias_correction_positive_volume_is_bit_identical_to_previous_path() -> None:
    image, _, _ = _bias_phantom()
    params = _small_params()

    corrected = correct_bias(image, params=params, n_threads=1)

    full_image = sitk.Cast(image, sitk.sitkFloat32)
    full_mask = sitk.Cast(full_image != 0, sitk.sitkUInt8)
    shrink_factors = [params.shrink_factor] * 3
    shrunk_image = sitk.Shrink(full_image, shrink_factors)
    shrunk_mask = sitk.Shrink(full_mask, shrink_factors)
    reference_filter = sitk.N4BiasFieldCorrectionImageFilter()
    reference_filter.SetMaximumNumberOfIterations(params.max_iterations)
    reference_filter.SetConvergenceThreshold(params.convergence_threshold)
    reference_filter.SetNumberOfHistogramBins(params.histogram_bins)
    reference_filter.SetNumberOfWorkUnits(1)
    reference_filter.Execute(shrunk_image, shrunk_mask)
    reference_field = reference_filter.GetLogBiasFieldAsImage(full_image)
    reference = sitk.Mask(
        full_image / sitk.Exp(reference_field), full_mask, outsideValue=0.0
    )
    reference = sitk.Cast(reference, sitk.sitkFloat32)

    assert np.array_equal(
        sitk.GetArrayFromImage(corrected), sitk.GetArrayFromImage(reference)
    )


def test_bias_correction_is_deterministic() -> None:
    image, _, _ = _bias_phantom()
    params = _small_params()
    first = sitk.GetArrayFromImage(correct_bias(image, params=params, n_threads=2))
    second = sitk.GetArrayFromImage(correct_bias(image, params=params, n_threads=2))
    assert np.array_equal(first, second)


def test_nifti_round_trip_preserves_affine_and_voxel_order_exactly() -> None:
    array = np.arange(4 * 5 * 6, dtype=np.float32).reshape(4, 5, 6)
    affine = np.array(
        [
            [-1.2, 0.0, 0.0, 10.0],
            [0.0, 2.5, 0.0, -7.0],
            [0.0, 0.0, 0.8, 3.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    image = nib.Nifti1Image(array, affine)
    round_trip = sitk_to_nifti(nifti_to_sitk(image))
    assert np.array_equal(np.asarray(round_trip.dataobj), array)
    assert np.array_equal(round_trip.affine, affine)


def test_correct_bias_nifti_preserves_grid_and_returns_float32() -> None:
    array = np.ones((16, 16, 16), dtype=np.float32)
    array[:8] = 2.0
    affine = np.diag([-1.0, -1.5, 2.0, 1.0])
    image = nib.Nifti1Image(array, affine)
    corrected = correct_bias_nifti(
        image,
        N4Parameters(max_iterations=(2, 2, 2), histogram_bins=32),
        n_threads=2,
    )
    assert corrected.shape == image.shape
    assert np.array_equal(corrected.affine, image.affine)
    assert corrected.get_data_dtype() == np.dtype(np.float32)


def test_run_n4_stage_reuses_and_recomputes_cache(tmp_path: Path) -> None:
    input_path = tmp_path / "input.nii.gz"
    nib.save(
        nib.Nifti1Image(np.ones((16, 16, 16), dtype=np.float32), np.eye(4)), input_path
    )
    cache = StageCache(tmp_path / "cache")
    params = N4Parameters(max_iterations=(1, 1, 1), histogram_bins=32)

    first = run_n4_stage(cache, input_path, params, n_threads=2)
    second = run_n4_stage(cache, input_path, params, n_threads=2)
    assert first == second
    assert (first / "volume.nii.gz").is_file()

    changed_params = N4Parameters(max_iterations=(2, 1, 1), histogram_bins=32)
    changed = run_n4_stage(cache, input_path, changed_params, n_threads=2)
    assert changed != first

    changed_input = np.zeros((16, 16, 16), dtype=np.float32)
    changed_input[2:-2, 2:-2, 2:-2] = 1.0
    nib.save(nib.Nifti1Image(changed_input, np.eye(4)), input_path)
    changed_input_result = run_n4_stage(cache, input_path, params, n_threads=2)
    assert changed_input_result != first


def test_n_threads_must_be_positive() -> None:
    image = sitk.GetImageFromArray(np.ones((16, 16, 16), dtype=np.float32))
    with pytest.raises(ValueError, match="n_threads"):
        correct_bias(image, params=N4Parameters(max_iterations=(1, 1, 1)), n_threads=0)

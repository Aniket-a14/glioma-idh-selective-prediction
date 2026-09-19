"""Unit tests for lossless orientation conversion and spacing resampling."""

from __future__ import annotations

import nibabel as nib
import numpy as np
import SimpleITK as sitk

from glioma_selective.preprocessing.resample import (
    nifti_to_sitk,
    reorient_to_ras,
    resample_to_spacing,
    sitk_to_nifti,
)


def test_reorient_to_ras_moves_asymmetric_marker_without_interpolation() -> None:
    data = np.zeros((3, 4, 5), dtype=np.float32)
    data[0, 1, 2] = 7.0
    affine = np.array(
        [
            [0.0, 3.0, 0.0, 10.0],
            [-2.0, 0.0, 0.0, 20.0],
            [0.0, 0.0, 4.0, 30.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )

    result = reorient_to_ras(nib.Nifti1Image(data, affine))

    assert nib.aff2axcodes(result.affine) == ("R", "A", "S")
    assert result.shape == (4, 3, 5)
    assert np.array_equal(np.argwhere(np.asarray(result.dataobj) == 7.0), [[1, 2, 2]])
    assert np.array_equal(np.unique(np.asarray(result.dataobj)), [0.0, 7.0])


def test_nifti_sitk_round_trip_preserves_data_and_affine() -> None:
    data = np.arange(4 * 5 * 6, dtype=np.int16).reshape((4, 5, 6))
    affine = np.array(
        [
            [0.0, 0.0, -2.0, 11.0],
            [1.5, 0.0, 0.0, -9.0],
            [0.0, 3.0, 0.0, 4.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    source = nib.Nifti1Image(data, affine)

    round_trip = sitk_to_nifti(nifti_to_sitk(source))

    np.testing.assert_array_equal(np.asarray(round_trip.dataobj), data)
    np.testing.assert_allclose(round_trip.affine, affine, atol=1e-6)


def test_resample_passes_through_matching_spacing_exactly() -> None:
    source = sitk.GetImageFromArray(
        np.arange(4 * 5 * 6, dtype=np.float32).reshape(6, 5, 4)
    )
    source.SetSpacing((1.00005, 0.99995, 1.0))

    result = resample_to_spacing(source, (1.0, 1.0, 1.0))

    assert result is source
    np.testing.assert_array_equal(
        sitk.GetArrayFromImage(result), sitk.GetArrayFromImage(source)
    )


def test_resample_preserves_extent_origin_direction_and_uses_linear_interpolation() -> (
    None
):
    values = np.zeros((4, 4, 4), dtype=np.float32)
    values[1, 1, 1] = 1.0
    source = sitk.GetImageFromArray(values)
    source.SetSpacing((2.0, 2.0, 2.0))
    source.SetOrigin((4.0, -3.0, 2.0))
    direction = (0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    source.SetDirection(direction)

    result = resample_to_spacing(source, (1.0, 1.0, 1.0))

    assert result.GetSize() == (7, 7, 7)
    np.testing.assert_allclose(result.GetOrigin(), source.GetOrigin())
    np.testing.assert_allclose(result.GetDirection(), direction)
    resampled = sitk.GetArrayFromImage(result)
    assert np.any((resampled > 0.0) & (resampled < 1.0))


def test_resample_mask_uses_nearest_neighbour() -> None:
    values = np.zeros((3, 3, 3), dtype=np.uint8)
    values[1, 1, 1] = 2
    source = sitk.GetImageFromArray(values)
    source.SetSpacing((2.0, 2.0, 2.0))

    result = resample_to_spacing(source, (1.0, 1.0, 1.0), is_mask=True)

    assert set(np.unique(sitk.GetArrayFromImage(result))) <= {0, 2}

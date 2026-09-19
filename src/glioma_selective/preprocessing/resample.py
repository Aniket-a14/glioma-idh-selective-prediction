"""Orientation conversion and spacing resampling for preprocessing volumes."""

from __future__ import annotations

from typing import Final

import nibabel as nib
import numpy as np
import SimpleITK as sitk

_RAS_TO_LPS: Final[np.ndarray] = np.diag([-1.0, -1.0, 1.0])
_SPACING_TOLERANCE_MM: Final[float] = 1e-4


def reorient_to_ras(nifti: nib.Nifti1Image) -> nib.Nifti1Image:
    """Return ``nifti`` in RAS orientation using only axis flips/permutations.

    ``nibabel``'s canonicalization changes voxel order and affine metadata but
    does not interpolate intensities.  The returned image is asserted to have
    RAS axis codes before it is returned.
    """

    canonical = nib.as_closest_canonical(nifti)
    if not isinstance(canonical, nib.Nifti1Image):
        raise TypeError("canonicalization did not return a NIfTI-1 image")
    if nib.aff2axcodes(canonical.affine) != ("R", "A", "S"):
        raise AssertionError("canonical NIfTI image is not RAS oriented")
    return canonical


def nifti_to_sitk(nifti: nib.Nifti1Image) -> sitk.Image:
    """Convert a three-dimensional RAS NIfTI image to a SimpleITK LPS image.

    NIfTI stores array axes as ``x, y, z`` while SimpleITK's NumPy bridge
    expects ``z, y, x``.  The affine is converted from RAS to LPS explicitly;
    sheared affines are rejected because SimpleITK represents geometry with
    orthonormal direction cosines, spacing, and origin.
    """

    if len(nifti.shape) != 3:
        raise ValueError("only three-dimensional NIfTI images are supported")
    affine = np.asarray(nifti.affine, dtype=np.float64)
    linear_lps = _RAS_TO_LPS @ affine[:3, :3]
    spacing = np.linalg.norm(linear_lps, axis=0)
    if np.any(spacing <= 0):
        raise ValueError("NIfTI affine has a zero-length spatial axis")
    direction = linear_lps / spacing
    if not np.allclose(direction.T @ direction, np.eye(3), atol=1e-5):
        raise ValueError("NIfTI affine contains shear, unsupported by SimpleITK")

    array_xyz = np.asarray(nifti.dataobj)
    image = sitk.GetImageFromArray(np.ascontiguousarray(array_xyz.transpose(2, 1, 0)))
    image.SetSpacing(tuple(float(value) for value in spacing))
    image.SetDirection(tuple(float(value) for value in direction.reshape(-1)))
    image.SetOrigin(tuple(float(value) for value in (_RAS_TO_LPS @ affine[:3, 3])))
    return image


def sitk_to_nifti(image: sitk.Image) -> nib.Nifti1Image:
    """Convert a three-dimensional SimpleITK LPS image to a RAS NIfTI image."""

    if image.GetDimension() != 3:
        raise ValueError("only three-dimensional SimpleITK images are supported")
    array_zyx = sitk.GetArrayFromImage(image)
    array_xyz = np.ascontiguousarray(array_zyx.transpose(2, 1, 0))
    direction = np.asarray(image.GetDirection(), dtype=np.float64).reshape(3, 3)
    affine_lps = np.eye(4, dtype=np.float64)
    affine_lps[:3, :3] = direction @ np.diag(image.GetSpacing())
    affine_lps[:3, 3] = image.GetOrigin()
    affine_ras = np.eye(4, dtype=np.float64)
    affine_ras[:3] = _RAS_TO_LPS @ affine_lps[:3]
    return nib.Nifti1Image(array_xyz, affine_ras)


def resample_to_spacing(
    image: sitk.Image,
    spacing: tuple[float, float, float] = (1.0, 1.0, 1.0),
    *,
    is_mask: bool = False,
) -> sitk.Image:
    """Resample ``image`` to ``spacing`` while preserving its physical extent.

    Intensity images use linear interpolation and masks use nearest-neighbour
    interpolation.  Origin and direction are copied unchanged.  Images
    already within ``1e-4`` mm of the requested spacing are returned directly,
    so this pass-through cannot alter voxel values.
    """

    if image.GetDimension() != 3:
        raise ValueError("only three-dimensional SimpleITK images are supported")
    if len(spacing) != 3 or any(float(value) <= 0 for value in spacing):
        raise ValueError("target spacing must contain three positive values")

    target_spacing = tuple(float(value) for value in spacing)
    input_spacing = tuple(float(value) for value in image.GetSpacing())
    if all(
        abs(current - target) <= _SPACING_TOLERANCE_MM
        for current, target in zip(input_spacing, target_spacing, strict=True)
    ):
        return image

    input_size = image.GetSize()
    output_size = tuple(
        max(
            1,
            int(
                round(
                    (input_size[index] - 1)
                    * input_spacing[index]
                    / target_spacing[index]
                )
            )
            + 1,
        )
        for index in range(3)
    )
    interpolator = sitk.sitkNearestNeighbor if is_mask else sitk.sitkLinear
    return sitk.Resample(
        image,
        output_size,
        sitk.Transform(),
        interpolator,
        image.GetOrigin(),
        target_spacing,
        image.GetDirection(),
        0.0,
        image.GetPixelID(),
    )

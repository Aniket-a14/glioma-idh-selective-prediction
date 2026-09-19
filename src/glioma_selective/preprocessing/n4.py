"""N4 bias-field correction for full-resolution preprocessing volumes."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import nibabel as nib
import numpy as np
import SimpleITK as sitk

from glioma_selective.preprocessing.cache import (
    StageCache,
    hash_file,
    stage_cache_key,
)
from glioma_selective.preprocessing.resample import nifti_to_sitk, sitk_to_nifti

__all__ = [
    "N4Parameters",
    "correct_bias",
    "correct_bias_nifti",
    "run_n4_stage",
]

_STAGE_NAME: Final[str] = "n4"
_STAGE_VERSION: Final[str] = "1"


@dataclass(frozen=True)
class N4Parameters:
    """Validated parameters for one N4 correction invocation."""

    shrink_factor: int = 4
    max_iterations: tuple[int, int, int] = (50, 50, 50)
    convergence_threshold: float = 1e-3
    histogram_bins: int = 200

    def __post_init__(self) -> None:
        if isinstance(self.shrink_factor, bool) or not isinstance(
            self.shrink_factor, int
        ):
            raise TypeError("shrink_factor must be an integer")
        if self.shrink_factor < 1:
            raise ValueError("shrink_factor must be at least 1")

        if not isinstance(self.max_iterations, tuple) or len(self.max_iterations) != 3:
            raise ValueError("max_iterations must contain exactly three integers")
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in self.max_iterations
        ):
            raise ValueError("max_iterations values must be positive integers")

        if not isinstance(self.convergence_threshold, int | float) or isinstance(
            self.convergence_threshold, bool
        ):
            raise TypeError("convergence_threshold must be a real number")
        if not math.isfinite(float(self.convergence_threshold)) or (
            self.convergence_threshold <= 0
        ):
            raise ValueError("convergence_threshold must be finite and positive")

        if isinstance(self.histogram_bins, bool) or not isinstance(
            self.histogram_bins, int
        ):
            raise TypeError("histogram_bins must be an integer")
        if self.histogram_bins < 2:
            raise ValueError("histogram_bins must be at least 2")

    def as_cache_params(self) -> dict[str, object]:
        """Return JSON-compatible parameters for content-addressed caching."""

        return {
            "shrink_factor": self.shrink_factor,
            "max_iterations": list(self.max_iterations),
            "convergence_threshold": float(self.convergence_threshold),
            "histogram_bins": self.histogram_bins,
        }


_DEFAULT_N4_PARAMETERS: Final = N4Parameters()


def _validate_threads(n_threads: int) -> None:
    if isinstance(n_threads, bool) or not isinstance(n_threads, int):
        raise TypeError("n_threads must be an integer")
    if n_threads < 1:
        raise ValueError("n_threads must be at least 1")


def _validate_image(image: sitk.Image, name: str) -> None:
    if not isinstance(image, sitk.Image):
        raise TypeError(f"{name} must be a SimpleITK image")
    if image.GetDimension() != 3:
        raise ValueError(f"{name} must be three-dimensional")
    if image.GetNumberOfComponentsPerPixel() != 1:
        raise ValueError(f"{name} must be a scalar image")


def _validate_mask_geometry(image: sitk.Image, mask: sitk.Image) -> None:
    if image.GetSize() != mask.GetSize():
        raise ValueError("mask must have the same size as image")
    if not np.allclose(image.GetSpacing(), mask.GetSpacing(), atol=1e-6):
        raise ValueError("mask must have the same spacing as image")
    if not np.allclose(image.GetOrigin(), mask.GetOrigin(), atol=1e-6):
        raise ValueError("mask must have the same origin as image")
    if not np.allclose(image.GetDirection(), mask.GetDirection(), atol=1e-6):
        raise ValueError("mask must have the same direction as image")


def _require_image(value: object, operation: str) -> sitk.Image:
    if not isinstance(value, sitk.Image):
        raise TypeError(f"SimpleITK {operation} did not return an image")
    return value


def _binary_mask(image: sitk.Image, mask: sitk.Image | None) -> sitk.Image:
    if mask is None:
        return _require_image(sitk.Cast(image != 0, sitk.sitkUInt8), "Cast")
    _validate_image(mask, "mask")
    _validate_mask_geometry(image, mask)
    return _require_image(sitk.Cast(mask != 0, sitk.sitkUInt8), "Cast")


def correct_bias(
    image: sitk.Image,
    mask: sitk.Image | None = None,
    params: N4Parameters = _DEFAULT_N4_PARAMETERS,
    *,
    n_threads: int = 2,
) -> sitk.Image:
    """Correct a scalar 3-D image while retaining its full-resolution grid.

    N4 estimates the spline field from a shrunk image and an estimation mask
    containing only strictly positive voxels inside the supplied or implicit
    non-zero mask.  The estimated log field is then evaluated on the original
    image grid and divided out across the whole non-zero mask, so negative
    voxels retain their sign.  The output is float32 and is exactly zero
    outside the supplied or implicit non-zero mask.
    """

    _validate_image(image, "image")
    _validate_threads(n_threads)
    if not isinstance(params, N4Parameters):
        raise TypeError("params must be an N4Parameters instance")

    full_image = sitk.Cast(image, sitk.sitkFloat32)
    binary_mask = _binary_mask(full_image, mask)
    mask_array = sitk.GetArrayViewFromImage(binary_mask) != 0
    if not np.any(mask_array):
        raise ValueError("mask must contain at least one non-zero voxel")
    image_array = sitk.GetArrayViewFromImage(full_image)
    if not np.all(np.isfinite(image_array)):
        raise ValueError("image contains non-finite voxels")
    estimation_mask = sitk.Cast(binary_mask & (full_image > 0), sitk.sitkUInt8)
    estimation_mask_array = sitk.GetArrayViewFromImage(estimation_mask) != 0
    if not np.any(estimation_mask_array):
        raise ValueError("mask contains no positive voxel")

    if any(size < params.shrink_factor for size in full_image.GetSize()):
        raise ValueError("image dimensions must be at least shrink_factor")
    shrink_factors = [params.shrink_factor] * 3
    shrunk_image = sitk.Shrink(full_image, shrink_factors)
    shrunk_mask = sitk.Shrink(estimation_mask, shrink_factors)

    correction = sitk.N4BiasFieldCorrectionImageFilter()
    correction.SetMaximumNumberOfIterations(params.max_iterations)
    correction.SetConvergenceThreshold(float(params.convergence_threshold))
    correction.SetNumberOfHistogramBins(params.histogram_bins)
    correction.SetNumberOfWorkUnits(n_threads)
    correction.Execute(shrunk_image, shrunk_mask)

    log_bias_field = correction.GetLogBiasFieldAsImage(full_image)
    corrected = full_image / sitk.Exp(log_bias_field)
    corrected = _require_image(
        sitk.Mask(corrected, binary_mask, outsideValue=0.0), "Mask"
    )
    return _require_image(sitk.Cast(corrected, sitk.sitkFloat32), "Cast")


def correct_bias_nifti(
    nifti: nib.Nifti1Image,
    params: N4Parameters,
    *,
    n_threads: int = 2,
) -> nib.Nifti1Image:
    """Correct a NIfTI image through the repository's RAS/LPS bridge."""

    if not isinstance(nifti, nib.Nifti1Image):
        raise TypeError("nifti must be a NIfTI-1 image")
    return sitk_to_nifti(
        correct_bias(nifti_to_sitk(nifti), params=params, n_threads=n_threads)
    )


def run_n4_stage(
    cache: StageCache,
    input_path: Path,
    params: N4Parameters,
    *,
    n_threads: int = 2,
) -> Path:
    """Run or reuse one cached N4 correction and return its output directory."""

    if not isinstance(cache, StageCache):
        raise TypeError("cache must be a StageCache instance")
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not isinstance(params, N4Parameters):
        raise TypeError("params must be an N4Parameters instance")
    _validate_threads(n_threads)

    input_key = hash_file(input_path)
    cache_params = params.as_cache_params()
    key = stage_cache_key(_STAGE_NAME, _STAGE_VERSION, cache_params, [input_key])

    def compute(output_dir: Path) -> None:
        source = nib.load(input_path)
        if not isinstance(source, nib.Nifti1Image):
            raise TypeError("N4 stage inputs must be NIfTI-1 images")
        corrected = correct_bias_nifti(source, params, n_threads=n_threads)
        output_dir.mkdir(parents=True, exist_ok=True)
        nib.save(corrected, output_dir / "volume.nii.gz")

    return cache.get_or_compute(
        _STAGE_NAME,
        key,
        compute,
        stage_version=_STAGE_VERSION,
        params=cache_params,
        input_keys=[input_key],
    )

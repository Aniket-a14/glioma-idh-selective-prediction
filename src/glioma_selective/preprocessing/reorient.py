"""Cached common-orientation and target-spacing preprocessing stage."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import nibabel as nib
import numpy as np

from glioma_selective.preprocessing.cache import (
    StageCache,
    hash_file,
    stage_cache_key,
)
from glioma_selective.preprocessing.resample import (
    nifti_to_sitk,
    reorient_to_ras,
    resample_to_spacing,
    sitk_to_nifti,
)

_STAGE_NAME = "reorient"
_STAGE_VERSION = "1"


@dataclass(frozen=True)
class ReorientParameters:
    """Validated parameters for the common RAS and spacing stage."""

    target_orientation: str = "RAS"
    target_spacing: tuple[float, float, float] = (1.0, 1.0, 1.0)
    spacing_tolerance_mm: float = 1e-4
    is_mask: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.target_orientation, str):
            raise TypeError("target_orientation must be a string")
        if self.target_orientation != "RAS":
            raise ValueError("only target_orientation='RAS' is supported")

        if not isinstance(self.target_spacing, tuple) or len(self.target_spacing) != 3:
            raise ValueError("target_spacing must contain exactly three values")
        if any(
            isinstance(value, bool)
            or not isinstance(value, int | float)
            or not math.isfinite(float(value))
            or float(value) <= 0
            for value in self.target_spacing
        ):
            raise ValueError("target_spacing values must be finite and positive")

        if isinstance(self.spacing_tolerance_mm, bool) or not isinstance(
            self.spacing_tolerance_mm, int | float
        ):
            raise TypeError("spacing_tolerance_mm must be a real number")
        if not math.isfinite(float(self.spacing_tolerance_mm)) or (
            self.spacing_tolerance_mm < 0
        ):
            raise ValueError("spacing_tolerance_mm must be finite and non-negative")

        if not isinstance(self.is_mask, bool):
            raise TypeError("is_mask must be a boolean")

    def as_cache_params(self) -> dict[str, object]:
        """Return JSON-compatible parameters for content-addressed caching."""

        return {
            "target_orientation": self.target_orientation,
            "target_spacing": [float(value) for value in self.target_spacing],
            "spacing_tolerance_mm": float(self.spacing_tolerance_mm),
            "is_mask": self.is_mask,
        }


@dataclass(frozen=True)
class ReorientResult:
    """Result of one orientation and spacing invocation.

    ``applied_axis_flips`` contains source voxel-axis indices whose direction
    was reversed while transforming the input orientation to RAS.  A
    permutation without a reversal does not add an entry.
    """

    image: nib.Nifti1Image
    resampled: bool
    applied_axis_flips: tuple[int, ...]


def _validate_nifti(nifti: nib.Nifti1Image) -> None:
    if not isinstance(nifti, nib.Nifti1Image):
        raise TypeError("nifti must be a NIfTI-1 image")
    if len(nifti.shape) != 3:
        raise ValueError("nifti must be a three-dimensional NIfTI image")


def _header_spacing(nifti: nib.Nifti1Image) -> tuple[float, float, float]:
    zooms = nifti.header.get_zooms()
    if len(zooms) < 3:
        raise ValueError("nifti header must contain three spatial spacings")
    spacing = (float(zooms[0]), float(zooms[1]), float(zooms[2]))
    if any(not math.isfinite(value) or value <= 0 for value in spacing):
        raise ValueError("nifti header spacing must be finite and positive")
    return spacing


def _spacing_matches(
    spacing: tuple[float, float, float], params: ReorientParameters
) -> bool:
    return all(
        abs(current - target) <= params.spacing_tolerance_mm
        for current, target in zip(spacing, params.target_spacing, strict=True)
    )


def _axis_flips_to_ras(
    input_image: nib.Nifti1Image, output_image: nib.Nifti1Image
) -> tuple[int, ...]:
    input_orientation = nib.orientations.io_orientation(input_image.affine)
    output_orientation = nib.orientations.io_orientation(output_image.affine)
    transform = nib.orientations.ornt_transform(input_orientation, output_orientation)
    return tuple(
        int(source_axis) for source_axis, direction in transform if direction < 0
    )


def _assert_no_resample_value_preservation(
    input_image: nib.Nifti1Image, output_image: nib.Nifti1Image
) -> None:
    input_array = np.asarray(input_image.dataobj)
    output_array = np.asarray(output_image.dataobj)
    input_orientation = nib.orientations.io_orientation(input_image.affine)
    output_orientation = nib.orientations.io_orientation(output_image.affine)
    transform = nib.orientations.ornt_transform(input_orientation, output_orientation)
    expected = nib.orientations.apply_orientation(input_array, transform)
    if not np.array_equal(output_array, expected):
        raise AssertionError(
            "no-resample RAS output is not an exact input axis permutation/flip"
        )


def reorient_volume(
    nifti: nib.Nifti1Image, params: ReorientParameters
) -> ReorientResult:
    """Orient a three-dimensional volume to RAS and, only when needed, resample.

    Spacing is checked from the NIfTI header before any conversion.  Matching
    spacing therefore takes the lossless canonicalization path; non-matching
    spacing uses linear interpolation for intensity images and nearest-neighbour
    interpolation for masks.
    """

    _validate_nifti(nifti)
    if not isinstance(params, ReorientParameters):
        raise TypeError("params must be a ReorientParameters instance")

    input_dtype = np.dtype(nifti.get_data_dtype())
    spacing = _header_spacing(nifti)
    resampled = not _spacing_matches(spacing, params)
    working = nifti
    if resampled:
        sitk_image = nifti_to_sitk(nifti)
        working = sitk_to_nifti(
            resample_to_spacing(
                sitk_image,
                params.target_spacing,
                is_mask=params.is_mask,
            )
        )

    output = reorient_to_ras(working)
    if nib.aff2axcodes(output.affine) != ("R", "A", "S"):
        raise AssertionError("reorient output is not RAS oriented")
    if np.dtype(output.get_data_dtype()) != input_dtype:
        raise AssertionError(
            "reorient output changed the input dtype: "
            f"{input_dtype} -> {output.get_data_dtype()}"
        )
    if not resampled:
        _assert_no_resample_value_preservation(nifti, output)

    return ReorientResult(
        image=output,
        resampled=resampled,
        applied_axis_flips=_axis_flips_to_ras(nifti, output),
    )


def run_reorient_stage(
    cache: StageCache, input_path: Path, params: ReorientParameters
) -> Path:
    """Run or reuse one cached reorientation/spacing stage."""

    if not isinstance(cache, StageCache):
        raise TypeError("cache must be a StageCache instance")
    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not isinstance(params, ReorientParameters):
        raise TypeError("params must be a ReorientParameters instance")

    input_key = hash_file(input_path)
    cache_params = params.as_cache_params()
    key = stage_cache_key(_STAGE_NAME, _STAGE_VERSION, cache_params, [input_key])

    def compute(output_dir: Path) -> None:
        source = nib.load(input_path)
        if not isinstance(source, nib.Nifti1Image):
            raise TypeError("reorient stage inputs must be NIfTI-1 images")
        result = reorient_volume(source, params)
        output_dir.mkdir(parents=True, exist_ok=True)
        nib.save(result.image, output_dir / "volume.nii.gz")

    return cache.get_or_compute(
        _STAGE_NAME,
        key,
        compute,
        stage_version=_STAGE_VERSION,
        params=cache_params,
        input_keys=[input_key],
    )


__all__ = [
    "ReorientParameters",
    "ReorientResult",
    "reorient_volume",
    "run_reorient_stage",
]

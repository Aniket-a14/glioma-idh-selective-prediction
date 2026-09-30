"""Online, deterministic spatial and intensity augmentation for Phase 06."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import torch
from scipy.ndimage import affine_transform  # type: ignore[import-untyped]

__all__ = ["AugmentConfig", "augment_sample"]


@dataclass(frozen=True)
class AugmentConfig:
    """Augmentation ranges; angles are degrees and distances are voxels."""

    rotation_degrees: float = 10.0
    scale_min: float = 0.9
    scale_max: float = 1.1
    translation_voxels: float = 8.0
    intensity_scale_min: float = 0.9
    intensity_scale_max: float = 1.1
    intensity_shift: float = 0.1
    gaussian_noise_sd: float = 0.05


def _rotation_matrix(angles: np.ndarray) -> np.ndarray:
    """Build a 3-D rotation matrix from angles in radians."""
    sx, sy, sz = np.sin(angles)
    cx, cy, cz = np.cos(angles)
    rx = np.array([[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]])
    ry = np.array([[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]])
    rz = np.array([[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]])
    return cast(np.ndarray, rz @ ry @ rx)


def _spatial_transform(
    array: np.ndarray,
    matrix: np.ndarray,
    offset: np.ndarray,
    *,
    order: int,
) -> np.ndarray:
    """Apply one output-to-input transform across the channel dimension."""
    result = np.empty(array.shape, dtype=np.float32)
    for channel in range(array.shape[0]):
        result[channel] = affine_transform(
            array[channel],
            matrix,
            offset=offset,
            output_shape=array.shape[1:],
            order=order,
            mode="constant",
            cval=0.0,
            prefilter=False,
        )
    return result


def augment_sample(
    sample: Mapping[str, Any],
    rng: np.random.Generator,
    config: AugmentConfig | None = None,
) -> dict[str, Any]:
    """Return an augmented copy of one sample using only the supplied RNG.

    Spatial parameters are shared by image and segmentation. Per-channel
    intensity operations and noise touch only non-zero voxels. A modality that
    was zeroed before augmentation and voxels outside the transformed brain
    mask remain exactly zero.
    """
    if config is None:
        config = AugmentConfig()
    image_tensor = cast(torch.Tensor, sample["image"])
    seg_tensor = cast(torch.Tensor, sample["seg"])
    image = image_tensor.detach().cpu().numpy().astype(np.float32, copy=True)
    seg = seg_tensor.detach().cpu().numpy().astype(np.float32, copy=True)
    if image.ndim != 4 or seg.ndim != 4 or image.shape[1:] != seg.shape[1:]:
        raise ValueError("image and segmentation must be channel-first 3-D arrays")

    shape = np.asarray(image.shape[1:], dtype=np.float64)
    angles = np.deg2rad(
        rng.uniform(-config.rotation_degrees, config.rotation_degrees, size=3)
    )
    scale = float(rng.uniform(config.scale_min, config.scale_max))
    forward = _rotation_matrix(angles) * scale
    inverse = np.linalg.inv(forward)
    translation = rng.uniform(
        -config.translation_voxels, config.translation_voxels, size=3
    )
    center = (shape - 1.0) / 2.0
    offset = center - inverse @ (center + translation)

    original_nonzero = image != 0.0
    transformed_brain = np.any(
        _spatial_transform(
            original_nonzero.astype(np.float32), inverse, offset, order=0
        )
        > 0.5,
        axis=0,
    )
    image = _spatial_transform(image, inverse, offset, order=1)
    seg = _spatial_transform(seg, inverse, offset, order=0)
    image[:, ~transformed_brain] = 0.0
    seg[:, ~transformed_brain] = 0.0

    for channel in range(image.shape[0]):
        channel_brain = (image[channel] != 0.0) & transformed_brain
        if not np.any(original_nonzero[channel]):
            image[channel] = 0.0
            continue
        factor = float(
            rng.uniform(config.intensity_scale_min, config.intensity_scale_max)
        )
        shift = float(rng.uniform(-config.intensity_shift, config.intensity_shift))
        values = image[channel]
        values[channel_brain] = values[channel_brain] * factor + shift
        values[channel_brain] += rng.normal(
            0.0, config.gaussian_noise_sd, size=int(channel_brain.sum())
        ).astype(np.float32)
        values[~transformed_brain] = 0.0

    augmented: dict[str, Any] = dict(sample)
    augmented["image"] = torch.from_numpy(np.ascontiguousarray(image))
    augmented["seg"] = torch.from_numpy(np.ascontiguousarray(seg))
    return augmented

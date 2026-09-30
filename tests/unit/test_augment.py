from __future__ import annotations

from typing import Any, cast

import numpy as np
import torch

from glioma_selective.training.augment import AugmentConfig, augment_sample


def _sample() -> dict[str, Any]:
    image = torch.zeros((4, 12, 12, 12), dtype=torch.float32)
    seg = torch.zeros((3, 12, 12, 12), dtype=torch.float32)
    image[0, 5, 5, 5] = 1.0
    image[1, 5, 5, 5] = 2.0
    seg[0, 5, 5, 5] = 1.0
    return {
        "image": image,
        "seg": seg,
        "has_seg": torch.tensor(True),
        "label": torch.tensor(1.0),
        "patient_id": "UTSW-BT0001",
    }


def test_augmentation_is_byte_identical_for_identical_rng_state() -> None:
    sample = _sample()
    left = augment_sample(sample, np.random.default_rng(17))
    right = augment_sample(sample, np.random.default_rng(17))
    assert torch.equal(
        cast(torch.Tensor, left["image"]), cast(torch.Tensor, right["image"])
    )
    assert torch.equal(
        cast(torch.Tensor, left["seg"]), cast(torch.Tensor, right["seg"])
    )


class _TranslationRng:
    """Hand-controlled draws: identity rotation/scale, then +1 on axis zero."""

    def __init__(self) -> None:
        self.uniform_calls = 0

    def uniform(
        self, low: Any, high: Any, size: int | tuple[int, ...] | None = None
    ) -> Any:
        self.uniform_calls += 1
        if self.uniform_calls == 1:
            return np.zeros(3)
        if self.uniform_calls == 2:
            return 1.0
        if self.uniform_calls == 3:
            return np.array([1.0, 0.0, 0.0])
        if low == high:
            return np.full(size, low) if size is not None else low
        return 1.0 if size is None else np.ones(size)

    def normal(self, loc: float, scale: float, size: int) -> np.ndarray:
        return np.zeros(size, dtype=np.float32)


def test_joint_transform_keeps_image_and_segmentation_aligned() -> None:
    config = AugmentConfig(
        rotation_degrees=0.0,
        scale_min=1.0,
        scale_max=1.0,
        translation_voxels=1.0,
        intensity_scale_min=1.0,
        intensity_scale_max=1.0,
        intensity_shift=0.0,
        gaussian_noise_sd=0.0,
    )
    transformed = augment_sample(_sample(), _TranslationRng(), config)  # type: ignore[arg-type]
    image = cast(torch.Tensor, transformed["image"])
    seg = cast(torch.Tensor, transformed["seg"])
    assert image[0, 6, 5, 5] == 1.0
    assert seg[0, 6, 5, 5] == 1.0
    assert image[0].sum() == 1.0
    assert seg[0].sum() == 1.0


def test_zero_channels_and_background_stay_zero() -> None:
    sample = _sample()
    sample["image"][3, 5, 5, 5] = 0.0
    transformed = augment_sample(sample, np.random.default_rng(5))
    image = cast(torch.Tensor, transformed["image"])
    assert torch.count_nonzero(image[3]) == 0
    assert torch.count_nonzero(image[:, 0, :, :]) == 0
    seg = cast(torch.Tensor, transformed["seg"])
    assert torch.count_nonzero(seg[:, 0, :, :]) == 0

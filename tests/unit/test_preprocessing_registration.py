"""Unit tests for deterministic rigid registration."""

from __future__ import annotations

import numpy as np
import SimpleITK as sitk

from glioma_selective.preprocessing.registration import apply_transform, rigid_register


def _asymmetric_blob() -> sitk.Image:
    first = sitk.GaussianSource(
        sitk.sitkFloat32,
        size=[24, 24, 24],
        sigma=[4.0, 5.0, 3.0],
        mean=[10.0, 12.0, 14.0],
    )
    second = sitk.GaussianSource(
        sitk.sitkFloat32,
        size=[24, 24, 24],
        sigma=[2.0, 3.0, 2.0],
        mean=[17.0, 7.0, 8.0],
    )
    return first + second


def test_registering_image_to_itself_is_identity_within_tolerance() -> None:
    image = _asymmetric_blob()

    result = rigid_register(image, image, n_threads=1, seed=123)

    assert max(abs(value) for value in result.parameters[:3]) < 0.05
    assert max(abs(value) for value in result.parameters[3:]) < 0.1
    assert result.stop_reason


def test_registration_recovers_known_small_translation_and_rotation() -> None:
    fixed = _asymmetric_blob()
    known = sitk.Euler3DTransform()
    known.SetCenter((11.5, 11.5, 11.5))
    known.SetParameters((0.02, -0.015, 0.01, 1.2, -0.8, 0.7))
    moving = sitk.Resample(
        fixed, fixed, known, sitk.sitkLinear, 0.0, fixed.GetPixelID()
    )

    result = rigid_register(fixed, moving, n_threads=1, seed=123)
    expected = known.GetInverse().GetParameters()

    np.testing.assert_allclose(result.parameters[:3], expected[:3], atol=0.05)
    np.testing.assert_allclose(result.parameters[3:], expected[3:], atol=0.2)


def test_registration_is_reproducible_for_same_seed() -> None:
    fixed = _asymmetric_blob()
    moving = sitk.Resample(
        fixed,
        fixed,
        sitk.TranslationTransform(3, (1.0, -0.5, 0.75)),
        sitk.sitkLinear,
        0.0,
        fixed.GetPixelID(),
    )

    first = rigid_register(fixed, moving, n_threads=1, seed=7)
    second = rigid_register(fixed, moving, n_threads=1, seed=7)

    np.testing.assert_allclose(first.parameters, second.parameters, atol=1e-12)
    assert first.center == second.center
    assert first.metric_value == second.metric_value
    assert first.stop_reason == second.stop_reason


def test_apply_transform_uses_reference_grid_and_nearest_neighbour_for_masks() -> None:
    fixed = _asymmetric_blob()
    moving = sitk.Image(fixed.GetSize(), sitk.sitkUInt8)
    moving.CopyInformation(fixed)
    moving[8, 9, 10] = 1
    result = rigid_register(fixed, fixed, n_threads=1, seed=1)

    transformed = apply_transform(moving, fixed, result, is_mask=True)

    assert transformed.GetSize() == fixed.GetSize()
    assert transformed.GetPixelID() == moving.GetPixelID()
    assert set(np.unique(sitk.GetArrayFromImage(transformed))) <= {0, 1}

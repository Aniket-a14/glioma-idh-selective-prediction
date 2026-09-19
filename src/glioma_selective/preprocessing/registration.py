"""Deterministic rigid registration using SimpleITK."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import SimpleITK as sitk


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    """Plain-data result of a three-dimensional Euler rigid registration."""

    transform_parameters: tuple[float, ...]
    transform_center: tuple[float, float, float]
    final_metric_value: float
    optimizer_stop_reason: str

    @property
    def parameters(self) -> tuple[float, ...]:
        """Return the Euler transform parameters as a plain tuple."""

        return self.transform_parameters

    @property
    def center(self) -> tuple[float, float, float]:
        """Return the Euler transform centre as a plain tuple."""

        return self.transform_center

    @property
    def metric_value(self) -> float:
        """Return the final registration metric value."""

        return self.final_metric_value

    @property
    def stop_reason(self) -> str:
        """Return the optimizer's stop-condition description."""

        return self.optimizer_stop_reason


def _seeded_fixed_mask(fixed: sitk.Image, seed: int) -> sitk.Image:
    """Build a deterministic metric mask from a caller-controlled seed."""

    array = sitk.GetArrayFromImage(fixed)
    generator = np.random.default_rng(seed)
    mask_array = generator.random(array.shape) < 0.20
    mask = sitk.GetImageFromArray(mask_array.astype(np.uint8, copy=False))
    mask.CopyInformation(fixed)
    return mask


def _result_transform(result: RegistrationResult) -> sitk.Euler3DTransform:
    """Reconstruct the SimpleITK transform stored in ``result``."""

    transform = sitk.Euler3DTransform()
    transform.SetCenter(result.transform_center)
    transform.SetParameters(result.transform_parameters)
    return transform


def rigid_register(
    fixed: sitk.Image,
    moving: sitk.Image,
    *,
    n_threads: int = 2,
    seed: int = 0,
) -> RegistrationResult:
    """Register ``moving`` to ``fixed`` with a deterministic rigid transform.

    The registration uses an Euler3D transform, Mattes mutual information,
    two resolution levels, and a seeded fixed metric-point mask.  The mask is
    used instead of SimpleITK's unseedable random sampler in the pinned
    SimpleITK Python API, preserving the requested fixed-seed determinism.
    ``n_threads`` limits the registration object's worker count.
    """

    if fixed.GetDimension() != 3 or moving.GetDimension() != 3:
        raise ValueError("rigid registration requires three-dimensional images")
    if n_threads < 1:
        raise ValueError("n_threads must be at least one")

    initial = sitk.Euler3DTransform()
    initial = sitk.CenteredTransformInitializer(
        fixed,
        moving,
        initial,
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )
    registration = sitk.ImageRegistrationMethod()
    registration.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)
    registration.SetMetricSamplingStrategy(sitk.ImageRegistrationMethod.NONE)
    registration.SetMetricFixedMask(_seeded_fixed_mask(fixed, seed))
    registration.SetInterpolator(sitk.sitkLinear)
    registration.SetOptimizerAsRegularStepGradientDescent(
        learningRate=2.0,
        minStep=0.01,
        numberOfIterations=100,
        relaxationFactor=0.5,
        gradientMagnitudeTolerance=1e-4,
    )
    registration.SetOptimizerScalesFromPhysicalShift()
    registration.SetShrinkFactorsPerLevel([2, 1])
    registration.SetSmoothingSigmasPerLevel([1, 0])
    registration.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()
    registration.SetInitialTransform(initial, inPlace=False)
    registration.SetNumberOfThreads(int(n_threads))
    transform = registration.Execute(fixed, moving)
    euler = sitk.Euler3DTransform()
    euler.SetCenter(initial.GetCenter())
    euler.SetParameters(transform.GetParameters())
    center = euler.GetCenter()
    return RegistrationResult(
        transform_parameters=tuple(float(value) for value in euler.GetParameters()),
        transform_center=(
            float(center[0]),
            float(center[1]),
            float(center[2]),
        ),
        final_metric_value=float(registration.GetMetricValue()),
        optimizer_stop_reason=registration.GetOptimizerStopConditionDescription(),
    )


def apply_transform(
    moving: sitk.Image,
    reference: sitk.Image,
    result: RegistrationResult,
    *,
    is_mask: bool = False,
) -> sitk.Image:
    """Resample ``moving`` into ``reference``'s grid using ``result``."""

    if moving.GetDimension() != 3 or reference.GetDimension() != 3:
        raise ValueError("transform application requires three-dimensional images")
    interpolator = sitk.sitkNearestNeighbor if is_mask else sitk.sitkLinear
    return sitk.Resample(
        moving,
        reference,
        _result_transform(result),
        interpolator,
        0.0,
        moving.GetPixelID(),
    )

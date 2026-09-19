"""Verification-only quality checks for Phase 04 core MRI inputs.

The UTSW and UCSF-PDGM core volumes are already skull-stripped, registered,
and on the expected grid (D-026).  This module therefore measures those
properties without transforming the inputs.  It also keeps the checks usable
for future raw cohorts and for deliberately failing synthetic cases.

Voxel data are read one volume at a time.  After a read, only a boolean
non-zero mask and scalar measurements are retained; the loaded image and its
voxel array are released before the next volume is read.  This bounds the
number of simultaneously loaded voxel volumes at one, without multiprocessing
or a global cache.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

import nibabel as nib
import numpy as np

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.discovery import CaseRecord

__all__ = [
    "CaseVerification",
    "ExpectedGrid",
    "VerificationCheck",
    "VerificationThresholds",
    "build_verification_report",
    "verify_case",
]


FailureCategory = Literal[
    "corrupt",
    "orientation-wrong",
    "registration-failed",
    "skullstrip-over",
    "skullstrip-under",
]

_SCHEMA_VERSION: Final[int] = 1
_AFFINE_ATOL: Final[float] = 1e-4
_SPACING_ATOL: Final[float] = 1e-4
_FAILURE_CATEGORIES: tuple[FailureCategory, ...] = (
    "corrupt",
    "orientation-wrong",
    "registration-failed",
    "skullstrip-over",
    "skullstrip-under",
)


@dataclass(frozen=True)
class ExpectedGrid:
    """Expected header geometry before any Phase 04 transformation.

    D-026 establishes the defaults for UTSW and UCSF-PDGM: a 240 x 240 x
    155 LPS grid with 1 mm spacing.  The affine origin is intentionally not
    part of this cohort-wide expectation because the two cohorts have
    different origins; affine equality is checked within each case instead.
    """

    shape: tuple[int, int, int] = (240, 240, 155)
    spacing: tuple[float, float, float] = (1.0, 1.0, 1.0)
    input_orientation: str = "LPS"

    def __post_init__(self) -> None:
        if len(self.shape) != 3 or any(d <= 0 for d in self.shape):
            raise ValueError(
                "expected grid shape must contain three positive dimensions"
            )
        if len(self.spacing) != 3 or any(s <= 0 for s in self.spacing):
            raise ValueError("expected grid spacing must contain three positive values")
        if len(self.input_orientation) != 3:
            raise ValueError("expected input orientation must contain three axcodes")


@dataclass(frozen=True)
class VerificationThresholds:
    """Thresholds for automated checks.

    The brain-fraction bounds are deliberately wide and provisional, not
    calibrated: D-026 measured roughly 0.11--0.20, and T04.9 human visual QC
    must calibrate these bounds later.  The cross-sequence Dice threshold is
    also recorded per case so a later calibration can audit its effect.
    """

    min_cross_sequence_mask_dice: float = 0.99
    max_brain_fraction: float = 0.35
    min_brain_fraction: float = 0.05

    def __post_init__(self) -> None:
        values = (
            self.min_cross_sequence_mask_dice,
            self.max_brain_fraction,
            self.min_brain_fraction,
        )
        if not all(np.isfinite(value) for value in values):
            raise ValueError("verification thresholds must be finite")
        if not 0 <= self.min_cross_sequence_mask_dice <= 1:
            raise ValueError("minimum mask Dice must be between zero and one")
        if not 0 <= self.min_brain_fraction <= self.max_brain_fraction <= 1:
            raise ValueError("brain-fraction bounds must be ordered in [0, 1]")


@dataclass(frozen=True)
class VerificationCheck:
    """One measured verification check and its optional failure category."""

    passed: bool
    measured: object | None
    failure_category: FailureCategory | None = None


@dataclass(frozen=True)
class CaseVerification:
    """All in-memory results for one case, including its canonical ID."""

    cohort: Cohort
    patient_id: str
    status: str
    checks: Mapping[str, VerificationCheck]
    failure_categories: tuple[FailureCategory, ...]
    brain_voxel_fraction: float | None
    cross_sequence_dice: Mapping[str, float]
    segmentation_inside_brain_fraction: Mapping[str, float]

    @property
    def passed(self) -> bool:
        """Whether every check passed, represented as verified-passthrough."""

        return self.status == "verified-passthrough"


@dataclass(frozen=True)
class _VolumeMeasurement:
    """Voxel-derived values retained after one volume has been released."""

    mask: np.ndarray
    shape: tuple[int, int, int]
    spacing: tuple[float, float, float]
    orientation: str
    affine: np.ndarray


def _read_volume(path: Path) -> _VolumeMeasurement:
    """Read one volume, validate finite voxels, and retain only its mask.

    The returned mask is the only array retained by the caller.  The image and
    voxel array are local variables so they become unreachable when this
    function returns.  ``ValueError`` is used for all malformed voxel content;
    the caller deliberately records only the generic ``corrupt`` category and
    never serializes an exception containing a filesystem path.
    """

    image = nib.load(path)
    if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
        raise ValueError("unsupported NIfTI image type")
    if len(image.shape) != 3:
        raise ValueError("volume is not three-dimensional")
    voxels = np.asarray(image.get_fdata(dtype=np.float32))
    if not np.all(np.isfinite(voxels)):
        raise ValueError("volume contains non-finite voxels")
    if not np.any(voxels != 0):
        raise ValueError("volume is all zero")

    zooms = image.header.get_zooms()
    if len(zooms) < 3:
        raise ValueError("volume has fewer than three spatial spacings")
    shape = (
        int(image.shape[0]),
        int(image.shape[1]),
        int(image.shape[2]),
    )
    spacing = (
        round(float(zooms[0]), 4),
        round(float(zooms[1]), 4),
        round(float(zooms[2]), 4),
    )
    orientation = "".join(
        code if code is not None else "?" for code in nib.aff2axcodes(image.affine)
    )
    affine = np.asarray(image.affine, dtype=np.float64).copy()
    mask = np.asarray(voxels != 0, dtype=bool)
    del voxels
    del image
    return _VolumeMeasurement(
        mask=mask,
        shape=shape,
        spacing=spacing,
        orientation=orientation,
        affine=affine,
    )


def _dice(left: np.ndarray, right: np.ndarray) -> float:
    """Return the Dice coefficient for two equally shaped boolean masks."""

    if left.shape != right.shape:
        raise ValueError("Dice masks must have equal shapes")
    left_count = int(np.count_nonzero(left))
    right_count = int(np.count_nonzero(right))
    denominator = left_count + right_count
    if denominator == 0:
        return 1.0
    intersection = int(np.count_nonzero(left & right))
    return 2.0 * intersection / denominator


def _grid_check(measurement: _VolumeMeasurement, expected: ExpectedGrid) -> bool:
    return bool(
        measurement.shape == expected.shape
        and np.allclose(measurement.spacing, expected.spacing, atol=_SPACING_ATOL)
        and measurement.orientation == expected.input_orientation
    )


def _new_check(
    checks: dict[str, VerificationCheck],
    name: str,
    passed: bool,
    measured: object | None,
    failure_category: FailureCategory | None = None,
) -> None:
    checks[name] = VerificationCheck(
        passed=bool(passed),
        measured=measured,
        failure_category=failure_category if not passed else None,
    )


def verify_case(
    case: CaseRecord,
    expected: ExpectedGrid,
    thresholds: VerificationThresholds,
) -> CaseVerification:
    """Verify one discovered case without transforming any input volume.

    Missing or unreadable core sequences are ``corrupt``.  Shape, spacing,
    orientation, and within-case affine mismatches are ``orientation-wrong``.
    Cross-sequence non-zero-mask disagreement is ``registration-failed``.
    Brain-fraction threshold failures are ``skullstrip-over`` or
    ``skullstrip-under``.  Modality mislabelling is not inferable from these
    measurements and is intentionally never emitted.
    """

    checks: dict[str, VerificationCheck] = {}
    measurements: dict[CanonicalSequence, _VolumeMeasurement] = {}
    failure_categories: set[FailureCategory] = set()
    cross_sequence_dice: dict[str, float] = {}

    for sequence in CORE_SEQUENCES:
        name = sequence.value
        path = case.sequence_files.get(sequence)
        if path is None:
            _new_check(checks, f"{name}.readable", False, None, "corrupt")
            failure_categories.add("corrupt")
            continue
        try:
            measurement = _read_volume(path)
        except (OSError, RuntimeError, ValueError, TypeError):
            _new_check(checks, f"{name}.readable", False, None, "corrupt")
            failure_categories.add("corrupt")
            continue
        measurements[sequence] = measurement
        _new_check(checks, f"{name}.readable", True, True)
        grid_passed = _grid_check(measurement, expected)
        _new_check(
            checks,
            f"{name}.grid",
            grid_passed,
            {
                "shape": list(measurement.shape),
                "spacing": list(measurement.spacing),
                "orientation": measurement.orientation,
            },
            "orientation-wrong",
        )
        if not grid_passed:
            failure_categories.add("orientation-wrong")

    t1ce = measurements.get(CanonicalSequence.T1CE)
    brain_fraction: float | None = None
    if t1ce is None:
        _new_check(checks, "cross_sequence.affine", False, None, "corrupt")
        _new_check(checks, "cross_sequence.mask_dice", False, None, "corrupt")
        _new_check(checks, "T1ce.brain_fraction", False, None, "corrupt")
        failure_categories.add("corrupt")
    else:
        brain_fraction = float(np.count_nonzero(t1ce.mask) / t1ce.mask.size)
        brain_category: FailureCategory | None
        if brain_fraction > thresholds.max_brain_fraction:
            brain_category = "skullstrip-over"
            brain_passed = False
        elif brain_fraction < thresholds.min_brain_fraction:
            brain_category = "skullstrip-under"
            brain_passed = False
        else:
            brain_category = None
            brain_passed = True
        _new_check(
            checks,
            "T1ce.brain_fraction",
            brain_passed,
            brain_fraction,
            brain_category,
        )
        if brain_category is not None:
            failure_categories.add(brain_category)

        affine_passed = True
        for _sequence, measurement in measurements.items():
            if not np.allclose(
                measurement.affine,
                t1ce.affine,
                atol=_AFFINE_ATOL,
                rtol=0,
            ):
                affine_passed = False
        _new_check(
            checks,
            "cross_sequence.affine",
            affine_passed,
            len(measurements),
            "orientation-wrong",
        )
        if not affine_passed:
            failure_categories.add("orientation-wrong")

        for sequence in CORE_SEQUENCES:
            sequence_measurement = measurements.get(sequence)
            if sequence_measurement is None:
                continue
            if sequence_measurement.mask.shape != t1ce.mask.shape:
                _new_check(
                    checks,
                    f"{sequence.value}.cross_sequence_mask_dice",
                    False,
                    None,
                    "orientation-wrong",
                )
                failure_categories.add("orientation-wrong")
                continue
            dice = _dice(sequence_measurement.mask, t1ce.mask)
            cross_sequence_dice[sequence.value] = dice
            dice_passed = dice >= thresholds.min_cross_sequence_mask_dice
            _new_check(
                checks,
                f"{sequence.value}.cross_sequence_mask_dice",
                dice_passed,
                dice,
                "registration-failed",
            )
            if not dice_passed:
                failure_categories.add("registration-failed")

    segmentation_inside: dict[str, float] = {}
    for role, path in sorted(case.segmentation_files.items()):
        try:
            segmentation = _read_volume(path)
        except (OSError, RuntimeError, ValueError, TypeError):
            _new_check(
                checks,
                f"segmentation.{role}.readable",
                False,
                None,
                "corrupt",
            )
            failure_categories.add("corrupt")
            continue

        shape_matches = t1ce is not None and segmentation.shape == t1ce.shape
        affine_matches = bool(
            t1ce is not None
            and np.allclose(
                segmentation.affine,
                t1ce.affine,
                atol=_AFFINE_ATOL,
                rtol=0,
            )
        )
        # With a corrupt/missing T1ce there is no reference geometry to test;
        # the core-volume failure already records the case as corrupt.
        alignment_passed = bool(t1ce is None or (shape_matches and affine_matches))
        _new_check(
            checks,
            f"segmentation.{role}.alignment",
            alignment_passed,
            {
                "shape": list(segmentation.shape),
                "shape_matches_t1ce": shape_matches,
                "affine_matches_t1ce": affine_matches,
            },
            "orientation-wrong",
        )
        if not alignment_passed:
            failure_categories.add("orientation-wrong")

        if t1ce is not None and segmentation.shape == t1ce.shape:
            segmentation_voxels = int(np.count_nonzero(segmentation.mask))
            if segmentation_voxels == 0:
                inside_fraction = 1.0
            else:
                inside_fraction = float(
                    np.count_nonzero(segmentation.mask & t1ce.mask)
                    / segmentation_voxels
                )
            segmentation_inside[role] = inside_fraction
            _new_check(
                checks,
                f"segmentation.{role}.inside_brain_fraction",
                True,
                inside_fraction,
            )
            self_dice = _dice(segmentation.mask, segmentation.mask)
            self_dice_passed = self_dice == 1.0
            _new_check(
                checks,
                f"segmentation.{role}.dice_self",
                self_dice_passed,
                self_dice,
                "corrupt",
            )
            if not self_dice_passed:
                failure_categories.add("corrupt")
        elif t1ce is not None:
            _new_check(
                checks,
                f"segmentation.{role}.inside_brain_fraction",
                False,
                None,
                "orientation-wrong",
            )
            failure_categories.add("orientation-wrong")

    ordered_categories = tuple(sorted(failure_categories))
    return CaseVerification(
        cohort=case.cohort,
        patient_id=case.patient_id,
        status="verified-passthrough" if not ordered_categories else "failed",
        checks=checks,
        failure_categories=ordered_categories,
        brain_voxel_fraction=brain_fraction,
        cross_sequence_dice=cross_sequence_dice,
        segmentation_inside_brain_fraction=segmentation_inside,
    )


def _distribution(values: Sequence[float]) -> dict[str, float | None]:
    """Return the fixed aggregate percentile summary for finite values."""

    if not values:
        return {key: None for key in ("min", "p1", "median", "p99", "max")}
    array = np.asarray(values, dtype=np.float64)
    percentiles = np.percentile(array, (1, 50, 99))
    return {
        "min": float(np.min(array)),
        "p1": float(percentiles[0]),
        "median": float(percentiles[1]),
        "p99": float(percentiles[2]),
        "max": float(np.max(array)),
    }


def build_verification_report(
    results: Sequence[CaseVerification],
) -> dict[str, object]:
    """Build an aggregate-only verification report with no IDs or paths."""

    grouped: dict[Cohort, list[CaseVerification]] = defaultdict(list)
    for result in results:
        grouped[result.cohort].append(result)

    cohort_reports: dict[str, object] = {}
    for cohort in sorted(grouped, key=lambda item: item.value):
        cohort_results = grouped[cohort]
        failure_counts: dict[str, int] = defaultdict(int)
        brain_fractions = [
            result.brain_voxel_fraction
            for result in cohort_results
            if result.brain_voxel_fraction is not None
        ]
        cross_dice = [
            value
            for result in cohort_results
            for value in result.cross_sequence_dice.values()
        ]
        segmentation_values: dict[str, list[float]] = defaultdict(list)
        for result in cohort_results:
            for role, value in result.segmentation_inside_brain_fraction.items():
                segmentation_values[role].append(value)
            for category in result.failure_categories:
                failure_counts[category] += 1
        for category in _FAILURE_CATEGORIES:
            failure_counts.setdefault(category, 0)

        cohort_reports[cohort.value] = {
            "case_count": len(cohort_results),
            "pass_count": sum(result.passed for result in cohort_results),
            "failure_counts_by_category": dict(sorted(failure_counts.items())),
            "brain_voxel_fraction_distribution": _distribution(brain_fractions),
            "cross_sequence_dice_distribution": _distribution(cross_dice),
            "segmentation_inside_brain_fraction_distribution": {
                role: _distribution(values)
                for role, values in sorted(segmentation_values.items())
            },
        }

    return {"schema_version": _SCHEMA_VERSION, "cohorts": cohort_reports}

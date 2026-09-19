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
    "SegmentationFinding",
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

_SCHEMA_VERSION: Final[int] = 2
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

    These thresholds are still provisional under D-031; the borderline
    brain-fraction bound has been raised twice after visual-QC misses.  The
    fail bounds decide whether a core-volume check fails.  A value that passes
    its fail bound but falls outside the tighter borderline band is sent to
    visual QC by T04.9.
    """

    min_cross_sequence_mask_dice: float = 0.90
    max_brain_fraction: float = 0.35
    min_brain_fraction: float = 0.05
    borderline_cross_sequence_mask_dice: float = 0.995
    borderline_max_brain_fraction: float = 0.30
    borderline_min_brain_fraction: float = 0.12

    def __post_init__(self) -> None:
        values = (
            self.min_cross_sequence_mask_dice,
            self.min_brain_fraction,
            self.max_brain_fraction,
            self.borderline_cross_sequence_mask_dice,
            self.borderline_min_brain_fraction,
            self.borderline_max_brain_fraction,
        )
        if not all(np.isfinite(value) for value in values):
            raise ValueError("verification thresholds must be finite")
        if not 0 <= self.min_cross_sequence_mask_dice <= 1:
            raise ValueError("minimum mask Dice must be between zero and one")
        if not 0 <= self.min_brain_fraction <= self.max_brain_fraction <= 1:
            raise ValueError("brain-fraction bounds must be ordered in [0, 1]")
        if not 0 <= self.borderline_cross_sequence_mask_dice <= 1:
            raise ValueError("borderline mask Dice must be between zero and one")
        if not (
            self.min_cross_sequence_mask_dice
            <= self.borderline_cross_sequence_mask_dice
        ):
            raise ValueError("borderline mask Dice must not be below the fail Dice")
        if not (
            0
            <= self.min_brain_fraction
            <= self.borderline_min_brain_fraction
            <= self.borderline_max_brain_fraction
            <= self.max_brain_fraction
            <= 1
        ):
            raise ValueError(
                "brain-fraction borderline bounds must be inside fail bounds"
            )


@dataclass(frozen=True)
class VerificationCheck:
    """One measured verification check and its optional failure category."""

    passed: bool
    measured: object | None
    failure_category: FailureCategory | None = None
    borderline: bool = False


@dataclass(frozen=True)
class SegmentationFinding:
    """Informational findings for one segmentation role.

    These findings never determine case status.  ``None`` means that a value
    was not measurable, such as for an unreadable mask or a missing T1ce
    reference.  An all-zero, readable mask has ``empty=True`` and a valid
    ``dice_self`` but no inside-brain fraction.
    """

    readable: bool
    empty: bool | None
    grid_matches_t1ce: bool | None
    inside_brain_fraction: float | None
    dice_self: float | None


@dataclass(frozen=True)
class CaseVerification:
    """All in-memory results for one case, including its canonical ID."""

    cohort: Cohort
    patient_id: str
    status: str
    checks: Mapping[str, VerificationCheck]
    failure_categories: tuple[FailureCategory, ...]
    borderline_checks: tuple[str, ...]
    brain_voxel_fraction: float | None
    cross_sequence_dice: Mapping[str, float]
    segmentation_findings: Mapping[str, SegmentationFinding]

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
    borderline: bool = False,
) -> None:
    checks[name] = VerificationCheck(
        passed=bool(passed),
        measured=measured,
        failure_category=failure_category if not passed else None,
        borderline=borderline,
    )


def _read_segmentation(path: Path) -> _VolumeMeasurement:
    """Read a segmentation while allowing an all-zero mask.

    Segmentation emptiness is an informational finding, not corruption.  The
    reader still rejects unreadable, non-finite, non-3D, and unsupported files.
    """

    image = nib.load(path)
    if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
        raise ValueError("unsupported NIfTI image type")
    if len(image.shape) != 3:
        raise ValueError("segmentation is not three-dimensional")
    voxels = np.asarray(image.get_fdata(dtype=np.float32))
    if not np.all(np.isfinite(voxels)):
        raise ValueError("segmentation contains non-finite voxels")

    zooms = image.header.get_zooms()
    if len(zooms) < 3:
        raise ValueError("segmentation has fewer than three spatial spacings")
    shape = (int(image.shape[0]), int(image.shape[1]), int(image.shape[2]))
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


def verify_case(
    case: CaseRecord,
    expected: ExpectedGrid,
    thresholds: VerificationThresholds,
) -> CaseVerification:
    """Verify one discovered case without transforming any input volume.

    Missing or unreadable core sequences are ``corrupt``.  Shape, spacing,
    orientation, and within-case affine mismatches are ``orientation-wrong``.
    Cross-sequence non-zero-mask disagreement is ``registration-failed``.
    Brain-fraction threshold failures are ``skullstrip-over`` when brain is
    removed and ``skullstrip-under`` when skull is retained.  Segmentation
    findings are informational and never affect case status.  Modality
    mislabelling is not inferable from these measurements and is intentionally
    never emitted.
    """

    checks: dict[str, VerificationCheck] = {}
    measurements: dict[CanonicalSequence, _VolumeMeasurement] = {}
    failure_categories: set[FailureCategory] = set()
    borderline_checks: set[str] = set()
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
        except (
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            nib.filebasedimages.ImageFileError,
        ):
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
            brain_category = "skullstrip-under"
            brain_passed = False
        elif brain_fraction < thresholds.min_brain_fraction:
            brain_category = "skullstrip-over"
            brain_passed = False
        elif (
            brain_fraction < thresholds.borderline_min_brain_fraction
            or brain_fraction > thresholds.borderline_max_brain_fraction
        ):
            brain_category = None
            brain_passed = True
            borderline_checks.add("T1ce.brain_fraction")
        else:
            brain_category = None
            brain_passed = True
        _new_check(
            checks,
            "T1ce.brain_fraction",
            brain_passed,
            brain_fraction,
            brain_category,
            borderline="T1ce.brain_fraction" in borderline_checks,
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
            dice_borderline = (
                dice_passed and dice < thresholds.borderline_cross_sequence_mask_dice
            )
            check_name = f"{sequence.value}.cross_sequence_mask_dice"
            if dice_borderline:
                borderline_checks.add(check_name)
            _new_check(
                checks,
                check_name,
                dice_passed,
                dice,
                "registration-failed",
                dice_borderline,
            )
            if not dice_passed:
                failure_categories.add("registration-failed")

    segmentation_findings: dict[str, SegmentationFinding] = {}
    for role, path in sorted(case.segmentation_files.items()):
        try:
            segmentation = _read_segmentation(path)
        except (
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            nib.filebasedimages.ImageFileError,
        ):
            segmentation_findings[role] = SegmentationFinding(
                readable=False,
                empty=None,
                grid_matches_t1ce=None,
                inside_brain_fraction=None,
                dice_self=None,
            )
            _new_check(
                checks,
                f"segmentation.{role}.readable",
                False,
                None,
            )
            continue

        empty = not bool(np.any(segmentation.mask))
        grid_matches = bool(
            t1ce is not None
            and segmentation.shape == t1ce.shape
            and np.allclose(
                segmentation.affine,
                t1ce.affine,
                atol=_AFFINE_ATOL,
                rtol=0,
            )
        )
        inside_fraction: float | None = None
        if not empty and grid_matches and t1ce is not None:
            inside_fraction = float(
                np.count_nonzero(segmentation.mask & t1ce.mask)
                / np.count_nonzero(segmentation.mask)
            )
        self_dice = _dice(segmentation.mask, segmentation.mask)
        segmentation_findings[role] = SegmentationFinding(
            readable=True,
            empty=empty,
            grid_matches_t1ce=grid_matches if t1ce is not None else None,
            inside_brain_fraction=inside_fraction,
            dice_self=self_dice,
        )
        _new_check(checks, f"segmentation.{role}.readable", True, True)
        _new_check(
            checks,
            f"segmentation.{role}.alignment",
            grid_matches,
            {
                "shape": list(segmentation.shape),
                "grid_matches_t1ce": grid_matches,
            },
            None,
        )
        _new_check(
            checks,
            f"segmentation.{role}.inside_brain_fraction",
            True,
            inside_fraction,
        )
        _new_check(
            checks,
            f"segmentation.{role}.dice_self",
            True,
            self_dice,
        )

    ordered_categories = tuple(sorted(failure_categories))
    if ordered_categories:
        status = "failed"
    elif borderline_checks:
        status = "verified-borderline"
    else:
        status = "verified-passthrough"
    return CaseVerification(
        cohort=case.cohort,
        patient_id=case.patient_id,
        status=status,
        checks=checks,
        failure_categories=ordered_categories,
        borderline_checks=tuple(sorted(borderline_checks)),
        brain_voxel_fraction=brain_fraction,
        cross_sequence_dice=cross_sequence_dice,
        segmentation_findings=segmentation_findings,
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
        borderline_counts: dict[str, int] = defaultdict(int)
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
        segmentation_by_role: dict[str, list[SegmentationFinding]] = defaultdict(list)
        for result in cohort_results:
            for role, finding in result.segmentation_findings.items():
                segmentation_by_role[role].append(finding)
            for category in result.failure_categories:
                failure_counts[category] += 1
            for check in result.borderline_checks:
                borderline_counts[check] += 1
        for category in _FAILURE_CATEGORIES:
            failure_counts.setdefault(category, 0)

        cohort_reports[cohort.value] = {
            "case_count": len(cohort_results),
            "pass_count": sum(
                result.status == "verified-passthrough" for result in cohort_results
            ),
            "borderline_count": sum(
                result.status == "verified-borderline" for result in cohort_results
            ),
            "failed_count": sum(result.status == "failed" for result in cohort_results),
            "failure_counts_by_category": dict(sorted(failure_counts.items())),
            "borderline_counts_by_check": dict(sorted(borderline_counts.items())),
            "brain_voxel_fraction_distribution": _distribution(brain_fractions),
            "cross_sequence_dice_distribution": _distribution(cross_dice),
            "segmentation": {
                role: {
                    "readable": sum(finding.readable for finding in findings),
                    "empty": sum(finding.empty is True for finding in findings),
                    "grid_matches_t1ce": sum(
                        finding.grid_matches_t1ce is True for finding in findings
                    ),
                    "inside_brain_fraction_distribution": _distribution(
                        [
                            finding.inside_brain_fraction
                            for finding in findings
                            if finding.inside_brain_fraction is not None
                        ]
                    ),
                }
                for role, findings in sorted(segmentation_by_role.items())
            },
        }

    return {"schema_version": _SCHEMA_VERSION, "cohorts": cohort_reports}

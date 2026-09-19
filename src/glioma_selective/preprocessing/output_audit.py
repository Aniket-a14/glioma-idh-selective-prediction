"""Audit the content-addressed outputs of the Phase 04 pipeline."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Final, cast

import nibabel as nib
import numpy as np

from glioma_selective.data.adapters._common import CORE_SEQUENCES
from glioma_selective.leakage.cohort_manifest import verify_roster_digest
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.cache import StageCache
from glioma_selective.preprocessing.verification import (
    ExpectedGrid,
    VerificationThresholds,
)
from glioma_selective.utils import paths

__all__ = ["OutputAuditError", "audit_preprocessing_outputs"]


_MASK_STAGE: Final[str] = "mask"
_VOLUME_STAGE: Final[str] = "volume"
_NEGATIVE_FRACTION_LIMIT: Final[float] = 1e-3
_MASK_IN_FOOTPRINT_LIMIT: Final[float] = 0.99
_AFFINE_ATOL: Final[float] = 1e-4
_Volume = tuple[np.ndarray, np.ndarray, str, np.dtype[np.generic]]


class OutputAuditError(ValueError):
    """Raised when an audit input is malformed or cannot be read."""


def _read_json(path: Path, message: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise OutputAuditError(message) from error


def _atomic_json_write(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _read_nifti(path: Path) -> tuple[np.ndarray, np.ndarray, str, np.dtype[np.generic]]:
    """Read one image once and return values, affine, orientation, and dtype."""

    image = nib.load(path)
    if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
        raise ValueError("unsupported NIfTI image type")
    if len(image.shape) != 3:
        raise ValueError("image is not three-dimensional")
    values = np.asarray(image.get_fdata(dtype=np.float32))
    if not np.all(np.isfinite(values)):
        raise ValueError("image contains non-finite voxels")
    affine = np.asarray(image.affine, dtype=np.float64).copy()
    orientation = "".join(
        code if code is not None else "?" for code in nib.aff2axcodes(affine)
    )
    dtype = np.dtype(image.get_data_dtype())
    return values, affine, orientation, dtype


def _entry_key(entry: Mapping[str, object], name: str) -> str | None:
    value = entry.get(name)
    return value if isinstance(value, str) and value else None


def _add_count(target: dict[str, dict[str, int]], name: str, passed: bool) -> None:
    counts = target.setdefault(name, {"passed": 0, "failed": 0})
    counts["passed" if passed else "failed"] += 1


def _load_outputs(path: Path) -> dict[str, dict[str, dict[str, object]]]:
    payload = _read_json(path, "preprocessing output index could not be read")
    if not isinstance(payload, dict):
        raise OutputAuditError("preprocessing output index must be an object")
    result: dict[str, dict[str, dict[str, object]]] = {}
    for raw_cohort, raw_cases in payload.items():
        if not isinstance(raw_cohort, str) or not isinstance(raw_cases, dict):
            raise OutputAuditError("preprocessing output index has invalid cohort data")
        cases: dict[str, dict[str, object]] = {}
        for raw_patient, raw_entry in raw_cases.items():
            if not isinstance(raw_patient, str) or not isinstance(raw_entry, dict):
                raise OutputAuditError(
                    "preprocessing output index has invalid case data"
                )
            cases[raw_patient] = dict(raw_entry)
        result[raw_cohort] = cases
    return result


def _load_cohort_manifest(path: Path) -> Mapping[str, object]:
    payload = _read_json(path, "post-QC cohort manifest could not be read")
    if not isinstance(payload, dict):
        raise OutputAuditError("post-QC cohort manifest must be an object")
    return cast(Mapping[str, object], payload)


def _manifest_cohort_entry(
    manifest: Mapping[str, object], cohort: str
) -> Mapping[str, object] | None:
    raw_cohorts = manifest.get("cohorts")
    if not isinstance(raw_cohorts, dict):
        raise OutputAuditError("post-QC cohort manifest is missing cohorts")
    raw_entry = raw_cohorts.get(cohort)
    if raw_entry is None:
        return None
    if not isinstance(raw_entry, dict):
        raise OutputAuditError("post-QC cohort manifest has invalid cohort data")
    return cast(Mapping[str, object], raw_entry)


def _load_volumes(
    cache: StageCache,
    entry: Mapping[str, object],
) -> tuple[dict[str, _Volume], dict[str, bool], list[str]]:
    volumes: dict[str, _Volume] = {}
    checks: dict[str, bool] = {}
    failures: list[str] = []
    for sequence in CORE_SEQUENCES:
        key = _entry_key(entry, sequence.value)
        loaded = False
        if key is not None:
            cache_entry = cache.get(_VOLUME_STAGE, key)
            if cache_entry is not None:
                try:
                    volumes[sequence.value] = _read_nifti(cache_entry / "volume.nii.gz")
                    loaded = True
                except (
                    OSError,
                    RuntimeError,
                    TypeError,
                    ValueError,
                    nib.filebasedimages.ImageFileError,
                ):
                    loaded = False
        checks[f"volume.{sequence.value}.load"] = loaded
        if not loaded:
            failures.append(f"volume.{sequence.value}.load")

    if len(volumes) != len(CORE_SEQUENCES):
        checks["volume_entries_load"] = False
        failures.append("volume_entries_load")
    else:
        checks["volume_entries_load"] = True
    return volumes, checks, failures


def _one_volume_geometry(
    values: np.ndarray,
    affine: np.ndarray,
    orientation: str,
    dtype: np.dtype[np.generic],
    expected: ExpectedGrid,
) -> bool:
    shape_ok = tuple(int(value) for value in values.shape) == expected.shape
    spacing = nib.affines.voxel_sizes(affine)
    spacing_ok = bool(
        len(spacing) == 3
        and np.all(np.abs(np.asarray(spacing) - expected.spacing) <= _AFFINE_ATOL)
    )
    return bool(
        shape_ok
        and spacing_ok
        and orientation == "RAS"
        and dtype == np.dtype(np.float32)
    )


def _volume_geometry(
    volumes: Mapping[str, _Volume], expected: ExpectedGrid
) -> tuple[bool, dict[str, object]]:
    geometry_passed = bool(volumes) and len(volumes) == len(CORE_SEQUENCES)
    negative_fractions: list[float] = []
    negative_counts: list[int] = []
    for values, affine, orientation, dtype in volumes.values():
        geometry_passed = geometry_passed and _one_volume_geometry(
            values, affine, orientation, dtype, expected
        )
        nonzero = values != 0
        nonzero_count = int(np.count_nonzero(nonzero))
        negative_count = int(np.count_nonzero(values < 0))
        negative_counts.append(negative_count)
        negative_fractions.append(
            negative_count / nonzero_count if nonzero_count else 0.0
        )
    return geometry_passed, {
        "negative_voxel_count": sum(negative_counts),
        "negative_volume_count": sum(count > 0 for count in negative_counts),
        "max_negative_fraction": max(negative_fractions, default=0.0),
        "negative_fraction_passed": all(
            fraction <= _NEGATIVE_FRACTION_LIMIT for fraction in negative_fractions
        )
        and len(volumes) == len(CORE_SEQUENCES),
    }


def _same_affine_shape(volumes: Mapping[str, _Volume]) -> bool:
    if len(volumes) != len(CORE_SEQUENCES):
        return False
    first_values, first_affine, _, _ = volumes[CORE_SEQUENCES[0].value]
    return all(
        values.shape == first_values.shape and np.array_equal(affine, first_affine)
        for values, affine, _, _ in volumes.values()
    )


def _dice_at_least(left: np.ndarray, right: np.ndarray, limit: float) -> bool:
    denominator = int(np.count_nonzero(left)) + int(np.count_nonzero(right))
    dice = (
        1.0
        if denominator == 0
        else 2.0 * int(np.count_nonzero(left & right)) / denominator
    )
    return dice >= limit


def _footprints_agree(volumes: Mapping[str, _Volume], dice_limit: float) -> bool:
    if len(volumes) != len(CORE_SEQUENCES):
        return False
    masks = [values != 0 for values, _, _, _ in volumes.values()]
    if any(np.all(mask) for mask in masks):
        return False
    if not all(mask.shape == masks[0].shape for mask in masks):
        return False
    return all(
        _dice_at_least(left, right, dice_limit)
        for index, left in enumerate(masks)
        for right in masks[index + 1 :]
    )


def _volume_grid_consistency(
    volumes: Mapping[str, _Volume], dice_limit: float
) -> tuple[bool, bool]:
    affine_shape_passed = _same_affine_shape(volumes)
    return affine_shape_passed, _footprints_agree(volumes, dice_limit)


def _load_mask(
    cache: StageCache, entry: Mapping[str, object]
) -> tuple[bool, _Volume | None]:
    mask_key = _entry_key(entry, "mask")
    if mask_key is not None:
        mask_entry = cache.get(_MASK_STAGE, mask_key)
        if mask_entry is not None:
            try:
                return True, _read_nifti(mask_entry / "mask.nii.gz")
            except (
                OSError,
                RuntimeError,
                TypeError,
                ValueError,
                nib.filebasedimages.ImageFileError,
            ):
                pass
    return False, None


def _mask_grid_labels(
    mask: _Volume, t1ce: _Volume, has_segmentation: object
) -> tuple[bool, bool, bool]:
    mask_values, mask_affine, mask_orientation, mask_dtype = mask
    t1ce_values, t1ce_affine, _, _ = t1ce
    integer_dtype = np.issubdtype(mask_dtype, np.integer)
    finite_labels = np.all(np.isfinite(mask_values))
    labels_ok = finite_labels and bool(
        np.all(np.isin(mask_values, np.asarray((0, 1, 2, 3), dtype=np.float32)))
    )
    shape_ok = mask_values.shape == t1ce_values.shape
    affine_ok = np.array_equal(mask_affine, t1ce_affine)
    nonzero = bool(np.any(mask_values != 0))
    properties_passed = bool(
        mask_orientation == "RAS"
        and integer_dtype
        and labels_ok
        and shape_ok
        and affine_ok
        and nonzero == has_segmentation
    )
    return properties_passed, shape_ok, nonzero


def _mask_alignment(
    mask_values: np.ndarray, t1ce_values: np.ndarray, nonzero: bool, shape_ok: bool
) -> tuple[bool, float]:
    if not nonzero:
        return True, 1.0
    if not shape_ok:
        return False, 1.0
    nonzero_mask = mask_values != 0
    fraction = float(
        np.count_nonzero(nonzero_mask & (t1ce_values != 0))
        / np.count_nonzero(nonzero_mask)
    )
    return fraction >= _MASK_IN_FOOTPRINT_LIMIT, fraction


def _mask_measurements(
    entry: Mapping[str, object],
    volumes: Mapping[str, _Volume],
    mask: _Volume | None,
    mask_loaded: bool,
) -> tuple[bool, bool, float, bool]:
    mask_alignment_fraction = 1.0
    has_segmentation = entry.get("has_segmentation")
    mask_checks_passed = mask_loaded and isinstance(has_segmentation, bool)
    alignment_passed = mask_loaded
    no_segmentation = False
    if mask_loaded and mask is not None:
        mask_values, mask_affine, mask_orientation, mask_dtype = mask
        t1ce = volumes.get("T1ce")
        nonzero_mask = mask_values != 0
        no_segmentation = not bool(np.any(nonzero_mask))
        if t1ce is None:
            mask_checks_passed = False
            alignment_passed = False
        else:
            t1ce_values, _, _, _ = t1ce
            if not isinstance(has_segmentation, bool):
                return False, False, mask_alignment_fraction, no_segmentation
            mask_checks_passed, shape_ok, nonzero = _mask_grid_labels(
                mask, t1ce, has_segmentation
            )
            alignment_passed, mask_alignment_fraction = _mask_alignment(
                mask_values, t1ce_values, nonzero, shape_ok
            )
    return (
        mask_checks_passed,
        bool(alignment_passed),
        mask_alignment_fraction,
        no_segmentation,
    )


def _audit_case(
    cache: StageCache,
    entry: Mapping[str, object],
    expected: ExpectedGrid,
    dice_limit: float,
) -> tuple[dict[str, bool], dict[str, object], list[str]]:
    volumes, checks, failures = _load_volumes(cache, entry)
    geometry_passed, geometry_details = _volume_geometry(volumes, expected)
    checks["volume_geometry"] = geometry_passed
    if not geometry_passed:
        failures.append("volume_geometry")
    negative_passed = cast(bool, geometry_details.pop("negative_fraction_passed"))
    checks["negative_fraction"] = negative_passed
    if not negative_passed:
        failures.append("negative_fraction")
    affine_passed, background_passed = _volume_grid_consistency(volumes, dice_limit)
    checks["cross_volume_affine_shape"] = affine_passed
    checks["background_footprint"] = background_passed
    if not affine_passed:
        failures.append("cross_volume_affine_shape")
    if not background_passed:
        failures.append("background_footprint")
    mask_loaded, mask = _load_mask(cache, entry)
    checks["mask.load"] = mask_loaded
    if not mask_loaded:
        failures.append("mask.load")
    mask_passed, alignment_passed, alignment_fraction, no_segmentation = (
        _mask_measurements(entry, volumes, mask, mask_loaded)
    )
    checks["mask_properties"] = mask_passed
    checks["mask_alignment"] = alignment_passed
    if not mask_passed:
        failures.append("mask_properties")
    if not alignment_passed:
        failures.append("mask_alignment")
    details = {
        **geometry_details,
        "mask_alignment_fraction": alignment_fraction,
        "no_segmentation": no_segmentation,
    }
    return checks, details, failures


def _audit_cases(
    cache: StageCache,
    case_entries: Mapping[str, Mapping[str, object]],
    expected: ExpectedGrid,
    dice_limit: float,
    cohort_name: str,
) -> tuple[dict[str, dict[str, int]], dict[str, object], list[dict[str, object]], bool]:
    check_counts: dict[str, dict[str, int]] = {}
    volumes_checked = 0
    negative_volume_count = 0
    total_negative_voxels = 0
    max_negative_fraction = 0.0
    alignment_values: list[float] = []
    no_segmentation_count = 0
    failures: list[dict[str, object]] = []
    for patient_id in sorted(case_entries):
        checks, details, case_failures = _audit_case(
            cache, case_entries[patient_id], expected, dice_limit
        )
        volumes_checked += sum(
            checks.get(f"volume.{sequence.value}.load", False)
            for sequence in CORE_SEQUENCES
        )
        negative_volume_count += cast(int, details["negative_volume_count"])
        total_negative_voxels += cast(int, details["negative_voxel_count"])
        max_negative_fraction = max(
            max_negative_fraction,
            cast(float, details["max_negative_fraction"]),
        )
        alignment_values.append(cast(float, details["mask_alignment_fraction"]))
        no_segmentation_count += int(cast(bool, details["no_segmentation"]))
        for name, passed in checks.items():
            _add_count(check_counts, name, passed)
        if case_failures:
            failures.append(
                {
                    "cohort": cohort_name,
                    "patient_id": patient_id,
                    "failed_checks": sorted(set(case_failures)),
                }
            )
    metrics = {
        "volumes_checked": volumes_checked,
        "negative_volume_count": negative_volume_count,
        "total_negative_voxels": total_negative_voxels,
        "max_negative_fraction": max_negative_fraction,
        "alignment_values": alignment_values,
        "no_segmentation_count": no_segmentation_count,
    }
    return check_counts, metrics, failures, not failures


def _roster_matches(
    manifest: Mapping[str, object], cohort: Cohort, patient_ids: Mapping[str, object]
) -> tuple[bool, bool]:
    entry = _manifest_cohort_entry(manifest, cohort.value)
    if entry is None:
        return False, False
    try:
        result = verify_roster_digest(manifest, cohort, patient_ids.keys())
    except (TypeError, ValueError, KeyError):
        return False, False
    return (
        result["roster_sha256"] == entry.get("roster_sha256"),
        result["retained_patient_count"] == entry.get("retained_patient_count"),
    )


def _audit_cohort(
    cache: StageCache,
    manifest: Mapping[str, object],
    cohort_name: str,
    case_entries: Mapping[str, Mapping[str, object]],
    expected: ExpectedGrid,
    dice_limit: float,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    try:
        cohort = Cohort(cohort_name)
    except ValueError as error:
        raise OutputAuditError(
            "preprocessing output index has an unsupported cohort"
        ) from error
    check_counts, metrics, failures, cases_passed = _audit_cases(
        cache, case_entries, expected, dice_limit, cohort_name
    )
    digest_match, count_match = _roster_matches(manifest, cohort, case_entries)
    roster_passed = digest_match and count_match
    _add_count(check_counts, "roster_digest", roster_passed)
    report = {
        "case_count": len(case_entries),
        "volumes_checked": metrics["volumes_checked"],
        "checks": dict(sorted(check_counts.items())),
        "negative_voxel_summary": {
            "volumes_with_any_negative": metrics["negative_volume_count"],
            "total_negative_voxels": metrics["total_negative_voxels"],
            "largest_negative_fraction_nonzero": metrics["max_negative_fraction"],
        },
        "mask_summary": {
            "minimum_mask_in_footprint_fraction": min(
                cast(list[float], metrics["alignment_values"]), default=1.0
            ),
            "no_segmentation_case_count": metrics["no_segmentation_count"],
        },
        "roster_digest_match": digest_match,
        "retained_patient_count_match": count_match,
        "passed": cases_passed and roster_passed,
    }
    return report, failures


def audit_preprocessing_outputs(
    *,
    outputs_path: Path | None = None,
    cohort_manifest_path: Path,
    output_path: Path,
    failures_path: Path | None = None,
    cache_root: Path | None = None,
    expected: ExpectedGrid | None = None,
) -> dict[str, object]:
    """Audit all indexed volume/mask outputs and write aggregate JSON.

    Patient identifiers are retained only in the optional private failure log.
    The committed report contains counts, measurements, thresholds, and roster
    digest booleans, but no identifiers or paths.
    """

    selected_outputs = outputs_path or (
        paths.manifests_dir() / "preprocessing_outputs.json"
    )
    selected_failures = failures_path or (
        paths.private_data_dir() / "preprocessing_output_audit_failures.json"
    )
    outputs = _load_outputs(selected_outputs)
    manifest = _load_cohort_manifest(cohort_manifest_path)
    grid = expected or ExpectedGrid()
    dice_limit = VerificationThresholds().min_cross_sequence_mask_dice
    cache = StageCache(cache_root or paths.processed_data_dir())
    cohorts: dict[str, object] = {}
    failures: list[dict[str, object]] = []
    overall_passed = True
    cohort_names = set(outputs) | {Cohort.UTSW.value, Cohort.UCSF_PDGM.value}
    for cohort_name in sorted(cohort_names):
        cohort_report, cohort_failures = _audit_cohort(
            cache,
            manifest,
            cohort_name,
            outputs.get(cohort_name, {}),
            grid,
            dice_limit,
        )
        cohorts[cohort_name] = cohort_report
        failures.extend(cohort_failures)
        overall_passed = overall_passed and bool(cohort_report["passed"])

    report: dict[str, object] = {
        "schema_version": 1,
        "cohorts": cohorts,
        "thresholds": {
            "expected_shape": list(grid.shape),
            "expected_spacing_mm": list(grid.spacing),
            "spacing_tolerance_mm": _AFFINE_ATOL,
            "negative_fraction_max": _NEGATIVE_FRACTION_LIMIT,
            "mask_in_footprint_min": _MASK_IN_FOOTPRINT_LIMIT,
            "cross_sequence_dice_min": dice_limit,
        },
        "passed": overall_passed and not failures,
    }
    _atomic_json_write(output_path, report)
    if failures:
        _atomic_json_write(selected_failures, {"failures": failures})
    return report

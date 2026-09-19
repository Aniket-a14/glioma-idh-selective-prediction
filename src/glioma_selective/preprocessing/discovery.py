"""Discover preprocessing inputs without reading NIfTI voxel data.

The Phase 02 adapters own directory and filename discovery.  This module adds
the retained-roster boundary, header-only geometry inspection, segmentation
role discovery, and aggregate reporting needed by Phase 04 T04.1.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

import nibabel as nib
import numpy as np

from glioma_selective.data.adapters import ucsf_pdgm, utsw
from glioma_selective.data.adapters._common import (
    CORE_SEQUENCES,
    CanonicalSequence,
    PatientFileInventory,
)
from glioma_selective.leakage.cohort_manifest import _UCSF_FOLLOWUP_DIRECTORY_RE
from glioma_selective.leakage.id_normalization import Cohort, normalize_identifier

__all__ = [
    "CaseRecord",
    "VolumeGeometry",
    "build_geometry_report",
    "discover_cases",
    "inspect_volume_geometry",
]


_REPORT_SCHEMA_VERSION: Final[int] = 1
_UCSF_BASELINE_COHORT: Final[Cohort] = Cohort.UCSF_PDGM
_SEGMENTATION_ROLES: dict[Cohort, frozenset[str]] = {
    Cohort.UTSW: frozenset(
        {
            "tumorseg_FeTS",
            "tumorseg_manual_correction",
            "rtumorseg_manual_correction",
        }
    ),
    Cohort.UCSF_PDGM: frozenset(
        {
            "tumor_segmentation",
            "brain_segmentation",
            "brain_parenchyma_segmentation",
        }
    ),
}
_NIFTI_SUFFIX_RE = re.compile(r"(?i)(?:\.nii\.gz|\.nii)$")
GeometryKey = tuple[tuple[int, int, int], tuple[float, float, float], str, str]


@dataclass(frozen=True)
class VolumeGeometry:
    """Geometry and header metadata read without loading voxel data."""

    shape: tuple[int, int, int]
    spacing: tuple[float, float, float]
    orientation: str
    dtype: str
    affine_sha256: str


@dataclass(frozen=True)
class CaseRecord:
    """Header-inspected inputs for one canonical patient record.

    ``patient_id`` is canonicalized with :func:`normalize_identifier`.  The
    source path and file paths are retained only in memory for downstream
    preprocessing; aggregate reports deliberately omit them.
    """

    cohort: Cohort
    patient_id: str
    source_directory: Path
    sequence_files: Mapping[CanonicalSequence, Path]
    geometries: Mapping[CanonicalSequence, VolumeGeometry]
    segmentation_files: Mapping[str, Path]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "sequence_files", MappingProxyType(dict(self.sequence_files))
        )
        object.__setattr__(self, "geometries", MappingProxyType(dict(self.geometries)))
        object.__setattr__(
            self, "segmentation_files", MappingProxyType(dict(self.segmentation_files))
        )

    @property
    def canonical_patient_id(self) -> str:
        """Return the canonical patient identifier stored in ``patient_id``."""

        return self.patient_id

    @property
    def missing_sequences(self) -> tuple[CanonicalSequence, ...]:
        """Return missing core sequences without substituting another file."""

        return tuple(
            sequence
            for sequence in CORE_SEQUENCES
            if sequence not in self.sequence_files
        )


def inspect_volume_geometry(volume_path: Path) -> VolumeGeometry:
    """Read a NIfTI header and return rounded geometry metadata.

    The image object is intentionally never converted to an array.  In
    particular, this function does not access ``dataobj`` or call
    ``get_fdata``; a valid header is sufficient for T04.1.
    """

    image = nib.load(volume_path)
    if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
        raise ValueError("preprocessing inputs must be NIfTI-1 or NIfTI-2 images")
    if len(image.shape) != 3:
        raise ValueError("preprocessing inputs must be three-dimensional NIfTI volumes")

    shape = (
        int(image.shape[0]),
        int(image.shape[1]),
        int(image.shape[2]),
    )
    zooms = image.header.get_zooms()
    if len(zooms) < 3:
        raise ValueError("NIfTI header does not contain three spatial zooms")
    spacing = (
        round(float(zooms[0]), 4),
        round(float(zooms[1]), 4),
        round(float(zooms[2]), 4),
    )

    affine = np.asarray(image.affine, dtype=np.float64)
    rounded_affine = np.round(affine, 4)
    affine_sha256 = hashlib.sha256(
        rounded_affine.astype("<f8", copy=False).tobytes(order="C")
    ).hexdigest()
    orientation = "".join(
        code if code is not None else "?" for code in nib.aff2axcodes(affine)
    )
    dtype = np.dtype(image.get_data_dtype()).name
    return VolumeGeometry(
        shape=shape,
        spacing=spacing,
        orientation=orientation,
        dtype=dtype,
        affine_sha256=affine_sha256,
    )


def _coerce_cohort(cohort: Cohort | str) -> Cohort:
    if isinstance(cohort, Cohort):
        return cohort
    aliases = {
        "utsw": Cohort.UTSW,
        "utsw-glioma": Cohort.UTSW,
        "utsw_glioma": Cohort.UTSW,
        "ucsf-pdgm": Cohort.UCSF_PDGM,
        "ucsf_pdgm": Cohort.UCSF_PDGM,
        "egd": Cohort.EGD,
    }
    try:
        return aliases[cohort.strip().lower()]
    except KeyError as error:
        raise ValueError(f"unsupported preprocessing cohort: {cohort!r}") from error


def _inventory_for_cohort(
    cohort: Cohort, root: Path | None
) -> tuple[Path, tuple[PatientFileInventory, ...]]:
    if cohort is Cohort.UTSW:
        selected_root = root if root is not None else utsw.cohort_root()
        return selected_root, utsw.discover_files(selected_root)
    if cohort is _UCSF_BASELINE_COHORT:
        selected_root = root if root is not None else ucsf_pdgm.cohort_root()
        inventories = ucsf_pdgm.discover_files(selected_root)
        baseline = tuple(
            inventory
            for inventory in inventories
            if _UCSF_FOLLOWUP_DIRECTORY_RE.fullmatch(inventory.patient_id) is None
        )
        return selected_root, baseline
    if cohort is Cohort.EGD:
        # Delegate the error and its meaning to the Phase 02 EGD adapter.  No
        # EGD filename convention is inferred here.
        from glioma_selective.data.adapters import egd

        egd.identify_sequence(Path())
        raise AssertionError("EGD sequence identification unexpectedly returned")
    raise ValueError(f"unsupported preprocessing cohort: {cohort.value}")


def _normalize_requested_ids(
    retained_patient_ids: Iterable[str] | None, cohort: Cohort
) -> set[str] | None:
    if retained_patient_ids is None:
        return None
    normalized = {
        normalize_identifier(patient_id, cohort) for patient_id in retained_patient_ids
    }
    return normalized


def _segmentation_role(file_path: Path, cohort: Cohort) -> str | None:
    stem = _NIFTI_SUFFIX_RE.sub("", file_path.name)
    for role in _SEGMENTATION_ROLES.get(cohort, frozenset()):
        if stem == role or stem.endswith(f"_{role}"):
            return role
    return None


def _discover_segmentation_files(
    inventory: PatientFileInventory, cohort: Cohort
) -> dict[str, Path]:
    segmentation_files: dict[str, Path] = {}
    for file_path in inventory.files:
        role = _segmentation_role(file_path, cohort)
        if role is None:
            continue
        if role in segmentation_files:
            raise ValueError("multiple files found for one segmentation role")
        segmentation_files[role] = file_path
    return segmentation_files


def discover_cases(
    cohort: Cohort | str,
    *,
    retained_patient_ids: Iterable[str] | None = None,
    root: Path | None = None,
) -> tuple[CaseRecord, ...]:
    """Discover retained cases, using only the cohort adapter's inventory.

    Retained IDs are normalized before matching.  If a retained roster is
    supplied, every requested patient must exist in the baseline-filtered
    inventory and no unrequested patient is returned.
    """

    selected_cohort = _coerce_cohort(cohort)
    selected_root, inventories = _inventory_for_cohort(selected_cohort, root)
    requested_ids = _normalize_requested_ids(retained_patient_ids, selected_cohort)

    inventory_by_id: dict[str, PatientFileInventory] = {}
    for inventory in inventories:
        canonical_id = normalize_identifier(inventory.patient_id, selected_cohort)
        if canonical_id in inventory_by_id:
            raise ValueError("inventory contains duplicate canonical patient IDs")
        inventory_by_id[canonical_id] = inventory

    if requested_ids is not None:
        if not requested_ids.issubset(inventory_by_id):
            raise ValueError(
                "one or more retained patients are absent from the inventory"
            )
        selected_ids = requested_ids
    else:
        selected_ids = set(inventory_by_id)

    cases: list[CaseRecord] = []
    for canonical_id in sorted(selected_ids):
        inventory = inventory_by_id[canonical_id]
        sequence_files = dict(inventory.sequence_files)
        geometries = {
            sequence: inspect_volume_geometry(file_path)
            for sequence, file_path in sequence_files.items()
        }
        cases.append(
            CaseRecord(
                cohort=selected_cohort,
                patient_id=normalize_identifier(inventory.patient_id, selected_cohort),
                source_directory=selected_root / inventory.patient_id,
                sequence_files=sequence_files,
                geometries=geometries,
                segmentation_files=_discover_segmentation_files(
                    inventory, selected_cohort
                ),
            )
        )
    return tuple(cases)


def _geometry_key(geometry: VolumeGeometry) -> GeometryKey:
    return (
        geometry.shape,
        geometry.spacing,
        geometry.orientation,
        geometry.dtype,
    )


def _geometry_counts(
    cases: Iterable[CaseRecord], sequence: CanonicalSequence
) -> tuple[list[dict[str, object]], int]:
    geometries = [
        case.geometries[sequence] for case in cases if sequence in case.geometries
    ]
    counts: Counter[GeometryKey] = Counter(
        _geometry_key(geometry) for geometry in geometries
    )
    serialized = [
        {
            "shape": list(key[0]),
            "spacing": list(key[1]),
            "orientation": key[2],
            "dtype": key[3],
            "case_count": count,
        }
        for key, count in sorted(counts.items(), key=lambda item: repr(item[0]))
    ]
    return serialized, len({geometry.affine_sha256 for geometry in geometries})


def build_geometry_report(cases: Iterable[CaseRecord]) -> dict[str, object]:
    """Build an aggregate-only geometry and segmentation report."""

    grouped: dict[Cohort, list[CaseRecord]] = {}
    for case in cases:
        grouped.setdefault(case.cohort, []).append(case)

    cohort_reports: dict[str, object] = {}
    for cohort in sorted(grouped, key=lambda item: item.value):
        cohort_cases = grouped[cohort]
        sequence_report: dict[str, object] = {}
        for sequence in CORE_SEQUENCES:
            geometry_counts, distinct_affine_count = _geometry_counts(
                cohort_cases, sequence
            )
            sequence_report[sequence.value] = {
                "geometry_counts": geometry_counts,
                "distinct_affine_hash_count": distinct_affine_count,
            }

        segmentation_counts: Counter[str] = Counter(
            role for case in cohort_cases for role in case.segmentation_files
        )
        identical_affine_count = sum(
            len(case.geometries) == len(CORE_SEQUENCES)
            and len(
                {case.geometries[sequence].affine_sha256 for sequence in CORE_SEQUENCES}
            )
            == 1
            for case in cohort_cases
        )
        cohort_reports[cohort.value] = {
            "case_count": len(cohort_cases),
            "sequences": sequence_report,
            "cases_with_four_identical_affines": identical_affine_count,
            "cases_with_any_missing_sequence": sum(
                bool(case.missing_sequences) for case in cohort_cases
            ),
            "segmentation_role_counts": dict(sorted(segmentation_counts.items())),
        }

    return {
        "schema_version": _REPORT_SCHEMA_VERSION,
        "cohorts": cohort_reports,
    }

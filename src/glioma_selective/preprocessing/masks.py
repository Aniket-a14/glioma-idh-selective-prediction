"""FeTS/BraTS segmentation-target handling for Phase 04."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final

import nibabel as nib
import numpy as np

from glioma_selective.data.adapters._common import CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.cache import (
    StageCache,
    hash_file,
    stage_cache_key,
)
from glioma_selective.preprocessing.discovery import CaseRecord
from glioma_selective.preprocessing.resample import reorient_to_ras

__all__ = [
    "BRATS_TO_CLASS",
    "SegmentationTarget",
    "build_mask_report",
    "inspect_segmentation_target",
    "remap_labels",
    "run_mask_stage",
    "select_segmentation_file",
]


BRATS_TO_CLASS: Final[dict[int, int]] = {0: 0, 1: 1, 2: 2, 4: 3}
_CLASS_TO_BRATS: Final[dict[int, int]] = {
    class_id: label for label, class_id in BRATS_TO_CLASS.items()
}
_MASK_STAGE: Final[str] = "mask"
_MASK_STAGE_VERSION: Final[str] = "1"
_CACHE_LABEL_MAP: Final[dict[str, object]] = {
    "label_map": {str(label): class_id for label, class_id in BRATS_TO_CLASS.items()}
}
_GRID_TOLERANCE: Final[float] = 1e-4


@dataclass(frozen=True)
class SegmentationTarget:
    """Aggregate information about one selected segmentation target."""

    cohort: Cohort
    canonical_patient_id: str
    has_segmentation: bool
    class_voxel_counts: Mapping[int, int]
    grid_matches_t1ce: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "class_voxel_counts",
            MappingProxyType(
                {
                    int(class_id): int(count)
                    for class_id, count in self.class_voxel_counts.items()
                }
            ),
        )


def select_segmentation_file(case: CaseRecord) -> Path | None:
    """Select the D-028 target role for a case, without fallback."""

    role = {
        Cohort.UTSW: "tumorseg_FeTS",
        Cohort.UCSF_PDGM: "tumor_segmentation",
    }.get(case.cohort)
    if role is None:
        return None
    return case.segmentation_files.get(role)


def remap_labels(array: np.ndarray) -> np.ndarray:
    """Map BraTS labels to contiguous ``uint8`` classes.

    Raises:
        ValueError: if any label is not one of 0, 1, 2, or 4.  The error
            contains only the offending values and never a source path.
    """

    source = np.asarray(array)
    observed = np.unique(source)
    offending = [
        value.item() for value in observed if value.item() not in BRATS_TO_CLASS
    ]
    if offending:
        raise ValueError(f"unsupported BraTS segmentation label values: {offending}")

    remapped = np.zeros(source.shape, dtype=np.uint8)
    for label, class_id in BRATS_TO_CLASS.items():
        remapped[source == label] = class_id
    return remapped


def _load_nifti(path: Path) -> nib.Nifti1Image | nib.Nifti2Image:
    """Load a supported NIfTI image and make its type explicit to mypy."""

    image = nib.load(path)
    if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
        raise ValueError("preprocessing inputs must be NIfTI-1 or NIfTI-2 images")
    return image


def _t1ce_image(case: CaseRecord) -> nib.Nifti1Image | nib.Nifti2Image:
    """Load the case T1ce image for its shape and affine only."""

    try:
        t1ce_path = case.sequence_files[CanonicalSequence.T1CE]
    except KeyError as error:
        raise ValueError("case has no T1ce volume") from error
    return _load_nifti(t1ce_path)


def _grid_matches(
    mask: nib.Nifti1Image | nib.Nifti2Image,
    t1ce: nib.Nifti1Image | nib.Nifti2Image,
) -> bool:
    """Return whether two NIfTI spatial grids match within the fixed tolerance."""

    return mask.shape == t1ce.shape and np.allclose(
        np.asarray(mask.affine),
        np.asarray(t1ce.affine),
        atol=_GRID_TOLERANCE,
        rtol=0.0,
    )


def _class_counts(remapped: np.ndarray) -> dict[int, int]:
    """Count only classes present in the remapped target."""

    return {
        class_id: int(np.count_nonzero(remapped == class_id))
        for class_id in sorted(set(int(value) for value in np.unique(remapped)))
    }


def inspect_segmentation_target(case: CaseRecord) -> SegmentationTarget:
    """Inspect one selected mask and its T1ce header without writing a cache."""

    mask_path = select_segmentation_file(case)
    if mask_path is None:
        return SegmentationTarget(
            cohort=case.cohort,
            canonical_patient_id=case.canonical_patient_id,
            has_segmentation=False,
            class_voxel_counts={},
            grid_matches_t1ce=False,
        )

    mask_image = _load_nifti(mask_path)
    t1ce_image = _t1ce_image(case)
    grid_matches = _grid_matches(mask_image, t1ce_image)
    remapped = remap_labels(np.asarray(mask_image.dataobj))
    counts = _class_counts(remapped)
    return SegmentationTarget(
        cohort=case.cohort,
        canonical_patient_id=case.canonical_patient_id,
        has_segmentation=bool(np.any(remapped != 0)),
        class_voxel_counts=counts,
        grid_matches_t1ce=grid_matches,
    )


def _write_mask_outputs(output_dir: Path, case: CaseRecord, mask_path: Path) -> None:
    """Compute and write the lossless mask and its aggregate metadata."""

    mask_image = _load_nifti(mask_path)
    t1ce_image = _t1ce_image(case)
    if not _grid_matches(mask_image, t1ce_image):
        raise ValueError("segmentation mask grid does not match the case T1ce grid")

    remapped = remap_labels(np.asarray(mask_image.dataobj))
    counts = _class_counts(remapped)
    output_image = nib.Nifti1Image(remapped, np.asarray(mask_image.affine))
    output_image.header.set_data_dtype(np.uint8)
    output_image = reorient_to_ras(output_image)
    nib.save(output_image, output_dir / "mask.nii.gz")
    (output_dir / "meta.json").write_text(
        json.dumps(
            {
                "has_segmentation": bool(np.any(remapped != 0)),
                "class_voxel_counts": {
                    str(class_id): count for class_id, count in counts.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def run_mask_stage(
    cache: StageCache,
    case: CaseRecord,
    params: Mapping[str, object] | None = None,
) -> Path:
    """Run or reuse the content-addressed, lossless segmentation stage."""

    del params  # D-028 fixes the target vocabulary and stage parameters.
    mask_path = select_segmentation_file(case)
    if mask_path is None:
        raise ValueError("case has no selected segmentation target")
    try:
        t1ce_path = case.sequence_files[CanonicalSequence.T1CE]
    except KeyError as error:
        raise ValueError("case has no T1ce volume") from error

    input_keys = [hash_file(mask_path), hash_file(t1ce_path)]
    key = stage_cache_key(
        _MASK_STAGE,
        _MASK_STAGE_VERSION,
        _CACHE_LABEL_MAP,
        input_keys,
    )
    entry = cache.get_or_compute(
        _MASK_STAGE,
        key,
        lambda output_dir: _write_mask_outputs(output_dir, case, mask_path),
        stage_version=_MASK_STAGE_VERSION,
        params=_CACHE_LABEL_MAP,
        input_keys=input_keys,
    )
    return entry / "mask.nii.gz"


def _observed_label_set(target: SegmentationTarget) -> str | None:
    """Serialize an observed BraTS label set for aggregate frequency counts."""

    if not target.class_voxel_counts:
        return None
    labels = [
        _CLASS_TO_BRATS[class_id]
        for class_id, count in target.class_voxel_counts.items()
        if count > 0
    ]
    return ",".join(str(label) for label in sorted(labels))


def build_mask_report(
    targets: Iterable[SegmentationTarget],
) -> dict[str, object]:
    """Build an aggregate-only per-cohort segmentation-target report."""

    grouped: dict[Cohort, list[SegmentationTarget]] = {}
    for target in targets:
        grouped.setdefault(target.cohort, []).append(target)

    cohorts: dict[str, object] = {}
    for cohort in sorted(grouped, key=lambda item: item.value):
        cohort_targets = grouped[cohort]
        class_counts: Counter[int] = Counter()
        label_sets: Counter[str] = Counter()
        for target in cohort_targets:
            class_counts.update(target.class_voxel_counts)
            observed = _observed_label_set(target)
            if observed is not None:
                label_sets[observed] += 1
        cohorts[cohort.value] = {
            "cases": len(cohort_targets),
            "has_segmentation": {
                "true": sum(target.has_segmentation for target in cohort_targets),
                "false": sum(not target.has_segmentation for target in cohort_targets),
            },
            "grid_matches_t1ce": {
                "true": sum(target.grid_matches_t1ce for target in cohort_targets),
                "false": sum(not target.grid_matches_t1ce for target in cohort_targets),
            },
            "total_voxels_per_class": {
                str(class_id): class_counts[class_id]
                for class_id in sorted(class_counts)
            },
            "observed_label_sets": dict(sorted(label_sets.items())),
        }
    return {"schema_version": 1, "cohorts": cohorts}

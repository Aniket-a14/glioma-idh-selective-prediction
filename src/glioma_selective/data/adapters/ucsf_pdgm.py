"""UCSF-PDGM file discovery and sequence identification."""

from __future__ import annotations

from pathlib import Path

from glioma_selective.data.adapters._common import (
    CanonicalSequence,
    PatientFileInventory,
    discover_patient_files,
)
from glioma_selective.utils import paths

__all__ = ["cohort_root", "discover_files", "identify_sequence"]


_SEQUENCE_BY_SUFFIX: tuple[tuple[str, CanonicalSequence], ...] = (
    ("_T1c", CanonicalSequence.T1CE),
    ("_T1", CanonicalSequence.T1),
    ("_T2", CanonicalSequence.T2),
    ("_FLAIR", CanonicalSequence.FLAIR),
)


def cohort_root() -> Path:
    """Return the configured UCSF-PDGM external-data directory."""
    return paths.external_data_dir() / "ucsf_pdgm"


def _nifti_stem(file_path: Path) -> str | None:
    if file_path.name.endswith(".nii.gz"):
        return file_path.name[: -len(".nii.gz")]
    if file_path.name.endswith(".nii"):
        return file_path.name[: -len(".nii")]
    return None


def identify_sequence(file_path: Path) -> CanonicalSequence | None:
    """Identify a core sequence from a UCSF-PDGM filename suffix.

    UCSF-PDGM uses ``_T1c`` for the post-contrast T1 sequence. Files ending
    in ``_bias`` are corrected variants and are intentionally not selected as
    the raw core input; they remain present in ``PatientFileInventory.files``.
    """
    stem = _nifti_stem(file_path)
    if stem is None:
        return None
    return next(
        (sequence for suffix, sequence in _SEQUENCE_BY_SUFFIX if stem.endswith(suffix)),
        None,
    )


def discover_files(root: Path | None = None) -> tuple[PatientFileInventory, ...]:
    """Discover UCSF-PDGM patients and identify their core sequence files."""
    return discover_patient_files(
        root if root is not None else cohort_root(), identify_sequence
    )

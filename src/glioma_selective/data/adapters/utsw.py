"""UTSW-Glioma file discovery and sequence identification."""

from __future__ import annotations

from pathlib import Path

from glioma_selective.data.adapters._common import (
    CanonicalSequence,
    PatientFileInventory,
    discover_patient_files,
)
from glioma_selective.utils import paths

__all__ = ["cohort_root", "discover_files", "identify_sequence"]


_SEQUENCE_BY_FILENAME: dict[str, CanonicalSequence] = {
    "brain_t1.nii.gz": CanonicalSequence.T1,
    "brain_t1ce.nii.gz": CanonicalSequence.T1CE,
    "brain_t2.nii.gz": CanonicalSequence.T2,
    "brain_flair.nii.gz": CanonicalSequence.FLAIR,
}


def cohort_root() -> Path:
    """Return the configured UTSW-Glioma raw-data directory."""
    return paths.raw_data_dir() / "utsw"


def identify_sequence(file_path: Path) -> CanonicalSequence | None:
    """Identify a core sequence from an exact UTSW filename.

    Registered variants and segmentation files deliberately return ``None``.
    """
    return _SEQUENCE_BY_FILENAME.get(file_path.name)


def discover_files(root: Path | None = None) -> tuple[PatientFileInventory, ...]:
    """Discover UTSW patients and identify their core sequence files."""
    return discover_patient_files(
        root if root is not None else cohort_root(), identify_sequence
    )

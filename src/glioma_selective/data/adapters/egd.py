"""EGD file discovery skeleton.

EGD has not been downloaded while its data-use agreement is pending. Patient
directory discovery is therefore implemented, but sequence identification is
fail-closed until the real EGD inventory establishes its filename convention.
"""

from __future__ import annotations

from pathlib import Path

from glioma_selective.data.adapters._common import (
    CanonicalSequence,
    PatientFileInventory,
    SequenceIdentificationUnavailable,
    discover_patient_files,
)
from glioma_selective.utils import paths

__all__ = ["cohort_root", "discover_files", "identify_sequence"]


def cohort_root() -> Path:
    """Return the configured EGD external-data directory."""
    return paths.external_data_dir() / "egd"


def identify_sequence(_file_path: Path) -> CanonicalSequence | None:
    """Identify an EGD sequence once its real filename convention is known.

    No EGD filename convention is guessed before the DUA-governed data is
    available. This prevents a later adapter from silently selecting the
    wrong modality.
    """
    raise SequenceIdentificationUnavailable(
        "EGD sequence identification is unavailable until the real EGD "
        "filename inventory is available"
    )


def discover_files(root: Path | None = None) -> tuple[PatientFileInventory, ...]:
    """Discover EGD patient directories without guessing their sequences."""
    return discover_patient_files(root if root is not None else cohort_root())

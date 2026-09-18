"""Shared contracts for cohort adapters.

The adapters only inspect directory entries and NIfTI filename suffixes. They
do not open image files or infer a missing sequence from another file.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType

__all__ = [
    "CORE_SEQUENCES",
    "CanonicalSequence",
    "PatientFileInventory",
    "SequenceIdentifier",
    "SequenceIdentificationUnavailable",
    "discover_patient_files",
]


class CanonicalSequence(StrEnum):
    """The four structural MRI sequences used by the study."""

    T1 = "T1"
    T1CE = "T1ce"
    T2 = "T2"
    FLAIR = "FLAIR"


CORE_SEQUENCES: tuple[CanonicalSequence, ...] = (
    CanonicalSequence.T1,
    CanonicalSequence.T1CE,
    CanonicalSequence.T2,
    CanonicalSequence.FLAIR,
)


class SequenceIdentificationUnavailable(RuntimeError):
    """Raised when a cohort's filename convention is not yet known."""


SequenceIdentifier = Callable[[Path], CanonicalSequence | None]


@dataclass(frozen=True)
class PatientFileInventory:
    """Files discovered for one patient directory.

    ``files`` contains every regular file in the patient directory. The
    ``sequence_files`` mapping contains only files identified as one of the
    four canonical sequences. A missing key is a reported missing modality;
    no file is synthesized or substituted.
    """

    patient_id: str
    files: tuple[Path, ...]
    sequence_files: Mapping[CanonicalSequence, Path]

    @property
    def missing_sequences(self) -> tuple[CanonicalSequence, ...]:
        """Return canonical sequences without an identified file."""
        return tuple(
            sequence
            for sequence in CORE_SEQUENCES
            if sequence not in self.sequence_files
        )

    @property
    def has_complete_core_sequences(self) -> bool:
        """Whether all four canonical sequences were identified."""
        return not self.missing_sequences


def discover_patient_files(
    root: Path,
    identify_sequence: SequenceIdentifier | None = None,
) -> tuple[PatientFileInventory, ...]:
    """Discover patient directories and their regular files under ``root``.

    Patient identifiers are returned exactly as directory names. Callers that
    persist identifiers must apply the project's governance-tier mapping
    before writing any manifest or other committed artifact.

    Args:
        root: Cohort directory whose immediate subdirectories are patients.
        identify_sequence: Optional cohort-specific filename mapper. When it
            is omitted, files are inventoried without sequence identification;
            this is used for a cohort whose naming convention is not available
            yet.

    Raises:
        FileNotFoundError: If ``root`` does not exist.
        NotADirectoryError: If ``root`` is not a directory.
        ValueError: If two files identify as the same canonical sequence.
    """
    if not root.exists():
        raise FileNotFoundError(root)
    if not root.is_dir():
        raise NotADirectoryError(root)

    inventories: list[PatientFileInventory] = []
    patient_directories = sorted(
        (entry for entry in root.iterdir() if entry.is_dir()),
        key=lambda entry: entry.name,
    )
    for patient_directory in patient_directories:
        files = tuple(
            sorted(
                (entry for entry in patient_directory.iterdir() if entry.is_file()),
                key=lambda entry: entry.name,
            )
        )
        sequence_files: dict[CanonicalSequence, Path] = {}
        if identify_sequence is not None:
            for file_path in files:
                sequence = identify_sequence(file_path)
                if sequence is None:
                    continue
                if sequence in sequence_files:
                    previous = sequence_files[sequence]
                    raise ValueError(
                        "Multiple files identified as "
                        f"{sequence.value} for patient {patient_directory.name}: "
                        f"{previous.name} and {file_path.name}"
                    )
                sequence_files[sequence] = file_path

        inventories.append(
            PatientFileInventory(
                patient_id=patient_directory.name,
                files=files,
                sequence_files=MappingProxyType(sequence_files),
            )
        )
    return tuple(inventories)

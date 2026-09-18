"""Aggregate naturally missing MRI sequences from raw cohort inventories.

This module reports naturally occurring missingness: a canonical sequence was
not identified in the raw download for a patient directory. It does not model
the simulated missing-modality conditions used later in Phase 08, where a
sequence is deliberately dropped from an otherwise complete study.

The report is aggregate-only. Patient identifiers are intentionally not
returned so that a derived operational report cannot become a committed raw-ID
roster by accident.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from glioma_selective.data.adapters._common import (
    CORE_SEQUENCES,
    PatientFileInventory,
)

__all__ = ["build_cohort_report", "build_report"]

_SCHEMA_VERSION = 1


def build_cohort_report(
    inventories: Sequence[PatientFileInventory],
) -> dict[str, object]:
    """Aggregate complete and naturally incomplete patients in one cohort.

    ``inventories`` must come from a cohort adapter's ``discover_files``. A
    patient contributes once to ``incomplete_patient_count`` and once to each
    sequence count in ``missing_sequence_patient_counts``. The latter counts
    are therefore not required to sum to the incomplete-patient count when a
    patient is missing multiple sequences.
    """

    missing_sequence_counts: Counter[str] = Counter()
    missing_combination_counts: Counter[str] = Counter()
    complete_patient_count = 0

    for inventory in inventories:
        missing_sequences = inventory.missing_sequences
        if not missing_sequences:
            complete_patient_count += 1
            continue

        for sequence in missing_sequences:
            missing_sequence_counts[sequence.value] += 1
        combination = "+".join(sequence.value for sequence in missing_sequences)
        missing_combination_counts[combination] += 1

    patient_count = len(inventories)
    incomplete_patient_count = patient_count - complete_patient_count
    return {
        "patient_count": patient_count,
        "complete_patient_count": complete_patient_count,
        "incomplete_patient_count": incomplete_patient_count,
        "missing_sequence_patient_counts": {
            sequence.value: missing_sequence_counts[sequence.value]
            for sequence in CORE_SEQUENCES
        },
        "missing_sequence_combinations": dict(
            sorted(missing_combination_counts.items())
        ),
    }


def build_report(
    cohort_inventories: Mapping[str, Sequence[PatientFileInventory]],
) -> dict[str, object]:
    """Build an aggregate-only report for naturally missing raw sequences.

    The report explicitly labels its scope as naturally occurring raw-download
    missingness. It must not be interpreted as the Phase 08 simulated
    missing-modality evaluation, which starts from complete studies and drops
    sequences deliberately.
    """

    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "missingness": {
            "type": "naturally_occurring",
            "source": "raw_download",
            "simulated": False,
            "description": (
                "Sequences absent from the raw cohort download; no sequence "
                "was deliberately dropped for this inventory."
            ),
        },
        "cohorts": {
            cohort_name: build_cohort_report(inventories)
            for cohort_name, inventories in sorted(cohort_inventories.items())
        },
    }

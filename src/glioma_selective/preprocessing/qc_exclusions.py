"""Extract explicit patient-level QC exclusion decisions."""

from __future__ import annotations

from glioma_selective.preprocessing.status import PreprocessingStatusManifest

__all__ = ["qc_exclusion_records"]


def qc_exclusion_records(
    status_manifest: PreprocessingStatusManifest,
) -> tuple[tuple[str, str, tuple[str, ...]], ...]:
    """Return deterministic ``(cohort, patient_id, reasons)`` QC records.

    A failed automated verification without a recorded decision is unresolved
    and therefore raises before any records are returned.  The error reports
    only an aggregate count so patient IDs never enter logs or messages.
    """

    if not isinstance(status_manifest, PreprocessingStatusManifest):
        raise TypeError("status_manifest must be a PreprocessingStatusManifest")
    unresolved_count = sum(
        case.verification_status == "failed" and not case.qc_reasons
        for case in status_manifest.cases.values()
    )
    if unresolved_count:
        raise ValueError(
            f"{unresolved_count} automated QC failures have no exclusion decision"
        )
    return tuple(
        (case.cohort, case.patient_id, tuple(case.qc_reasons))
        for _, case in sorted(status_manifest.cases.items())
        if case.qc_reasons
    )

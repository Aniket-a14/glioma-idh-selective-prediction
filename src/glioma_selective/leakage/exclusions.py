"""Build the UCSF-PDGM exclusion list from the T03.4 overlap audit.

The exclusion roster is a raw-identifier-tier derived artifact.  It is written
to the configured manifests directory for operational use and must not be
committed or published.  The aggregate summary contains counts only and is
safe to retain in tracked research documentation.

This exclusion covers the BraTS-2021 training and validation crosswalk that is
available locally.  The BraTS-2021 challenge test set is sequestered and is
not covered; the same caveat is carried by the T03.4 overlap audit.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Final, cast

from glioma_selective.data.adapters import ucsf_pdgm
from glioma_selective.leakage.id_normalization import (
    Cohort,
    IdentifierNormalizationError,
    normalize_identifier,
    normalize_ucsf_pdgm_id,
)
from glioma_selective.leakage.overlap_audit import (
    BRATS_TEST_SET_CAVEAT,
    build_real_overlap_audit,
)
from glioma_selective.utils import paths

__all__ = [
    "BRATS_EXCLUSION_REASON",
    "ExclusionReportError",
    "build_brats_exclusion_report",
    "build_real_brats_exclusion_report",
    "build_brats_exclusion_summary",
    "verify_post_exclusion_no_brats_overlap",
    "write_brats_exclusion_report",
    "write_brats_exclusion_summary",
]


BRATS_EXCLUSION_REASON: Final[str] = "overlap:brats2021"
_PAIR_KEY: Final[str] = "ucsf_pdgm|brats2021"
_REPORT_VERSION: Final[int] = 1
_UCSF_FOLLOWUP_RE = re.compile(
    r"(UCSF-PDGM-\d{3,4})_FU[A-Za-z0-9]+_nifti", re.IGNORECASE
)


class ExclusionReportError(RuntimeError):
    """Raised when an overlap-derived exclusion report is malformed."""


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ExclusionReportError(f"{context} must be a JSON object")
    return cast(Mapping[str, object], value)


def _pair_rows(overlap_details: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    """Extract and normalize the authoritative T03.4 UCSF/BraTS pairs."""

    pairs_by_key = _mapping(overlap_details.get("pairs"), "overlap_details.pairs")
    raw_pairs = pairs_by_key.get(_PAIR_KEY)
    if not isinstance(raw_pairs, list | tuple):
        raise ExclusionReportError(
            f"overlap_details.pairs[{_PAIR_KEY!r}] must be an array"
        )

    normalized: dict[str, str] = {}
    for index, raw_pair in enumerate(raw_pairs):
        if not isinstance(raw_pair, list | tuple) or len(raw_pair) != 2:
            raise ExclusionReportError(
                f"overlap_details.pairs[{_PAIR_KEY!r}][{index}] must contain two IDs"
            )
        raw_source, raw_brats = raw_pair
        if not isinstance(raw_source, str) or not isinstance(raw_brats, str):
            raise ExclusionReportError(
                f"overlap_details.pairs[{_PAIR_KEY!r}][{index}] IDs must be strings"
            )
        try:
            source_id = normalize_ucsf_pdgm_id(raw_source)
            brats_id = normalize_identifier(raw_brats, Cohort.BRATS_2021)
        except IdentifierNormalizationError as error:
            raise ExclusionReportError(
                f"invalid UCSF-PDGM/BraTS pair at index {index}"
            ) from error
        if source_id in normalized:
            raise ExclusionReportError(
                f"source patient appears in more than one UCSF/BraTS pair: {source_id}"
            )
        normalized[source_id] = brats_id
    return tuple(sorted(normalized.items()))


def _report_exclusion_ids(report: Mapping[str, object]) -> frozenset[str]:
    """Validate and return normalized source IDs from a local roster report."""

    raw_exclusions = report.get("exclusions")
    if not isinstance(raw_exclusions, list | tuple):
        raise ExclusionReportError("exclusion report must contain an exclusions array")
    normalized: set[str] = set()
    for index, raw_entry in enumerate(raw_exclusions):
        entry = _mapping(raw_entry, f"exclusions[{index}]")
        patient_id = entry.get("patient_id")
        reason = entry.get("reason")
        if not isinstance(patient_id, str) or reason != BRATS_EXCLUSION_REASON:
            raise ExclusionReportError(
                f"exclusions[{index}] must contain a patient_id and "
                f"{BRATS_EXCLUSION_REASON}"
            )
        try:
            normalized_id = normalize_ucsf_pdgm_id(patient_id)
        except IdentifierNormalizationError as error:
            raise ExclusionReportError(
                f"exclusions[{index}] contains an invalid UCSF-PDGM ID"
            ) from error
        if normalized_id in normalized:
            raise ExclusionReportError(
                f"exclusion report contains a duplicate patient: {normalized_id}"
            )
        normalized.add(normalized_id)
    return frozenset(normalized)


def _normalize_ucsf_inventory_id(raw_id: str) -> str:
    """Normalize a UCSF directory ID, including the observed follow-up wrapper."""

    try:
        return normalize_ucsf_pdgm_id(raw_id)
    except IdentifierNormalizationError:
        match = _UCSF_FOLLOWUP_RE.fullmatch(raw_id)
        if match is None:
            raise
        return normalize_ucsf_pdgm_id(match.group(1))


def build_brats_exclusion_report(
    overlap_details: Mapping[str, object],
) -> dict[str, object]:
    """Build the local UCSF-PDGM roster from T03.4's derived detail report.

    Each excluded source patient gets the machine-readable reason
    ``overlap:brats2021``.  Only the locally available BraTS-2021
    training+validation crosswalk is represented; the sequestered challenge
    test set remains outside this exclusion result.
    """

    pairs = _pair_rows(overlap_details)
    exclusions = [
        {"patient_id": source_id, "reason": BRATS_EXCLUSION_REASON}
        for source_id, _ in pairs
    ]
    report: dict[str, object] = {
        "report_version": _REPORT_VERSION,
        "cohort": Cohort.UCSF_PDGM.value,
        "basis": "t03.4_authoritative_ucsf_pdgm_brats_pairs",
        "brats_coverage_caveat": BRATS_TEST_SET_CAVEAT,
        "excluded_patient_count": len(exclusions),
        "reason_counts": {BRATS_EXCLUSION_REASON: len(exclusions)},
        "exclusions": exclusions,
    }
    return report


def build_brats_exclusion_summary(
    exclusion_report: Mapping[str, object],
) -> dict[str, object]:
    """Return a roster-free summary suitable for tracked documentation."""

    exclusions = _report_exclusion_ids(exclusion_report)
    reason_counts = exclusion_report.get("reason_counts")
    if not isinstance(reason_counts, Mapping):
        raise ExclusionReportError("exclusion report must contain reason_counts")
    return {
        "report_version": _REPORT_VERSION,
        "cohort": Cohort.UCSF_PDGM.value,
        "excluded_patient_count": len(exclusions),
        "reason_counts": dict(reason_counts),
        "brats_coverage_caveat": BRATS_TEST_SET_CAVEAT,
    }


def verify_post_exclusion_no_brats_overlap(
    ucsf_patient_ids: Iterable[str],
    exclusion_report: Mapping[str, object],
    overlap_details: Mapping[str, object],
) -> dict[str, object]:
    """Verify the remaining UCSF inventory has no T03.4 BraTS overlap.

    ``ucsf_patient_ids`` is normally read from the real UCSF-PDGM directory
    inventory.  The check compares normalized source IDs directly and also
    requires the exclusion roster to equal the authoritative T03.4 source-ID
    side of the pair list, so ``501 - 293`` cannot mask a wrong roster.
    """

    raw_inventory = tuple(ucsf_patient_ids)
    try:
        normalized_inventory_entries = tuple(
            _normalize_ucsf_inventory_id(patient_id) for patient_id in raw_inventory
        )
    except IdentifierNormalizationError as error:
        raise ExclusionReportError(
            "real UCSF-PDGM inventory contains an invalid patient ID"
        ) from error
    excluded_ids = _report_exclusion_ids(exclusion_report)
    pair_sources = frozenset(source_id for source_id, _ in _pair_rows(overlap_details))
    if excluded_ids != pair_sources:
        raise ExclusionReportError(
            "exclusion roster does not equal the T03.4 UCSF source-ID pair set"
        )
    normalized_inventory = frozenset(normalized_inventory_entries)
    if not excluded_ids.issubset(normalized_inventory):
        raise ExclusionReportError(
            "exclusion roster contains a patient absent from the UCSF inventory"
        )

    remaining_entries = tuple(
        patient_id
        for patient_id in normalized_inventory_entries
        if patient_id not in excluded_ids
    )
    remaining = frozenset(remaining_entries)
    residual_overlap = remaining & pair_sources
    if residual_overlap:
        raise ExclusionReportError(
            "post-exclusion UCSF-PDGM inventory still contains BraTS overlap"
        )
    return {
        "status": "verified",
        "ucsf_pdgm_input_patient_count": len(raw_inventory),
        "ucsf_pdgm_input_unique_patient_count": len(normalized_inventory),
        "excluded_patient_count": len(excluded_ids),
        "ucsf_pdgm_remaining_patient_count": len(remaining_entries),
        "ucsf_pdgm_remaining_unique_patient_count": len(remaining),
        "remaining_brats_overlap_count": len(residual_overlap),
    }


def _load_real_ucsf_source_ids() -> tuple[str, ...]:
    """Load only the source-ID column from the real UCSF metadata file."""

    metadata_path = paths.external_data_dir() / "UCSF-PDGM-metadata_v2.csv"
    try:
        with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or "ID" not in reader.fieldnames:
                raise ExclusionReportError("UCSF metadata is missing its ID column")
            source_ids = tuple(
                value.strip()
                for row in reader
                for value in [row.get("ID")]
                if value is not None and value.strip()
            )
    except OSError as error:
        raise ExclusionReportError(
            f"cannot read the UCSF metadata source: {metadata_path}"
        ) from error
    if not source_ids:
        raise ExclusionReportError("UCSF metadata contains no source IDs")
    return source_ids


def build_real_brats_exclusion_report() -> dict[str, object]:
    """Build and verify the real local UCSF-PDGM/BraTS exclusion roster."""

    _, overlap_details = build_real_overlap_audit()
    report = build_brats_exclusion_report(overlap_details)
    metadata_verification = verify_post_exclusion_no_brats_overlap(
        _load_real_ucsf_source_ids(),
        report,
        overlap_details,
    )
    directory_verification = verify_post_exclusion_no_brats_overlap(
        (item.patient_id for item in ucsf_pdgm.discover_files()),
        report,
        overlap_details,
    )
    report["post_exclusion_verification"] = metadata_verification
    report["image_directory_verification"] = directory_verification
    return report


def _write_json(report: Mapping[str, object], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


def write_brats_exclusion_report(
    report: Mapping[str, object], output_path: Path | None = None
) -> Path:
    """Write the raw-identifier-tier roster through the configured paths."""

    destination = output_path or (
        paths.manifests_dir() / "ucsf_pdgm_brats_exclusions.json"
    )
    return _write_json(report, destination)


def write_brats_exclusion_summary(
    report: Mapping[str, object], output_path: Path | None = None
) -> Path:
    """Write only the roster-free aggregate exclusion summary."""

    destination = output_path or (
        paths.manifests_dir() / "ucsf_pdgm_brats_exclusions_summary.json"
    )
    return _write_json(build_brats_exclusion_summary(report), destination)

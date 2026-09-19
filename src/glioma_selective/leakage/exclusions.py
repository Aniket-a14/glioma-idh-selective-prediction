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

import copy
import csv
import json
import re
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Final, cast

from glioma_selective.data.adapters import ucsf_pdgm
from glioma_selective.leakage.id_normalization import (
    Cohort,
    IdentifierNormalizationError,
    normalize_identifier,
    normalize_ucsf_pdgm_id,
    normalize_utsw_id,
)
from glioma_selective.leakage.overlap_audit import (
    BRATS_TEST_SET_CAVEAT,
    build_real_overlap_audit,
)
from glioma_selective.utils import paths

__all__ = [
    "BRATS_EXCLUSION_REASON",
    "FOLLOWUP_TIMEPOINT_REASON",
    "IDH_UNAVAILABLE_REASON",
    "NO_IMAGING_AVAILABLE_REASON",
    "QC_CATEGORIES",
    "ExclusionReportError",
    "append_qc_exclusions",
    "build_exclusion_manifest",
    "build_followup_timepoint_selection_record",
    "build_brats_exclusion_report",
    "build_real_exclusion_manifest",
    "build_real_followup_timepoint_selection_record",
    "build_real_brats_exclusion_report",
    "build_brats_exclusion_summary",
    "verify_post_exclusion_no_brats_overlap",
    "write_exclusion_manifest",
    "write_followup_timepoint_selection_record",
    "write_brats_exclusion_report",
    "write_brats_exclusion_summary",
]


BRATS_EXCLUSION_REASON: Final[str] = "overlap:brats2021"
IDH_UNAVAILABLE_REASON: Final[str] = "label:idh_unavailable"
NO_IMAGING_AVAILABLE_REASON: Final[str] = "no_imaging_available"
FOLLOWUP_TIMEPOINT_REASON: Final[str] = "duplicate:followup_timepoint"
QC_CATEGORIES: Final[tuple[str, ...]] = (
    "registration-failed",
    "skullstrip-over",
    "skullstrip-under",
    "n4-artifact",
    "orientation-wrong",
    "corrupt",
    "modality-mislabelled",
)
_QC_REASON_PREFIX: Final[str] = "qc:"
_QC_COHORT_NORMALIZERS: Final[dict[str, Callable[[str], str]]] = {
    Cohort.UTSW.value: normalize_utsw_id,
    Cohort.UCSF_PDGM.value: normalize_ucsf_pdgm_id,
}
_PAIR_KEY: Final[str] = "ucsf_pdgm|brats2021"
_REPORT_VERSION: Final[int] = 1
_MANIFEST_VERSION: Final[int] = 1
_UCSF_FOLLOWUP_RE = re.compile(
    r"(UCSF-PDGM-\d{3,4})_FU[A-Za-z0-9]+_nifti", re.IGNORECASE
)
_UCSF_BASE_DIRECTORY_RE = re.compile(r"(UCSF-PDGM-\d{3,4})_nifti", re.IGNORECASE)


class ExclusionReportError(RuntimeError):
    """Raised when an overlap-derived exclusion report is malformed."""


def _qc_cohort_and_id(cohort: object, patient_id: object) -> tuple[str, str]:
    """Validate and canonicalize a QC exclusion's cohort and patient ID."""

    if not isinstance(cohort, str) or cohort not in _QC_COHORT_NORMALIZERS:
        raise ExclusionReportError(f"unknown QC exclusion cohort: {cohort!r}")
    if not isinstance(patient_id, str):
        raise ExclusionReportError("QC exclusion patient_id must be a string")
    try:
        normalized_id = _QC_COHORT_NORMALIZERS[cohort](patient_id)
    except (IdentifierNormalizationError, TypeError) as error:
        raise ExclusionReportError(
            f"invalid QC exclusion patient ID for cohort {cohort}"
        ) from error
    return cohort, normalized_id


def _qc_reason_values(reasons: object) -> tuple[str, ...]:
    """Validate, de-duplicate, and sort one QC reason collection."""

    if isinstance(reasons, str) or not isinstance(reasons, Iterable):
        raise ExclusionReportError("QC exclusion reasons must be a non-empty tuple")
    values = tuple(reasons)
    if not values:
        raise ExclusionReportError("QC exclusion reasons must not be empty")
    valid_reasons = {f"{_QC_REASON_PREFIX}{category}" for category in QC_CATEGORIES}
    if any(
        not isinstance(reason, str)
        or not reason.startswith(_QC_REASON_PREFIX)
        or reason not in valid_reasons
        for reason in values
    ):
        raise ExclusionReportError("QC exclusion contains an unknown or non-qc reason")
    return tuple(sorted(set(values)))


def _increment_reason_counts(
    report: Mapping[str, object], reasons: Iterable[str], context: str
) -> dict[str, int]:
    """Copy and increment a manifest reason-count mapping."""

    raw_counts = report.get("reason_counts")
    if not isinstance(raw_counts, Mapping):
        raise ExclusionReportError(f"{context}.reason_counts must be an object")
    counts: dict[str, int] = {}
    for reason, count in raw_counts.items():
        if (
            not isinstance(reason, str)
            or isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
        ):
            raise ExclusionReportError(f"{context}.reason_counts is malformed")
        counts[reason] = count
    for reason in reasons:
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def append_qc_exclusions(
    manifest: Mapping[str, object],
    qc_exclusions: Iterable[tuple[str, str, tuple[str, ...]]],
) -> dict[str, object]:
    """Return a deep-copied Phase 03 manifest with QC exclusions appended.

    Patient IDs are canonicalized with the Phase 03 cohort normalizers.  QC
    reasons are represented once per patient, joined with ``+`` in sorted
    order, while the aggregate reason counts count each category separately.
    The pre-QC accounting checks are copied without modification.
    """

    result = copy.deepcopy(dict(manifest))
    raw_rows = result.get("exclusions")
    if not isinstance(raw_rows, list):
        raise ExclusionReportError("manifest.exclusions must be an array")
    raw_cohorts = result.get("cohorts")
    if not isinstance(raw_cohorts, Mapping):
        raise ExclusionReportError("manifest.cohorts must be an object")
    cohorts = {str(key): value for key, value in raw_cohorts.items()}

    existing_ids: set[tuple[str, str]] = set()
    for index, raw_row in enumerate(raw_rows):
        if not isinstance(raw_row, Mapping):
            raise ExclusionReportError(
                f"manifest.exclusions[{index}] must be an object"
            )
        cohort, patient_id = _qc_cohort_and_id(
            raw_row.get("cohort"), raw_row.get("patient_id")
        )
        key = (cohort, patient_id)
        if key in existing_ids:
            raise ExclusionReportError(
                f"manifest.exclusions contains duplicate patient in {cohort}"
            )
        existing_ids.add(key)

    normalized_records: list[tuple[str, str, tuple[str, ...]]] = []
    input_ids: set[tuple[str, str]] = set()
    for record in qc_exclusions:
        if not isinstance(record, tuple) or len(record) != 3:
            raise ExclusionReportError(
                "each QC exclusion must be a (cohort, patient_id, reasons) tuple"
            )
        cohort, patient_id = _qc_cohort_and_id(record[0], record[1])
        reasons = _qc_reason_values(record[2])
        key = (cohort, patient_id)
        if key in input_ids:
            raise ExclusionReportError(
                "QC exclusions contain a duplicate patient within the input"
            )
        if key in existing_ids:
            raise ExclusionReportError(
                "QC exclusion patient is already present in exclusions"
            )
        input_ids.add(key)
        normalized_records.append((cohort, patient_id, reasons))

    if not normalized_records:
        result["generated_by"] = "T03.10 exclusion manifest + T04.12 QC exclusions"
        result["qc_exclusion_count"] = 0
        result["accounting_checks_scope"] = "pre-QC"
        result["cohorts"] = {
            cohort: (
                {
                    **value,
                    "qc_excluded_patient_count": value.get(
                        "qc_excluded_patient_count", 0
                    ),
                }
                if isinstance(value, Mapping)
                else value
            )
            for cohort, value in cohorts.items()
        }
        return result

    top_level_excluded = result.get("excluded_patient_count")
    if (
        isinstance(top_level_excluded, bool)
        or not isinstance(top_level_excluded, int)
        or top_level_excluded < 0
    ):
        raise ExclusionReportError("manifest.excluded_patient_count is malformed")
    top_level_reasons = _increment_reason_counts(result, (), "manifest")

    records_by_cohort: dict[str, list[tuple[str, ...]]] = {}
    for cohort, _, reasons in normalized_records:
        records_by_cohort.setdefault(cohort, []).append(reasons)

    cohort_updates: dict[str, dict[str, object]] = {}
    for cohort, cohort_reasons in records_by_cohort.items():
        raw_report = cohorts.get(cohort)
        if not isinstance(raw_report, Mapping):
            raise ExclusionReportError(f"manifest.cohorts.{cohort} must be an object")
        report = dict(raw_report)
        retained = report.get("retained_patient_count")
        excluded = report.get("excluded_patient_count")
        prior_qc_count = report.get("qc_excluded_patient_count", 0)
        if (
            isinstance(retained, bool)
            or not isinstance(retained, int)
            or retained < 0
            or isinstance(excluded, bool)
            or not isinstance(excluded, int)
            or excluded < 0
            or isinstance(prior_qc_count, bool)
            or not isinstance(prior_qc_count, int)
            or prior_qc_count < 0
        ):
            raise ExclusionReportError(
                f"manifest.cohorts.{cohort} counts are malformed"
            )
        if retained < len(cohort_reasons):
            raise ExclusionReportError(
                f"QC exclusions would make the {cohort} retained count negative"
            )
        updated = report
        updated["retained_patient_count"] = retained - len(cohort_reasons)
        updated["excluded_patient_count"] = excluded + len(cohort_reasons)
        updated["reason_counts"] = _increment_reason_counts(
            updated,
            (reason for reasons in cohort_reasons for reason in reasons),
            f"manifest.cohorts.{cohort}",
        )
        updated["qc_excluded_patient_count"] = prior_qc_count + len(cohort_reasons)
        cohort_updates[cohort] = updated

    qc_rows = [
        {"cohort": cohort, "patient_id": patient_id, "reason": "+".join(reasons)}
        for cohort, patient_id, reasons in sorted(normalized_records)
    ]
    result["exclusions"] = raw_rows + qc_rows
    result["excluded_patient_count"] = top_level_excluded + len(normalized_records)
    for _, _, reasons in normalized_records:
        top_level_reasons = _increment_reason_counts(
            {"reason_counts": top_level_reasons}, reasons, "manifest"
        )
    result["reason_counts"] = top_level_reasons
    updated_cohorts: dict[str, object] = {
        cohort: cohort_updates.get(cohort, value) for cohort, value in cohorts.items()
    }
    for cohort, report in cohorts.items():
        if cohort not in cohort_updates:
            if not isinstance(report, Mapping):
                raise ExclusionReportError(
                    f"manifest.cohorts.{cohort} must be an object"
                )
            report_copy = dict(report)
            prior_qc_count = report_copy.get("qc_excluded_patient_count", 0)
            if (
                isinstance(prior_qc_count, bool)
                or not isinstance(prior_qc_count, int)
                or prior_qc_count < 0
            ):
                raise ExclusionReportError(
                    f"manifest.cohorts.{cohort}.qc_excluded_patient_count is malformed"
                )
            report_copy["qc_excluded_patient_count"] = prior_qc_count
            updated_cohorts[cohort] = report_copy
    result["cohorts"] = updated_cohorts
    result["generated_by"] = "T03.10 exclusion manifest + T04.12 QC exclusions"
    result["qc_exclusion_count"] = len(normalized_records)
    result["accounting_checks_scope"] = "pre-QC"
    return result


def _normalize_unique(
    raw_ids: Iterable[str],
    normalizer: Callable[[str], str],
    context: str,
) -> tuple[str, ...]:
    """Normalize an identifier inventory and reject duplicate canonical IDs."""

    normalized: list[str] = []
    seen: set[str] = set()
    for index, raw_id in enumerate(raw_ids):
        try:
            identifier = normalizer(raw_id)
        except (IdentifierNormalizationError, TypeError) as error:
            raise ExclusionReportError(
                f"{context}[{index}] is not a valid patient identifier"
            ) from error
        if identifier in seen:
            raise ExclusionReportError(
                f"{context} contains duplicate patient: {identifier}"
            )
        seen.add(identifier)
        normalized.append(identifier)
    return tuple(sorted(normalized))


def _ucsf_inventory_groups(
    raw_directory_ids: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    """Group raw UCSF directory names by their canonical patient ID."""

    grouped: dict[str, list[str]] = {}
    seen_raw: set[str] = set()
    for index, raw_id in enumerate(raw_directory_ids):
        if not isinstance(raw_id, str) or not raw_id:
            raise ExclusionReportError(
                f"ucsf_directory_ids[{index}] must be a non-empty string"
            )
        if raw_id in seen_raw:
            raise ExclusionReportError(
                f"ucsf_directory_ids contains duplicate directory: {raw_id}"
            )
        seen_raw.add(raw_id)
        try:
            normalized_id = _normalize_ucsf_inventory_id(raw_id)
        except IdentifierNormalizationError as error:
            raise ExclusionReportError(
                f"ucsf_directory_ids[{index}] is not a valid UCSF directory ID"
            ) from error
        grouped.setdefault(normalized_id, []).append(raw_id)
    return {
        patient_id: tuple(sorted(directory_ids))
        for patient_id, directory_ids in sorted(grouped.items())
    }


def build_followup_timepoint_selection_record(
    ucsf_directory_ids: Iterable[str],
) -> dict[str, object]:
    """Record UCSF baseline/follow-up directory choices separately.

    This is a directory-selection record, not a patient-level exclusion
    roster.  Every observed ``_FU..._nifti`` directory must have exactly one
    base ``_nifti`` directory for the same normalized patient.  The follow-up
    directory is omitted from later preprocessing while the baseline remains
    the retained scan.
    """

    groups = _ucsf_inventory_groups(ucsf_directory_ids)
    selections: list[dict[str, object]] = []
    for patient_id, directories in groups.items():
        base_directories = tuple(
            directory
            for directory in directories
            if _UCSF_BASE_DIRECTORY_RE.fullmatch(directory) is not None
        )
        followup_directories = tuple(
            directory
            for directory in directories
            if _UCSF_FOLLOWUP_RE.fullmatch(directory) is not None
        )
        if len(directories) != len(base_directories) + len(followup_directories):
            raise ExclusionReportError(
                f"unclassified UCSF directory for patient {patient_id}"
            )
        if followup_directories and len(base_directories) != 1:
            raise ExclusionReportError(
                f"follow-up patient {patient_id} must have exactly one base directory"
            )
        for followup_directory in followup_directories:
            selections.append(
                {
                    "patient_id": patient_id,
                    "retained_directory": base_directories[0],
                    "excluded_directory": followup_directory,
                    "reason": FOLLOWUP_TIMEPOINT_REASON,
                }
            )

    return {
        "record_version": _MANIFEST_VERSION,
        "cohort": Cohort.UCSF_PDGM.value,
        "basis": "d021_baseline_retained_followup_timepoint_excluded",
        "selection_count": len(selections),
        "reason": FOLLOWUP_TIMEPOINT_REASON,
        "directory_accounting": {
            "raw_directory_count": sum(
                len(directories) for directories in groups.values()
            ),
            "directory_backed_patient_count": len(groups),
            "baseline_directory_count": len(groups),
            "followup_directory_count": len(selections),
        },
        "selections": selections,
    }


def build_exclusion_manifest(
    *,
    utsw_patient_ids: Iterable[str],
    utsw_idh_unavailable_ids: Iterable[str],
    ucsf_metadata_ids: Iterable[str],
    ucsf_directory_ids: Iterable[str],
    brats_exclusion_report: Mapping[str, object],
) -> dict[str, object]:
    """Build the Phase 03 patient-level exclusion manifest.

    UCSF accounting intentionally keeps two bases separate: metadata patients
    partition into directory-backed and no-imaging groups, while the retained
    imaging cohort subtracts BraTS overlap only from the directory-backed
    group.  The returned checks assert both forms of ``202`` agree.
    """

    utsw_ids = _normalize_unique(
        utsw_patient_ids, normalize_utsw_id, "utsw_patient_ids"
    )
    utsw_idh_unavailable = _normalize_unique(
        utsw_idh_unavailable_ids,
        normalize_utsw_id,
        "utsw_idh_unavailable_ids",
    )
    utsw_set = frozenset(utsw_ids)
    utsw_missing_set = frozenset(utsw_idh_unavailable)
    if not utsw_missing_set.issubset(utsw_set):
        raise ExclusionReportError(
            "UTSW IDH-unavailable IDs must belong to the UTSW patient inventory"
        )

    raw_ucsf_directory_ids = tuple(ucsf_directory_ids)
    ucsf_ids = _normalize_unique(
        ucsf_metadata_ids, normalize_ucsf_pdgm_id, "ucsf_metadata_ids"
    )
    ucsf_set = frozenset(ucsf_ids)
    directory_groups = _ucsf_inventory_groups(raw_ucsf_directory_ids)
    directory_backed = frozenset(directory_groups)
    no_imaging = ucsf_set - directory_backed
    brats_ids = _report_exclusion_ids(brats_exclusion_report)
    if not brats_ids.issubset(ucsf_set):
        raise ExclusionReportError(
            "BraTS exclusions must belong to the UCSF metadata inventory"
        )
    if not brats_ids.issubset(directory_backed):
        raise ExclusionReportError(
            "BraTS exclusions must belong to the directory-backed UCSF cohort"
        )
    if brats_ids & no_imaging:
        raise ExclusionReportError(
            "BraTS exclusions and no-imaging UCSF patients must be disjoint"
        )

    followup_record = build_followup_timepoint_selection_record(raw_ucsf_directory_ids)
    followup_count = followup_record["selection_count"]
    if not isinstance(followup_count, int):
        raise ExclusionReportError("follow-up selection count must be an integer")

    exclusions = [
        {
            "cohort": Cohort.UTSW.value,
            "patient_id": patient_id,
            "reason": IDH_UNAVAILABLE_REASON,
        }
        for patient_id in utsw_idh_unavailable
    ]
    exclusions.extend(
        {
            "cohort": Cohort.UCSF_PDGM.value,
            "patient_id": patient_id,
            "reason": BRATS_EXCLUSION_REASON,
        }
        for patient_id in sorted(brats_ids)
    )
    exclusions.extend(
        {
            "cohort": Cohort.UCSF_PDGM.value,
            "patient_id": patient_id,
            "reason": NO_IMAGING_AVAILABLE_REASON,
        }
        for patient_id in sorted(no_imaging)
    )

    ucsf_metadata_count = len(ucsf_set)
    directory_backed_count = len(directory_backed)
    no_imaging_count = len(no_imaging)
    raw_directory_count = len(raw_ucsf_directory_ids)
    retained_from_directory = directory_backed_count - len(brats_ids)
    retained_from_metadata = ucsf_metadata_count - len(brats_ids) - no_imaging_count
    if ucsf_metadata_count != directory_backed_count + no_imaging_count:
        raise ExclusionReportError("UCSF metadata partition does not close")
    if raw_directory_count != directory_backed_count + followup_count:
        raise ExclusionReportError("UCSF directory partition does not close")
    if retained_from_directory != retained_from_metadata:
        raise ExclusionReportError("UCSF retained-cohort identities disagree")

    reason_counts = {
        IDH_UNAVAILABLE_REASON: len(utsw_idh_unavailable),
        BRATS_EXCLUSION_REASON: len(brats_ids),
        NO_IMAGING_AVAILABLE_REASON: no_imaging_count,
    }
    return {
        "manifest_version": _MANIFEST_VERSION,
        "generated_by": "T03.10 exclusion manifest",
        "exclusions": exclusions,
        "excluded_patient_count": len(exclusions),
        "reason_counts": reason_counts,
        "cohorts": {
            Cohort.UTSW.value: {
                "source_patient_count": len(utsw_ids),
                "excluded_patient_count": len(utsw_idh_unavailable),
                "retained_patient_count": len(utsw_ids) - len(utsw_idh_unavailable),
                "reason_counts": {IDH_UNAVAILABLE_REASON: len(utsw_idh_unavailable)},
            },
            Cohort.UCSF_PDGM.value: {
                "metadata_patient_count": ucsf_metadata_count,
                "directory_backed_patient_count": directory_backed_count,
                "no_imaging_patient_count": no_imaging_count,
                "excluded_patient_count": len(brats_ids) + no_imaging_count,
                "retained_patient_count": retained_from_directory,
                "reason_counts": {
                    BRATS_EXCLUSION_REASON: len(brats_ids),
                    NO_IMAGING_AVAILABLE_REASON: no_imaging_count,
                },
                "followup_selection_count": followup_count,
            },
        },
        "accounting_checks": {
            "ucsf_metadata_partition": {
                "metadata_patient_count": ucsf_metadata_count,
                "directory_backed_patient_count": directory_backed_count,
                "no_imaging_patient_count": no_imaging_count,
                "identity": (
                    f"{ucsf_metadata_count} = {directory_backed_count} + "
                    f"{no_imaging_count}"
                ),
                "identity_holds": (
                    ucsf_metadata_count == directory_backed_count + no_imaging_count
                ),
            },
            "ucsf_directory_partition": {
                "raw_directory_count": raw_directory_count,
                "baseline_directory_count": directory_backed_count,
                "followup_directory_count": followup_count,
                "identity_holds": (
                    raw_directory_count == directory_backed_count + followup_count
                ),
            },
            "ucsf_retained_cohort": {
                "from_directory_backed": retained_from_directory,
                "from_metadata": retained_from_metadata,
                "identity": (
                    f"{directory_backed_count} - {len(brats_ids)} = "
                    f"{ucsf_metadata_count} - {len(brats_ids)} - {no_imaging_count}"
                ),
                "identity_holds": retained_from_directory == retained_from_metadata,
            },
        },
    }


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


def _load_real_utsw_patient_ids() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Load UTSW IDs and the rows without an IDH result from real metadata."""

    metadata_path = paths.raw_data_dir() / "UTSW_Glioma_Metadata-2-1.tsv"
    patient_ids: list[str] = []
    idh_unavailable_ids: list[str] = []
    try:
        with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            required = {"Subject ID", "IDH"}
            if not reader.fieldnames or not required.issubset(reader.fieldnames):
                raise ExclusionReportError(
                    "UTSW metadata is missing Subject ID or IDH columns"
                )
            for row in reader:
                raw_id = row.get("Subject ID")
                raw_idh = row.get("IDH")
                if raw_id is None or not raw_id.strip():
                    raise ExclusionReportError(
                        "UTSW metadata contains a blank Subject ID"
                    )
                if raw_idh is None:
                    raise ExclusionReportError(
                        "UTSW metadata contains a missing IDH cell"
                    )
                patient_ids.append(raw_id.strip())
                if raw_idh.strip().casefold() in {"", "na", "n/a"}:
                    idh_unavailable_ids.append(raw_id.strip())
    except OSError as error:
        raise ExclusionReportError(
            f"cannot read the UTSW metadata source: {metadata_path}"
        ) from error
    if not patient_ids:
        raise ExclusionReportError("UTSW metadata contains no patient IDs")
    return tuple(patient_ids), tuple(idh_unavailable_ids)


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


def build_real_followup_timepoint_selection_record() -> dict[str, object]:
    """Build the real UCSF baseline/follow-up directory selection record."""

    return build_followup_timepoint_selection_record(
        item.patient_id for item in ucsf_pdgm.discover_files()
    )


def build_real_exclusion_manifest() -> dict[str, object]:
    """Build and arithmetic-check the real Phase 03 exclusion manifest."""

    _, overlap_details = build_real_overlap_audit()
    brats_report = build_brats_exclusion_report(overlap_details)
    utsw_patient_ids, utsw_idh_unavailable_ids = _load_real_utsw_patient_ids()
    ucsf_metadata_ids = _load_real_ucsf_source_ids()
    ucsf_directory_ids = tuple(item.patient_id for item in ucsf_pdgm.discover_files())
    return build_exclusion_manifest(
        utsw_patient_ids=utsw_patient_ids,
        utsw_idh_unavailable_ids=utsw_idh_unavailable_ids,
        ucsf_metadata_ids=ucsf_metadata_ids,
        ucsf_directory_ids=ucsf_directory_ids,
        brats_exclusion_report=brats_report,
    )


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


def write_exclusion_manifest(
    manifest: Mapping[str, object], output_path: Path | None = None
) -> Path:
    """Write the patient-level exclusion manifest through configured paths."""

    destination = output_path or paths.manifests_dir() / "exclusion_manifest.json"
    return _write_json(manifest, destination)


def write_followup_timepoint_selection_record(
    record: Mapping[str, object], output_path: Path | None = None
) -> Path:
    """Write the UCSF directory-selection companion record."""

    destination = output_path or (
        paths.manifests_dir() / "ucsf_pdgm_followup_timepoint_selections.json"
    )
    return _write_json(record, destination)


def write_brats_exclusion_summary(
    report: Mapping[str, object], output_path: Path | None = None
) -> Path:
    """Write only the roster-free aggregate exclusion summary."""

    destination = output_path or (
        paths.manifests_dir() / "ucsf_pdgm_brats_exclusions_summary.json"
    )
    return _write_json(build_brats_exclusion_summary(report), destination)

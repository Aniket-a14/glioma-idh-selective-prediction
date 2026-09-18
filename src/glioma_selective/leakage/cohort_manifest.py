"""Build and verify the committed, roster-free Phase 03 cohort manifest.

The operational exclusion manifest remains on the configured external storage
because it contains patient identifiers.  This module derives the retained
canonical roster from that manifest and the real cohort inventories, but only
commits aggregate counts and a digest of each roster.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

from glioma_selective.data.adapters import ucsf_pdgm, utsw
from glioma_selective.leakage.exclusions import build_real_exclusion_manifest
from glioma_selective.leakage.id_normalization import (
    Cohort,
    IdentifierNormalizationError,
    normalize_identifier,
)

__all__ = [
    "COHORT_MANIFEST_VERSION",
    "ROSTER_CONSTRUCTION",
    "CohortManifestError",
    "build_cohort_manifest",
    "build_real_cohort_manifest",
    "build_real_retained_rosters",
    "compute_roster_sha256",
    "verify_roster_digest",
    "write_cohort_manifest",
]


COHORT_MANIFEST_VERSION: Final[int] = 1
ROSTER_CONSTRUCTION: Final[str] = (
    "Normalize every retained raw patient ID with the cohort-specific "
    "normalizer; sort canonical IDs in Unicode lexicographic order; join "
    "with one LF (U+000A) separator and no trailing LF; encode the joined "
    "string as UTF-8; hash those bytes with SHA-256."
)
EGD_NOTE: Final[str] = (
    "EGD is not included yet because its DUA is pending (D-018). This "
    "manifest will require version 2 once EGD arrives."
)
_UCSF_FOLLOWUP_DIRECTORY_RE: Final[re.Pattern[str]] = re.compile(
    r"(UCSF-PDGM-\d{3,4})_FU[A-Za-z0-9]+_nifti$", re.IGNORECASE
)
_MANIFEST_COHORTS: Final[tuple[Cohort, ...]] = (
    Cohort.UTSW,
    Cohort.UCSF_PDGM,
)


class CohortManifestError(ValueError):
    """Raised when a cohort manifest or roster verification is malformed."""


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise CohortManifestError(f"{context} must be a JSON object")
    return cast(Mapping[str, object], value)


def _cohort_value(cohort: object) -> Cohort:
    if isinstance(cohort, Cohort):
        return cohort
    if not isinstance(cohort, str):
        raise CohortManifestError(f"unsupported manifest cohort: {cohort!r}")
    try:
        return Cohort(cohort)
    except ValueError as error:
        raise CohortManifestError(f"unsupported manifest cohort: {cohort!r}") from error


def _canonical_roster(
    patient_ids: Iterable[str], cohort: Cohort | str
) -> tuple[str, ...]:
    selected = _cohort_value(cohort)
    canonical: list[str] = []
    seen: set[str] = set()
    for index, raw_id in enumerate(patient_ids):
        try:
            normalized = normalize_identifier(raw_id, selected)
        except (IdentifierNormalizationError, TypeError) as error:
            raise CohortManifestError(
                f"{selected.value} retained roster entry {index} is invalid"
            ) from error
        if normalized in seen:
            raise CohortManifestError(
                f"{selected.value} retained roster contains duplicate: {normalized}"
            )
        seen.add(normalized)
        canonical.append(normalized)
    return tuple(sorted(canonical))


def compute_roster_sha256(patient_ids: Iterable[str], cohort: Cohort | str) -> str:
    """Hash a cohort's sorted, canonical retained patient-ID roster.

    The roster is normalized before sorting.  The joined UTF-8 bytes contain
    no final newline; the exact construction is recorded in
    :data:`ROSTER_CONSTRUCTION` and in every committed cohort entry.
    """

    canonical = _canonical_roster(patient_ids, cohort)
    return _hash_canonical_roster(canonical)


def _hash_canonical_roster(canonical: Iterable[str]) -> str:
    joined = "\n".join(canonical).encode("utf-8")
    return hashlib.sha256(joined).hexdigest()


def _nonnegative_int(value: object, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CohortManifestError(f"{context} must be a non-negative integer")
    return value


def _reason_counts(value: object, context: str) -> dict[str, int]:
    values = _mapping(value, context)
    result: dict[str, int] = {}
    for reason, count in values.items():
        result[reason] = _nonnegative_int(count, f"{context}.{reason}")
    return dict(sorted(result.items()))


def _cohort_exclusion_report(
    exclusion_manifest: Mapping[str, object], cohort: Cohort
) -> Mapping[str, object]:
    cohorts = _mapping(exclusion_manifest.get("cohorts"), "exclusion_manifest.cohorts")
    return _mapping(
        cohorts.get(cohort.value), f"exclusion_manifest.cohorts.{cohort.value}"
    )


def _normalize_inventory_id(raw_id: str, cohort: Cohort) -> str:
    """Normalize an inventory ID, including UCSF's observed follow-up wrapper."""

    try:
        return normalize_identifier(raw_id, cohort)
    except IdentifierNormalizationError:
        if cohort is Cohort.UCSF_PDGM:
            match = _UCSF_FOLLOWUP_DIRECTORY_RE.fullmatch(raw_id)
            if match is not None:
                return normalize_identifier(match.group(1), cohort)
        raise


def _excluded_ids(
    exclusion_manifest: Mapping[str, object], cohort: Cohort
) -> frozenset[str]:
    entries = exclusion_manifest.get("exclusions")
    if not isinstance(entries, list | tuple):
        raise CohortManifestError("exclusion_manifest.exclusions must be an array")
    excluded: set[str] = set()
    for index, raw_entry in enumerate(entries):
        entry = _mapping(raw_entry, f"exclusion_manifest.exclusions[{index}]")
        if entry.get("cohort") != cohort.value:
            continue
        patient_id = entry.get("patient_id")
        if not isinstance(patient_id, str):
            raise CohortManifestError(
                f"exclusion_manifest.exclusions[{index}].patient_id must be a string"
            )
        normalized = _normalize_inventory_id(patient_id, cohort)
        if normalized in excluded:
            raise CohortManifestError(
                f"exclusion manifest repeats {cohort.value} patient {normalized}"
            )
        excluded.add(normalized)
    return frozenset(excluded)


def build_cohort_manifest(
    exclusion_manifest: Mapping[str, object],
    retained_patient_ids: Mapping[Cohort, Iterable[str]],
    *,
    generated_at: str | None = None,
) -> dict[str, object]:
    """Build the roster-free committed manifest from T03.10 accounting.

    Counts and exclusion reasons are copied from the already-verified T03.10
    manifest.  The supplied retained IDs are used only to compute the digest;
    they are never included in the returned mapping.
    """

    selected: dict[Cohort, Iterable[str]] = {}
    for raw_cohort, roster in retained_patient_ids.items():
        cohort = _cohort_value(raw_cohort)
        if cohort not in _MANIFEST_COHORTS:
            raise CohortManifestError(
                f"cohort {cohort.value} is not part of manifest version 1"
            )
        if cohort in selected:
            raise CohortManifestError(f"duplicate retained roster for {cohort.value}")
        selected[cohort] = roster
    if set(selected) != set(_MANIFEST_COHORTS):
        missing = sorted(
            cohort.value for cohort in set(_MANIFEST_COHORTS) - set(selected)
        )
        raise CohortManifestError(f"missing retained roster for: {', '.join(missing)}")

    cohort_entries: dict[str, object] = {}
    for cohort in _MANIFEST_COHORTS:
        report = _cohort_exclusion_report(exclusion_manifest, cohort)
        retained_count = _nonnegative_int(
            report.get("retained_patient_count"),
            f"exclusion_manifest.cohorts.{cohort.value}.retained_patient_count",
        )
        excluded_count = _nonnegative_int(
            report.get("excluded_patient_count"),
            f"exclusion_manifest.cohorts.{cohort.value}.excluded_patient_count",
        )
        reason_counts = _reason_counts(
            report.get("reason_counts"),
            f"exclusion_manifest.cohorts.{cohort.value}.reason_counts",
        )
        canonical = _canonical_roster(selected[cohort], cohort)
        digest = _hash_canonical_roster(canonical)
        canonical_count = len(canonical)
        if canonical_count != retained_count:
            raise CohortManifestError(
                f"{cohort.value} retained roster has {canonical_count} IDs, "
                f"but T03.10 records {retained_count}"
            )
        cohort_entries[cohort.value] = {
            "retained_patient_count": retained_count,
            "excluded_patient_count": excluded_count,
            "exclusion_reason_counts": reason_counts,
            "roster_sha256": digest,
            "roster_construction": ROSTER_CONSTRUCTION,
        }

    timestamp = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    return {
        "manifest_version": COHORT_MANIFEST_VERSION,
        "generated_at": timestamp,
        "note": EGD_NOTE,
        "cohorts": cohort_entries,
    }


def verify_roster_digest(
    manifest: Mapping[str, object],
    cohort: Cohort | str,
    retained_patient_ids: Iterable[str],
) -> dict[str, object]:
    """Recompute a retained roster digest and verify a committed manifest entry."""

    selected = _cohort_value(cohort)
    cohorts = _mapping(manifest.get("cohorts"), "manifest.cohorts")
    entry = _mapping(cohorts.get(selected.value), f"manifest.cohorts.{selected.value}")
    expected = entry.get("roster_sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        raise CohortManifestError(
            f"manifest.cohorts.{selected.value}.roster_sha256 is malformed"
        )
    canonical = _canonical_roster(retained_patient_ids, selected)
    actual = _hash_canonical_roster(canonical)
    if actual != expected:
        raise CohortManifestError(
            f"{selected.value} roster digest mismatch: expected {expected}, "
            f"got {actual}"
        )
    recorded_count = _nonnegative_int(
        entry.get("retained_patient_count"),
        f"manifest.cohorts.{selected.value}.retained_patient_count",
    )
    if len(canonical) != recorded_count:
        raise CohortManifestError(
            f"{selected.value} roster count mismatch: expected {recorded_count}, "
            f"got {len(canonical)}"
        )
    if entry.get("roster_construction") != ROSTER_CONSTRUCTION:
        raise CohortManifestError(
            f"{selected.value} roster construction does not match the verifier"
        )
    return {
        "status": "verified",
        "cohort": selected.value,
        "retained_patient_count": len(canonical),
        "roster_sha256": actual,
    }


def build_real_retained_rosters(
    exclusion_manifest: Mapping[str, object] | None = None,
) -> dict[Cohort, tuple[str, ...]]:
    """Return real canonical retained patient sets for digest verification."""

    selected_exclusion_manifest = (
        exclusion_manifest
        if exclusion_manifest is not None
        else build_real_exclusion_manifest()
    )
    retained: dict[Cohort, tuple[str, ...]] = {}
    for cohort, inventory in (
        (Cohort.UTSW, utsw.discover_files()),
        (Cohort.UCSF_PDGM, ucsf_pdgm.discover_files()),
    ):
        excluded = _excluded_ids(selected_exclusion_manifest, cohort)
        normalized_inventory = tuple(
            _normalize_inventory_id(item.patient_id, cohort) for item in inventory
        )
        retained_set = {
            patient_id
            for patient_id in normalized_inventory
            if patient_id not in excluded
        }
        retained[cohort] = tuple(sorted(retained_set))
    return retained


def build_real_cohort_manifest(*, generated_at: str | None = None) -> dict[str, object]:
    """Build and verify the real T03.11 manifest from local cohort inventories."""

    exclusion_manifest = build_real_exclusion_manifest()
    retained = build_real_retained_rosters(exclusion_manifest)

    manifest = build_cohort_manifest(
        exclusion_manifest,
        retained,
        generated_at=generated_at,
    )
    for cohort in _MANIFEST_COHORTS:
        verify_roster_digest(manifest, cohort, retained[cohort])
    return manifest


def write_cohort_manifest(manifest: Mapping[str, object], output_path: Path) -> Path:
    """Write the roster-free manifest to its committed documentation path."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_path

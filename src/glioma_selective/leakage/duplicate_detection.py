"""Detect duplicate scans within the downloaded cohorts.

The detector works from the Phase 02 adapter inventories. It never walks a
cohort root itself, so a patient directory remains the unit of discovery. A
complete duplicate-scan candidate is reported when either every discovered
file has the same content as another patient directory or all four canonical
sequence files have the same content. Shared individual file hashes are also
reported as weaker evidence for review.

Reports are operational artifacts and may contain raw patient directory names;
they must be written through :mod:`glioma_selective.utils.paths` and must not be
committed. The detector recommends a retention rule when candidates exist but
does not exclude or delete any directory. Research Lead approval is required
before that recommendation becomes an exclusion policy.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from glioma_selective.data.adapters import ucsf_pdgm, utsw
from glioma_selective.data.adapters._common import PatientFileInventory
from glioma_selective.utils import paths

__all__ = [
    "DuplicateDetectionError",
    "build_report",
    "detect_cohort_duplicates",
]


CHUNK_SIZE: Final[int] = 1024 * 1024
INTEGRITY_REPORT_NAME: Final[str] = "download_integrity_report.json"
COHORT_NAMES: Final[tuple[str, ...]] = ("utsw", "ucsf_pdgm")


class DuplicateDetectionError(RuntimeError):
    """Raised when an input inventory or optional hash report is malformed."""


@dataclass(frozen=True)
class PatientHashRecord:
    """Content hashes for the files discovered in one patient directory."""

    patient_id: str
    file_hashes: tuple[tuple[str, int, str], ...]
    core_sequence_hashes: tuple[tuple[str, int, str], ...]

    @property
    def file_fingerprint(self) -> tuple[tuple[int, str], ...]:
        """Return a filename-independent multiset of all file contents."""

        return tuple(sorted((size, digest) for _, size, digest in self.file_hashes))

    @property
    def core_sequence_fingerprint(
        self,
    ) -> tuple[tuple[str, int, str], ...] | None:
        """Return the four-sequence fingerprint when all four are present."""

        return (
            self.core_sequence_hashes if len(self.core_sequence_hashes) == 4 else None
        )


def _cohort_roots() -> dict[str, Path]:
    """Resolve cohort roots through the canonical path abstraction."""

    return {
        "utsw": paths.raw_data_dir() / "utsw",
        "ucsf_pdgm": paths.external_data_dir() / "ucsf_pdgm",
    }


def _discover(cohort: str, root: Path) -> tuple[PatientFileInventory, ...]:
    """Discover one cohort through its existing adapter contract."""

    if cohort == "utsw":
        return utsw.discover_files(root)
    if cohort == "ucsf_pdgm":
        return ucsf_pdgm.discover_files(root)
    raise ValueError(f"unsupported cohort: {cohort}")


def _sha256(path: Path) -> str:
    """Hash a file with bounded memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_from_files(inventory: PatientFileInventory) -> PatientHashRecord:
    """Hash the files in an adapter inventory and retain sequence associations."""

    hashes_by_path: dict[Path, tuple[str, int, str]] = {}
    for file_path in inventory.files:
        size = file_path.stat().st_size
        hashes_by_path[file_path] = (file_path.name, size, _sha256(file_path))

    file_hashes = tuple(sorted(hashes_by_path.values()))
    core_hashes = tuple(
        sorted(
            (
                sequence.value,
                hashes_by_path[file_path][1],
                hashes_by_path[file_path][2],
            )
            for sequence, file_path in inventory.sequence_files.items()
        )
    )
    return PatientHashRecord(inventory.patient_id, file_hashes, core_hashes)


def _as_mapping(value: object, context: str) -> dict[str, object]:
    """Validate and return a JSON object without introducing ``Any``."""

    if not isinstance(value, dict):
        raise DuplicateDetectionError(f"{context} must be a JSON object")
    return cast(dict[str, object], value)


def _as_sequence(value: object, context: str) -> list[object]:
    """Validate and return a JSON array."""

    if not isinstance(value, list):
        raise DuplicateDetectionError(f"{context} must be a JSON array")
    return value


def _required_string(value: object, context: str) -> str:
    """Read a required non-empty JSON string."""

    if not isinstance(value, str) or not value:
        raise DuplicateDetectionError(f"{context} must be a non-empty string")
    return value


def _required_integer(value: object, context: str) -> int:
    """Read a required JSON integer, excluding booleans."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise DuplicateDetectionError(f"{context} must be an integer")
    return value


def _integrity_records(
    inventories: tuple[PatientFileInventory, ...],
    report: Mapping[str, object],
    cohort: str,
) -> tuple[PatientHashRecord, ...]:
    """Convert a complete, matching integrity report into hash records.

    The fast path is rejected unless the report is complete and its patient
    and file inventory exactly matches the adapter discovery. A rejected report
    causes the caller to hash the files independently.
    """

    cohort_data = _as_mapping(report.get("cohorts"), "integrity report cohorts")
    cohort_report = _as_mapping(cohort_data.get(cohort), f"integrity report {cohort}")
    if cohort_report.get("inventory_complete") is not True:
        raise DuplicateDetectionError(f"integrity report {cohort} is not complete")

    patient_entries = _as_sequence(
        cohort_report.get("patients"), f"integrity report {cohort}.patients"
    )
    by_patient: dict[str, dict[str, object]] = {}
    for index, value in enumerate(patient_entries):
        entry = _as_mapping(value, f"integrity report {cohort}.patients[{index}]")
        patient_id = _required_string(
            entry.get("patient_id"), f"integrity report {cohort} patient_id"
        )
        if patient_id in by_patient:
            raise DuplicateDetectionError(f"duplicate report patient: {patient_id}")
        by_patient[patient_id] = entry

    if set(by_patient) != {inventory.patient_id for inventory in inventories}:
        raise DuplicateDetectionError(f"integrity report {cohort} patient set differs")

    records: list[PatientHashRecord] = []
    for inventory in inventories:
        entry = by_patient[inventory.patient_id]
        file_entries = _as_sequence(
            entry.get("files"), f"integrity report {cohort} files"
        )
        report_files: dict[str, tuple[int, str]] = {}
        for index, value in enumerate(file_entries):
            file_entry = _as_mapping(value, f"integrity report file[{index}]")
            relative_path = _required_string(
                file_entry.get("relative_path"), "integrity report relative_path"
            )
            size = _required_integer(
                file_entry.get("size_bytes"), "integrity report size_bytes"
            )
            digest = _required_string(
                file_entry.get("sha256"), "integrity report sha256"
            )
            if len(digest) != 64 or any(
                character not in "0123456789abcdef" for character in digest
            ):
                raise DuplicateDetectionError(
                    "integrity report contains an invalid SHA-256"
                )
            if relative_path in report_files:
                raise DuplicateDetectionError(
                    "integrity report contains duplicate files"
                )
            report_files[relative_path] = (size, digest)

        actual_files = {
            file_path.name: file_path.stat().st_size for file_path in inventory.files
        }
        if report_files.keys() != actual_files.keys():
            raise DuplicateDetectionError(
                f"integrity report files differ for patient {inventory.patient_id}"
            )
        if any(actual_files[name] != size for name, (size, _) in report_files.items()):
            raise DuplicateDetectionError(
                f"integrity report file sizes differ for patient {inventory.patient_id}"
            )

        file_hashes = tuple(
            sorted(
                (name, size, digest) for name, (size, digest) in report_files.items()
            )
        )
        path_by_sequence = {
            sequence.value: file_path
            for sequence, file_path in inventory.sequence_files.items()
        }
        core_hashes = tuple(
            sorted(
                (
                    sequence,
                    report_files[path.name][0],
                    report_files[path.name][1],
                )
                for sequence, path in path_by_sequence.items()
            )
        )
        records.append(
            PatientHashRecord(inventory.patient_id, file_hashes, core_hashes)
        )
    return tuple(records)


def _load_integrity_report(path: Path) -> dict[str, object] | None:
    """Load the optional T02.6 report, returning ``None`` when unavailable."""

    try:
        payload = cast(object, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return cast(dict[str, object], payload)


def _hash_records(
    inventories: tuple[PatientFileInventory, ...],
    cohort: str,
    integrity_report: Mapping[str, object] | None,
) -> tuple[tuple[PatientHashRecord, ...], str]:
    """Obtain hash records, using the optional report only when it matches."""

    if integrity_report is not None:
        try:
            return _integrity_records(inventories, integrity_report, cohort), (
                "download_integrity_report"
            )
        except DuplicateDetectionError:
            pass
    return tuple(_record_from_files(inventory) for inventory in inventories), "computed"


def _group_by(
    records: Sequence[PatientHashRecord],
    key_name: str,
) -> dict[tuple[object, ...], tuple[str, ...]]:
    """Group patient IDs by one of the two duplicate fingerprints."""

    grouped: defaultdict[tuple[object, ...], list[str]] = defaultdict(list)
    for record in records:
        key = getattr(record, key_name)
        if key is not None:
            grouped[cast(tuple[object, ...], key)].append(record.patient_id)
    return {
        key: tuple(sorted(patient_ids))
        for key, patient_ids in grouped.items()
        if len(patient_ids) >= 2
    }


def _shared_hash_groups(
    records: Sequence[PatientHashRecord],
) -> list[dict[str, object]]:
    """Return individual file hashes shared by at least two patients."""

    grouped: defaultdict[tuple[int, str], list[tuple[str, str]]] = defaultdict(list)
    for record in records:
        for relative_path, size, digest in record.file_hashes:
            grouped[(size, digest)].append((record.patient_id, relative_path))

    result: list[dict[str, object]] = []
    for (size, digest), occurrences in sorted(
        grouped.items(), key=lambda item: item[0]
    ):
        patient_ids = sorted({patient_id for patient_id, _ in occurrences})
        if len(patient_ids) < 2:
            continue
        result.append(
            {
                "sha256": digest,
                "size_bytes": size,
                "patient_ids": patient_ids,
                "occurrence_count": len(occurrences),
            }
        )
    return result


def _duplicate_groups(
    exact_groups: Mapping[tuple[object, ...], tuple[str, ...]],
    core_groups: Mapping[tuple[object, ...], tuple[str, ...]],
) -> list[dict[str, object]]:
    """Merge overlapping exact/core groups while retaining signal evidence."""

    evidence_by_patients: dict[frozenset[str], list[str]] = defaultdict(list)
    for patient_ids in exact_groups.values():
        evidence_by_patients[frozenset(patient_ids)].append("identical_all_files")
    for patient_ids in core_groups.values():
        evidence_by_patients[frozenset(patient_ids)].append(
            "identical_four_core_sequences"
        )
    return [
        {
            "patient_ids": sorted(patient_ids),
            "evidence": sorted(set(evidence)),
        }
        for patient_ids, evidence in sorted(
            evidence_by_patients.items(), key=lambda item: tuple(sorted(item[0]))
        )
    ]


def _retention_recommendation(has_duplicates: bool) -> dict[str, object]:
    """Return a recommendation without applying a retention decision."""

    if not has_duplicates:
        return {
            "status": "not_applicable",
            "research_lead_approval_required": False,
            "recommended_rule": None,
        }
    return {
        "status": "recommendation_only",
        "research_lead_approval_required": True,
        "recommended_rule": (
            "retain the earliest verified acquisition; when acquisition dates are "
            "unavailable, retain one deterministic representative and record the "
            "choice in the exclusion manifest"
        ),
        "reason": (
            "Directory names do not establish acquisition chronology, and no "
            "directory is excluded by this detector. The Research Lead must "
            "approve the rule and its fallback before manifest freezing."
        ),
    }


def detect_cohort_duplicates(
    cohort: str,
    *,
    root: Path | None = None,
    integrity_report: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Detect within-cohort duplicate-scan candidates and return a report.

    Args:
        cohort: Either ``"utsw"`` or ``"ucsf_pdgm"``.
        root: Optional test or caller-supplied cohort root. Production callers
            should omit it so the adapter and :mod:`utils.paths` resolve it.
        integrity_report: Optional parsed T02.6 report. It is used only when
            complete and consistent with current adapter discovery.
    """

    if cohort not in COHORT_NAMES:
        raise ValueError(f"unsupported cohort: {cohort}")
    resolved_root = root if root is not None else _cohort_roots()[cohort]
    inventories = _discover(cohort, resolved_root)
    records, hash_source = _hash_records(inventories, cohort, integrity_report)
    exact_groups = _group_by(records, "file_fingerprint")
    core_groups = _group_by(records, "core_sequence_fingerprint")
    duplicate_groups = _duplicate_groups(exact_groups, core_groups)
    duplicate_patient_ids = {
        patient_id
        for group in duplicate_groups
        for patient_id in cast(list[str], group["patient_ids"])
    }
    shared_hash_groups = _shared_hash_groups(records)
    if duplicate_groups:
        finding = "duplicate_scan_candidates_found"
    elif shared_hash_groups:
        finding = "no_complete_duplicate_scan_shared_hash_review"
    else:
        finding = "no_duplicate_scan_found"
    return {
        "root": str(resolved_root),
        "patient_count": len(inventories),
        "file_count": sum(len(inventory.files) for inventory in inventories),
        "hash_source": hash_source,
        "duplicate_finding": finding,
        "exact_file_set_group_count": len(exact_groups),
        "core_sequence_group_count": len(core_groups),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_patient_count": len(duplicate_patient_ids),
        "shared_file_hash_group_count": len(shared_hash_groups),
        "duplicate_groups": duplicate_groups,
        "shared_file_hash_groups": shared_hash_groups,
        "retention_rule_recommendation": _retention_recommendation(
            bool(duplicate_groups)
        ),
    }


def build_report(
    *,
    cohorts: Sequence[str] = COHORT_NAMES,
    roots: Mapping[str, Path] | None = None,
    integrity_report_path: Path | None = None,
    use_integrity_report: bool = True,
) -> dict[str, object]:
    """Build a duplicate-scan report without writing it.

    The default output path is deliberately resolved by the CLI through
    ``utils.paths.manifests_dir()``. No derived report is written to Git.
    """

    unknown = sorted(set(cohorts).difference(COHORT_NAMES))
    if unknown:
        raise ValueError(f"unsupported cohort(s): {', '.join(unknown)}")
    resolved_roots = dict(roots) if roots is not None else _cohort_roots()
    report: dict[str, object] | None = None
    if use_integrity_report:
        report_path = integrity_report_path
        if report_path is None:
            try:
                report_path = paths.manifests_dir() / INTEGRITY_REPORT_NAME
            except paths.PathResolutionError:
                report_path = None
        if report_path is not None and report_path.is_file():
            report = _load_integrity_report(report_path)

    cohort_reports = {
        cohort: detect_cohort_duplicates(
            cohort,
            root=resolved_roots[cohort],
            integrity_report=report,
        )
        for cohort in cohorts
    }
    return {
        "schema_version": 1,
        "generated_by": "T03.8 duplicate-scan detection",
        "integrity_report_used": bool(cohort_reports)
        and all(
            isinstance(cohort_report, dict)
            and cohort_report.get("hash_source") == "download_integrity_report"
            for cohort_report in cohort_reports.values()
        ),
        "cohorts": cohort_reports,
        "retention_rule": {
            "status": "requires_research_lead_approval",
            "applies_to": "duplicate_scan_candidates_only",
            "recommendation": (
                "retain the earliest verified acquisition; use a deterministic "
                "representative only as a documented fallback when dates are absent"
            ),
        },
    }

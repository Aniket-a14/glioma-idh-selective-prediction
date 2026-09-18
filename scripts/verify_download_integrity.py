#!/usr/bin/env python3
"""Verify downloaded cohorts without reading image pixels.

The default command inventories both Phase 02 cohorts through the canonical
path accessors and writes ``data/manifests/download_integrity_report.json``.
The report schema is:

* ``schema_version`` and ``generated_at_utc`` identify the report format and
  run.
* ``cohorts.<name>.patient_count`` records the observed and SPEC-claimed
  counts, with ``count_status`` set to ``matches`` or ``mismatch``.  The SPEC
  count remains provisional until Phase 03's hashed manifest (D-009).
* ``cohorts.<name>.patients`` contains one entry per inventoried patient.  It
  records the raw folder name, file count, and every file relative to that
  folder.  Each file has its size and SHA-256.  ``.nii.gz`` files also have
  gzip and NIfTI-header validation fields.
* ``cohorts.<name>.failures`` repeats every failed file check with a
  machine-readable reason and ``review_required_before_use`` disposition.
  This list is intentionally explicit so a failed run cannot look like a
  successful checksum-only run.

The report is derived from restricted raw data and must not be committed.  It
contains raw patient folder names because it is an operational audit artifact;
the script, tests, and committed documentation contain no patient IDs.

Examples::

    python scripts/verify_download_integrity.py
    python scripts/verify_download_integrity.py --cohort utsw --limit 3

``--limit`` is for development only.  The default has no limit and is the
acceptance run for the complete cohorts.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import struct
import sys
import zlib
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

# Running this file directly does not put ``src/`` on sys.path.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.utils import paths  # noqa: E402

CHUNK_SIZE: Final[int] = 1024 * 1024
NIFTI1_HEADER_SIZE: Final[int] = 348
NIFTI2_HEADER_SIZE: Final[int] = 540
EXPECTED_PATIENT_COUNTS: Final[dict[str, int]] = {
    "utsw": 625,
    "ucsf_pdgm": 501,
}


class IntegrityVerificationError(RuntimeError):
    """Raised when a cohort cannot be inventoried safely."""


def _cohort_roots() -> dict[str, Path]:
    """Resolve the two T02.6 cohort roots through ``utils.paths`` only."""

    return {
        "utsw": paths.raw_data_dir() / "utsw",
        "ucsf_pdgm": paths.external_data_dir() / "ucsf_pdgm",
    }


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of *path* using bounded memory."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _nifti_header(header: bytes) -> tuple[bool, dict[str, object], str | None]:
    """Parse the identifying fields of a NIfTI-1 or NIfTI-2 header.

    This validates header structure and dimensions only.  It deliberately does
    not load or inspect voxel data.
    """

    if len(header) < 4:
        return False, {}, "nifti_header_too_short"

    byte_order: str | None = None
    version: str | None = None
    header_size: int | None = None
    for endian in ("<", ">"):
        size = struct.unpack(f"{endian}i", header[:4])[0]
        if size == NIFTI1_HEADER_SIZE:
            byte_order = endian
            version = "nifti-1"
            header_size = NIFTI1_HEADER_SIZE
            magic = header[344:348]
            if magic not in (b"n+1\x00", b"ni1\x00"):
                return False, {}, "nifti1_magic_mismatch"
            dimension_offset = 40
            break
        if size == NIFTI2_HEADER_SIZE and len(header) >= NIFTI2_HEADER_SIZE:
            byte_order = endian
            version = "nifti-2"
            header_size = NIFTI2_HEADER_SIZE
            magic = header[4:8]
            if magic not in (b"n+2\x00", b"ni2\x00"):
                return False, {}, "nifti2_magic_mismatch"
            dimension_offset = 16
            break
    else:
        return False, {}, "nifti_header_size_mismatch"

    if byte_order is None or version is None or header_size is None:
        return False, {}, "nifti_header_parse_failed"
    if len(header) < header_size:
        return False, {}, "nifti_header_too_short"

    dimension_format = "8h" if version == "nifti-1" else "8q"
    dimensions = struct.unpack(
        f"{byte_order}{dimension_format}",
        header[dimension_offset : dimension_offset + struct.calcsize(dimension_format)],
    )
    dimension_count = dimensions[0]
    if not 1 <= dimension_count <= 7:
        return False, {}, "nifti_dimension_count_invalid"
    if any(dimension <= 0 for dimension in dimensions[1 : dimension_count + 1]):
        return False, {}, "nifti_dimension_invalid"

    return (
        True,
        {
            "format": version,
            "byte_order": "little" if byte_order == "<" else "big",
            "dimensions": list(dimensions[: dimension_count + 1]),
        },
        None,
    )


def _validate_nifti_gzip(path: Path) -> dict[str, object]:
    """Validate gzip framing, decompression, and the NIfTI header."""

    header = b""
    try:
        with gzip.open(path, "rb") as stream:
            header = stream.read(NIFTI2_HEADER_SIZE)
            for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
                del chunk
    except (EOFError, OSError, zlib.error) as exc:
        return {
            "gzip_valid": False,
            "nifti_valid": False,
            "status": "invalid",
            "error": f"gzip_read_error:{type(exc).__name__}",
        }

    nifti_valid, header_info, error = _nifti_header(header)
    return {
        "gzip_valid": True,
        "nifti_valid": nifti_valid,
        "status": "valid" if nifti_valid else "invalid",
        "header": header_info if nifti_valid else None,
        "error": error,
    }


def _file_record(path: Path, patient_dir: Path) -> dict[str, object]:
    """Hash one file and validate it when its name denotes ``.nii.gz``."""

    relative_path = path.relative_to(patient_dir).as_posix()
    record: dict[str, object] = {
        "relative_path": relative_path,
        "size_bytes": path.stat().st_size,
        "sha256": None,
        "is_nifti_gz": path.name.lower().endswith(".nii.gz"),
        "validation": None,
    }
    try:
        record["sha256"] = _sha256(path)
    except OSError as exc:
        record["hash_error"] = f"hash_read_error:{type(exc).__name__}"
        return record

    if record["is_nifti_gz"]:
        record["validation"] = _validate_nifti_gzip(path)
    return record


def _failure_for_file(patient_id: str, record: dict[str, object]) -> dict[str, str]:
    """Return a failure entry for a file record, or an empty mapping."""

    if record.get("sha256") is None:
        return {
            "patient_id": patient_id,
            "relative_path": str(record["relative_path"]),
            "reason": str(record.get("hash_error", "hash_missing")),
            "disposition": "review_required_before_use",
        }
    validation = record.get("validation")
    if isinstance(validation, dict) and validation.get("status") != "valid":
        return {
            "patient_id": patient_id,
            "relative_path": str(record["relative_path"]),
            "reason": str(validation.get("error", "nifti_validation_failed")),
            "disposition": "review_required_before_use",
        }
    return {}


def _inventory_cohort(name: str, root: Path, limit: int | None) -> dict[str, object]:
    """Inventory one cohort root, preserving all failures in the report."""

    if not root.exists() or not root.is_dir():
        raise IntegrityVerificationError(f"cohort root is not a directory: {root}")

    all_patient_dirs = sorted(
        (entry for entry in root.iterdir() if entry.is_dir()),
        key=lambda path: path.name,
    )
    patient_dirs = all_patient_dirs if limit is None else all_patient_dirs[:limit]
    file_name_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    patients: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    total_file_count = 0
    valid_nifti_count = 0
    invalid_nifti_count = 0

    for patient_dir in patient_dirs:
        file_paths = sorted(path for path in patient_dir.rglob("*") if path.is_file())
        records: list[dict[str, object]] = []
        for file_path in file_paths:
            record = _file_record(file_path, patient_dir)
            records.append(record)
            file_name_counts[file_path.name] += 1
            suffix = (
                ".nii.gz"
                if file_path.name.lower().endswith(".nii.gz")
                else file_path.suffix.lower() or "<no-extension>"
            )
            extension_counts[suffix] += 1
            failure = _failure_for_file(patient_dir.name, record)
            if failure:
                failures.append(failure)
            validation = record.get("validation")
            if isinstance(validation, dict):
                if validation.get("status") == "valid":
                    valid_nifti_count += 1
                else:
                    invalid_nifti_count += 1

        if not records:
            failures.append(
                {
                    "patient_id": patient_dir.name,
                    "relative_path": ".",
                    "reason": "empty_patient_directory",
                    "disposition": "review_required_before_use",
                }
            )
        patients.append(
            {
                "patient_id": patient_dir.name,
                "file_count": len(records),
                "files": records,
            }
        )
        total_file_count += len(records)

    expected_count = EXPECTED_PATIENT_COUNTS[name]
    observed_count = len(all_patient_dirs)
    count_status = "matches" if observed_count == expected_count else "mismatch"
    complete = limit is None
    file_checks_passed = not failures
    if not complete:
        status = "sampled"
    elif file_checks_passed and count_status == "matches":
        status = "pass"
    else:
        status = "review_required"
    return {
        "root": str(root),
        "expected_patient_count": expected_count,
        "expected_count_is_provisional": True,
        "observed_patient_count": observed_count,
        "inventoried_patient_count": len(patient_dirs),
        "count_status": count_status,
        "inventory_complete": complete,
        "status": status,
        "file_checks_passed": file_checks_passed,
        "inventoried_file_count": total_file_count,
        "valid_nifti_gz_count": valid_nifti_count,
        "invalid_nifti_gz_count": invalid_nifti_count,
        "file_name_counts": dict(sorted(file_name_counts.items())),
        "extension_counts": dict(sorted(extension_counts.items())),
        "patients": patients,
        "failures": failures,
    }


def build_report(
    *, cohorts: Sequence[str] = ("utsw", "ucsf_pdgm"), limit: int | None = None
) -> dict[str, object]:
    """Build a complete or limited integrity report without writing it."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be at least 1")
    roots = _cohort_roots()
    selected = {name: _inventory_cohort(name, roots[name], limit) for name in cohorts}
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source_checksum_available": False,
        "source_checksum_note": (
            "Manual download; no published source checksum was available."
        ),
        "cohorts": selected,
    }


def _summary(report: dict[str, object]) -> dict[str, object]:
    """Create concise stdout output without exposing patient identifiers."""

    cohorts = report["cohorts"]
    if not isinstance(cohorts, dict):
        raise IntegrityVerificationError(
            "report schema error: cohorts is not an object"
        )
    return {
        name: {
            key: cohort[key]
            for key in (
                "status",
                "observed_patient_count",
                "inventoried_patient_count",
                "inventoried_file_count",
                "valid_nifti_gz_count",
                "invalid_nifti_gz_count",
                "count_status",
                "file_checks_passed",
            )
        }
        for name, cohort in cohorts.items()
        if isinstance(cohort, dict)
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the verifier, write the report, and print an identifier-free summary."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort",
        choices=("all", "utsw", "ucsf_pdgm"),
        default="all",
        help="cohort to verify (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="inventory only the first N sorted patient directories; development only",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "report path (default: "
            "paths.manifests_dir()/download_integrity_report.json)"
        ),
    )
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")

    cohort_names = ("utsw", "ucsf_pdgm") if args.cohort == "all" else (args.cohort,)
    output = args.output or paths.manifests_dir() / "download_integrity_report.json"
    try:
        report = build_report(cohorts=cohort_names, limit=args.limit)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except (IntegrityVerificationError, OSError, ValueError) as exc:
        print(f"verify_download_integrity.py: error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"output": str(output), "cohorts": _summary(report)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

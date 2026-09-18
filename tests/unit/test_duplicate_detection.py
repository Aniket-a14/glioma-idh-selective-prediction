"""Synthetic tests for the T03.8 duplicate-scan detector."""

from __future__ import annotations

import json
from pathlib import Path

from glioma_selective.leakage import duplicate_detection as detector

_SEQUENCES = {
    "brain_t1.nii.gz": b"t1",
    "brain_t1ce.nii.gz": b"t1ce",
    "brain_t2.nii.gz": b"t2",
    "brain_flair.nii.gz": b"flair",
}


def _write_patient(root: Path, name: str, *, payloads: dict[str, bytes]) -> None:
    patient = root / name
    patient.mkdir(parents=True)
    for filename, payload in payloads.items():
        (patient / filename).write_bytes(payload)


def test_duplicate_detection_reports_exact_and_core_signals(tmp_path: Path) -> None:
    """A copied scan is reported without choosing which directory to retain."""

    root = tmp_path / "utsw"
    _write_patient(root, "SYNTHETIC-A", payloads=_SEQUENCES)
    _write_patient(
        root,
        "SYNTHETIC-B",
        payloads={**_SEQUENCES, "extra.txt": b"different bookkeeping"},
    )

    report = detector.detect_cohort_duplicates("utsw", root=root, integrity_report=None)

    assert report["hash_source"] == "computed"
    assert report["exact_file_set_group_count"] == 0
    assert report["core_sequence_group_count"] == 1
    assert report["duplicate_group_count"] == 1
    assert report["duplicate_patient_count"] == 2
    group = report["duplicate_groups"][0]
    assert group["patient_ids"] == ["SYNTHETIC-A", "SYNTHETIC-B"]
    assert group["evidence"] == ["identical_four_core_sequences"]
    assert report["retention_rule_recommendation"]["status"] == ("recommendation_only")
    assert (
        report["retention_rule_recommendation"]["research_lead_approval_required"]
        is True
    )


def test_duplicate_detection_reports_no_complete_duplicate_for_one_shared_file(
    tmp_path: Path,
) -> None:
    """One common file is weaker evidence and must not form a scan duplicate."""

    root = tmp_path / "utsw"
    _write_patient(root, "SYNTHETIC-A", payloads={"one.bin": b"shared"})
    _write_patient(
        root,
        "SYNTHETIC-B",
        payloads={"one.bin": b"shared", "two.bin": b"other"},
    )

    report = detector.detect_cohort_duplicates("utsw", root=root, integrity_report=None)

    assert report["duplicate_finding"] == (
        "no_complete_duplicate_scan_shared_hash_review"
    )
    assert report["duplicate_group_count"] == 0
    assert report["shared_file_hash_group_count"] == 1
    assert report["retention_rule_recommendation"]["status"] == "not_applicable"


def test_integrity_report_fast_path_is_used_and_written_report_is_structured(
    tmp_path: Path,
) -> None:
    """A complete matching integrity report avoids file re-hashing."""

    root = tmp_path / "utsw"
    _write_patient(root, "SYNTHETIC-A", payloads=_SEQUENCES)
    inventories = detector._discover("utsw", root)
    records = tuple(detector._record_from_files(inventory) for inventory in inventories)
    integrity_report = {
        "cohorts": {
            "utsw": {
                "inventory_complete": True,
                "patients": [
                    {
                        "patient_id": record.patient_id,
                        "files": [
                            {
                                "relative_path": name,
                                "size_bytes": size,
                                "sha256": digest,
                            }
                            for name, size, digest in record.file_hashes
                        ],
                    }
                    for record in records
                ],
            }
        }
    }

    report = detector.detect_cohort_duplicates(
        "utsw", root=root, integrity_report=integrity_report
    )

    assert report["hash_source"] == "download_integrity_report"
    assert report["duplicate_group_count"] == 0
    assert report["duplicate_finding"] == "no_duplicate_scan_found"
    json.dumps(report)

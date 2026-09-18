"""Unit tests for the Phase 02 T02.6 integrity verifier."""

from __future__ import annotations

import gzip
import json
import struct
from pathlib import Path

from scripts import verify_download_integrity as verifier


def _write_nifti_gz(path: Path, *, payload: bytes = b"voxel-bytes") -> None:
    """Write a minimal structurally valid NIfTI-1 gzip fixture."""

    header = bytearray(verifier.NIFTI1_HEADER_SIZE)
    struct.pack_into("<i", header, 0, verifier.NIFTI1_HEADER_SIZE)
    struct.pack_into("<8h", header, 40, 3, 2, 2, 2, 1, 1, 1, 1)
    header[344:348] = b"n+1\x00"
    with gzip.open(path, "wb") as stream:
        stream.write(header)
        stream.write(payload)


def test_build_report_hashes_all_files_and_records_missing_sequence(
    tmp_path: Path, monkeypatch
) -> None:
    """The inventory preserves file presence and hashes non-NIfTI files too."""

    root = tmp_path / "utsw"
    patient = root / "synthetic-patient"
    patient.mkdir(parents=True)
    _write_nifti_gz(patient / "present.nii.gz")
    (patient / "notes.txt").write_text("not an image", encoding="utf-8")
    monkeypatch.setattr(verifier, "EXPECTED_PATIENT_COUNTS", {"utsw": 1})
    monkeypatch.setattr(verifier, "_cohort_roots", lambda: {"utsw": root})

    report = verifier.build_report(cohorts=("utsw",))
    cohort = report["cohorts"]["utsw"]

    assert cohort["status"] == "pass"
    assert cohort["count_status"] == "matches"
    assert cohort["inventoried_file_count"] == 2
    assert cohort["valid_nifti_gz_count"] == 1
    assert cohort["invalid_nifti_gz_count"] == 0
    assert cohort["failures"] == []
    assert cohort["patients"][0]["file_count"] == 2
    records = {
        record["relative_path"]: record for record in cohort["patients"][0]["files"]
    }
    assert records["present.nii.gz"]["sha256"]
    assert records["notes.txt"]["sha256"]
    assert records["present.nii.gz"]["validation"]["nifti_valid"] is True


def test_truncated_nifti_is_a_recorded_failure(tmp_path: Path, monkeypatch) -> None:
    """A truncated gzip is detected even though its filename and hash exist."""

    root = tmp_path / "utsw"
    patient = root / "synthetic-patient"
    patient.mkdir(parents=True)
    valid_path = patient / "valid.nii.gz"
    _write_nifti_gz(valid_path)
    truncated_path = patient / "truncated.nii.gz"
    truncated_path.write_bytes(valid_path.read_bytes()[:-8])
    monkeypatch.setattr(verifier, "EXPECTED_PATIENT_COUNTS", {"utsw": 1})
    monkeypatch.setattr(verifier, "_cohort_roots", lambda: {"utsw": root})

    report = verifier.build_report(cohorts=("utsw",))
    cohort = report["cohorts"]["utsw"]

    assert cohort["status"] == "review_required"
    assert cohort["file_checks_passed"] is False
    assert cohort["invalid_nifti_gz_count"] == 1
    assert len(cohort["failures"]) == 1
    assert cohort["failures"][0]["relative_path"] == "truncated.nii.gz"
    assert cohort["failures"][0]["disposition"] == "review_required_before_use"


def test_invalid_header_is_detected_after_valid_gzip(
    tmp_path: Path, monkeypatch
) -> None:
    """A gzip stream with a non-NIfTI payload does not pass integrity checks."""

    root = tmp_path / "utsw"
    patient = root / "synthetic-patient"
    patient.mkdir(parents=True)
    with gzip.open(patient / "not_nifti.nii.gz", "wb") as stream:
        stream.write(b"valid gzip, invalid NIfTI")
    monkeypatch.setattr(verifier, "EXPECTED_PATIENT_COUNTS", {"utsw": 1})
    monkeypatch.setattr(verifier, "_cohort_roots", lambda: {"utsw": root})

    report = verifier.build_report(cohorts=("utsw",))
    validation = report["cohorts"]["utsw"]["patients"][0]["files"][0]["validation"]

    assert validation["gzip_valid"] is True
    assert validation["nifti_valid"] is False
    assert validation["error"] == "nifti_header_size_mismatch"


def test_cli_writes_structured_json_without_patient_inventory_on_stdout(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The CLI writes the detailed report and keeps stdout aggregate-only."""

    root = tmp_path / "utsw"
    patient = root / "synthetic-patient"
    patient.mkdir(parents=True)
    _write_nifti_gz(patient / "present.nii.gz")
    output = tmp_path / "report.json"
    monkeypatch.setattr(verifier, "EXPECTED_PATIENT_COUNTS", {"utsw": 1})
    monkeypatch.setattr(verifier, "_cohort_roots", lambda: {"utsw": root})

    assert verifier.main(["--cohort", "utsw", "--output", str(output)]) == 0
    stdout = capsys.readouterr().out
    summary = json.loads(stdout)
    written = json.loads(output.read_text(encoding="utf-8"))

    assert summary["cohorts"]["utsw"]["status"] == "pass"
    assert "synthetic-patient" not in stdout
    assert written["schema_version"] == 1
    assert written["cohorts"]["utsw"]["patients"][0]["patient_id"] == (
        "synthetic-patient"
    )

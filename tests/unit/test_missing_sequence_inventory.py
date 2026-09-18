"""Tests for the aggregate naturally-missing sequence inventory."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import inventory_missing_sequences as inventory_script

from glioma_selective.data import missing_sequences
from glioma_selective.data.adapters import CanonicalSequence, ucsf_pdgm, utsw


def _touch(directory: Path, filename: str) -> None:
    (directory / filename).write_bytes(b"synthetic fixture")


def _write_utsw_patient(
    root: Path,
    patient_id: str,
    present: set[CanonicalSequence],
) -> None:
    filenames = {
        CanonicalSequence.T1: "brain_t1.nii.gz",
        CanonicalSequence.T1CE: "brain_t1ce.nii.gz",
        CanonicalSequence.T2: "brain_t2.nii.gz",
        CanonicalSequence.FLAIR: "brain_flair.nii.gz",
    }
    patient_directory = root / patient_id
    patient_directory.mkdir(parents=True)
    for sequence in present:
        _touch(patient_directory, filenames[sequence])


def _write_ucsf_patient(
    root: Path,
    patient_id: str,
    present: set[CanonicalSequence],
) -> None:
    suffixes = {
        CanonicalSequence.T1: "_T1.nii.gz",
        CanonicalSequence.T1CE: "_T1c.nii.gz",
        CanonicalSequence.T2: "_T2.nii.gz",
        CanonicalSequence.FLAIR: "_FLAIR.nii.gz",
    }
    patient_directory = root / f"{patient_id}_nifti"
    patient_directory.mkdir(parents=True)
    for sequence in present:
        _touch(patient_directory, f"{patient_id}{suffixes[sequence]}")


def test_build_report_aggregates_complete_and_natural_missingness(
    tmp_path: Path,
) -> None:
    """Counts describe raw absence and never invent a replacement sequence."""

    utsw_root = tmp_path / "utsw"
    _write_utsw_patient(
        utsw_root,
        "SYN-001",
        set(CanonicalSequence),
    )
    _write_utsw_patient(
        utsw_root,
        "SYN-002",
        {CanonicalSequence.T1, CanonicalSequence.T1CE},
    )
    _write_utsw_patient(
        utsw_root,
        "SYN-003",
        {CanonicalSequence.T1, CanonicalSequence.T1CE, CanonicalSequence.FLAIR},
    )

    ucsf_root = tmp_path / "ucsf_pdgm"
    _write_ucsf_patient(
        ucsf_root,
        "SYN-101",
        set(CanonicalSequence),
    )
    _write_ucsf_patient(
        ucsf_root,
        "SYN-102",
        {CanonicalSequence.T1, CanonicalSequence.T2, CanonicalSequence.FLAIR},
    )

    report = missing_sequences.build_report(
        {
            "utsw": utsw.discover_files(utsw_root),
            "ucsf_pdgm": ucsf_pdgm.discover_files(ucsf_root),
        }
    )

    assert report["missingness"]["type"] == "naturally_occurring"
    assert report["missingness"]["simulated"] is False
    assert report["cohorts"]["utsw"] == {
        "patient_count": 3,
        "complete_patient_count": 1,
        "incomplete_patient_count": 2,
        "missing_sequence_patient_counts": {
            "T1": 0,
            "T1ce": 0,
            "T2": 2,
            "FLAIR": 1,
        },
        "missing_sequence_combinations": {"T2+FLAIR": 1, "T2": 1},
    }
    assert report["cohorts"]["ucsf_pdgm"] == {
        "patient_count": 2,
        "complete_patient_count": 1,
        "incomplete_patient_count": 1,
        "missing_sequence_patient_counts": {
            "T1": 0,
            "T1ce": 1,
            "T2": 0,
            "FLAIR": 0,
        },
        "missing_sequence_combinations": {"T1ce": 1},
    }
    assert "SYN-001" not in json.dumps(report)


def test_cli_writes_aggregate_report_without_patient_roster(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    """The operational JSON and stdout expose counts, never raw patient IDs."""

    root = tmp_path / "utsw"
    _write_utsw_patient(root, "SYN-001", set(CanonicalSequence))
    output = tmp_path / "inventory.json"
    monkeypatch.setitem(
        inventory_script._DISCOVERERS,
        "utsw",
        lambda: utsw.discover_files(root),
    )

    assert inventory_script.main(["--cohort", "utsw", "--output", str(output)]) == 0

    stdout = capsys.readouterr().out
    written = json.loads(output.read_text(encoding="utf-8"))
    assert "SYN-001" not in stdout
    assert "SYN-001" not in json.dumps(written)
    assert written["cohorts"]["utsw"]["complete_patient_count"] == 1

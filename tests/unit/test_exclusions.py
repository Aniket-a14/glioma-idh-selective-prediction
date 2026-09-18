"""Synthetic tests for the T03.5 UCSF-PDGM/BraTS exclusion roster."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from glioma_selective.leakage.exclusions import (
    BRATS_EXCLUSION_REASON,
    FOLLOWUP_TIMEPOINT_REASON,
    IDH_UNAVAILABLE_REASON,
    NO_IMAGING_AVAILABLE_REASON,
    ExclusionReportError,
    build_brats_exclusion_report,
    build_brats_exclusion_summary,
    build_exclusion_manifest,
    build_followup_timepoint_selection_record,
    verify_post_exclusion_no_brats_overlap,
    write_brats_exclusion_report,
)


def _details(*pairs: tuple[str, str]) -> dict[str, object]:
    return {"pairs": {"ucsf_pdgm|brats2021": [list(pair) for pair in pairs]}}


def test_builds_one_machine_readable_reason_per_normalized_source_patient() -> None:
    report = build_brats_exclusion_report(
        _details(
            ("UCSF-PDGM-001", "BraTS2021_00001"),
            ("ucsf-pdgm-0002", "brats21-00002"),
        )
    )

    assert report["excluded_patient_count"] == 2
    assert report["exclusions"] == [
        {"patient_id": "UCSF-PDGM-0001", "reason": BRATS_EXCLUSION_REASON},
        {"patient_id": "UCSF-PDGM-0002", "reason": BRATS_EXCLUSION_REASON},
    ]


def test_summary_is_aggregate_only_and_post_exclusion_check_is_direct() -> None:
    details = _details(
        ("UCSF-PDGM-001", "BraTS2021_00001"),
        ("UCSF-PDGM-0002", "BraTS2021_00002"),
    )
    report = build_brats_exclusion_report(details)
    summary = build_brats_exclusion_summary(report)
    verification = verify_post_exclusion_no_brats_overlap(
        ["UCSF-PDGM-0001", "UCSF-PDGM-0002", "UCSF-PDGM-0003"],
        report,
        details,
    )

    assert summary["excluded_patient_count"] == 2
    assert "exclusions" not in summary
    assert "UCSF-PDGM-0001" not in json.dumps(summary)
    assert verification == {
        "status": "verified",
        "ucsf_pdgm_input_patient_count": 3,
        "ucsf_pdgm_input_unique_patient_count": 3,
        "excluded_patient_count": 2,
        "ucsf_pdgm_remaining_patient_count": 1,
        "ucsf_pdgm_remaining_unique_patient_count": 1,
        "remaining_brats_overlap_count": 0,
    }


def test_written_roster_is_local_artifact_and_summary_has_no_roster(
    tmp_path: Path,
) -> None:
    report = build_brats_exclusion_report(
        _details(("UCSF-PDGM-0001", "BraTS2021_00001"))
    )
    roster_path = write_brats_exclusion_report(report, tmp_path / "roster.json")

    written = json.loads(roster_path.read_text(encoding="utf-8"))
    summary = build_brats_exclusion_summary(written)
    assert written["exclusions"][0]["reason"] == BRATS_EXCLUSION_REASON
    assert "UCSF-PDGM-0001" not in json.dumps(summary)


def test_post_exclusion_check_rejects_a_roster_that_leaves_an_overlap() -> None:
    details = _details(("UCSF-PDGM-0001", "BraTS2021_00001"))
    report = build_brats_exclusion_report(details)
    with pytest.raises(
        ExclusionReportError, match="does not equal the T03.4 UCSF source-ID pair set"
    ):
        verify_post_exclusion_no_brats_overlap(
            ["UCSF-PDGM-0001", "UCSF-PDGM-0002"],
            {**report, "exclusions": []},
            details,
        )


def test_combined_manifest_keeps_its_two_ucsf_bases_separate() -> None:
    brats_report = build_brats_exclusion_report(
        _details(
            ("UCSF-PDGM-0001", "BraTS2021_00001"),
            ("UCSF-PDGM-0003", "BraTS2021_00003"),
        )
    )
    manifest = build_exclusion_manifest(
        utsw_patient_ids=("BT0001", "BT0002", "BT0003"),
        utsw_idh_unavailable_ids=("BT0002",),
        ucsf_metadata_ids=(
            "UCSF-PDGM-001",
            "UCSF-PDGM-0002",
            "UCSF-PDGM-0003",
            "UCSF-PDGM-0004",
            "UCSF-PDGM-0005",
        ),
        ucsf_directory_ids=(
            "UCSF-PDGM-0001_nifti",
            "UCSF-PDGM-0002_nifti",
            "UCSF-PDGM-0003_nifti",
            "UCSF-PDGM-0003_FU001d_nifti",
            "UCSF-PDGM-0004_nifti",
        ),
        brats_exclusion_report=brats_report,
    )

    assert manifest["reason_counts"] == {
        IDH_UNAVAILABLE_REASON: 1,
        BRATS_EXCLUSION_REASON: 2,
        NO_IMAGING_AVAILABLE_REASON: 1,
    }
    assert manifest["excluded_patient_count"] == 4
    cohorts = manifest["cohorts"]
    assert isinstance(cohorts, dict)
    assert cohorts["utsw"]["retained_patient_count"] == 2
    assert cohorts["ucsf_pdgm"]["metadata_patient_count"] == 5
    assert cohorts["ucsf_pdgm"]["directory_backed_patient_count"] == 4
    assert cohorts["ucsf_pdgm"]["no_imaging_patient_count"] == 1
    assert cohorts["ucsf_pdgm"]["retained_patient_count"] == 2
    assert cohorts["ucsf_pdgm"]["excluded_patient_count"] == 3
    assert cohorts["ucsf_pdgm"]["followup_selection_count"] == 1
    checks = manifest["accounting_checks"]
    assert isinstance(checks, dict)
    assert checks["ucsf_metadata_partition"]["identity_holds"] is True
    assert checks["ucsf_directory_partition"]["identity_holds"] is True
    assert checks["ucsf_retained_cohort"]["identity_holds"] is True
    assert all(
        entry["reason"] != FOLLOWUP_TIMEPOINT_REASON for entry in manifest["exclusions"]
    )


def test_followup_selection_record_is_directory_level_and_retains_baseline() -> None:
    record = build_followup_timepoint_selection_record(
        (
            "UCSF-PDGM-0001_nifti",
            "UCSF-PDGM-0001_FU016d_nifti",
            "UCSF-PDGM-0002_nifti",
        )
    )

    assert record["selection_count"] == 1
    assert record["selections"] == [
        {
            "patient_id": "UCSF-PDGM-0001",
            "retained_directory": "UCSF-PDGM-0001_nifti",
            "excluded_directory": "UCSF-PDGM-0001_FU016d_nifti",
            "reason": FOLLOWUP_TIMEPOINT_REASON,
        }
    ]
    assert record["directory_accounting"] == {
        "raw_directory_count": 3,
        "directory_backed_patient_count": 2,
        "baseline_directory_count": 2,
        "followup_directory_count": 1,
    }


def test_followup_selection_requires_a_baseline_directory() -> None:
    with pytest.raises(ExclusionReportError, match="exactly one base directory"):
        build_followup_timepoint_selection_record(("UCSF-PDGM-0001_FU016d_nifti",))

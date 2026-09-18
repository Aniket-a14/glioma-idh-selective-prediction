"""Synthetic tests for the T03.5 UCSF-PDGM/BraTS exclusion roster."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from glioma_selective.leakage.exclusions import (
    BRATS_EXCLUSION_REASON,
    ExclusionReportError,
    build_brats_exclusion_report,
    build_brats_exclusion_summary,
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

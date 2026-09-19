"""Synthetic tests for the roster-free Phase 04 QC report."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.qc_report import (
    QCReportError,
    _agreement,
    _ReviewRow,
    _VerificationCase,
    build_qc_report,
)
from glioma_selective.preprocessing.status import PreprocessingStatusManifest
from glioma_selective.preprocessing.verification import CaseVerification


def _verification(
    patient_id: str,
    status: str,
    fraction: float,
    *,
    cohort: Cohort,
    failure_categories: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "cohort": cohort.value,
        "patient_id": patient_id,
        "status": status,
        "failure_categories": list(failure_categories),
        "borderline_checks": [],
        "brain_voxel_fraction": fraction,
        "cross_sequence_dice": {"T1": 1.0, "T1ce": 1.0},
    }


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    cases = [
        _verification("UTSW-BT0001", "verified-passthrough", 0.04, cohort=Cohort.UTSW),
        _verification(
            "UTSW-BT0002",
            "failed",
            0.09,
            cohort=Cohort.UTSW,
            failure_categories=("corrupt",),
        ),
        _verification("UTSW-BT0003", "verified-passthrough", 0.16, cohort=Cohort.UTSW),
        _verification(
            "UCSF-PDGM-0001", "verified-borderline", 0.07, cohort=Cohort.UCSF_PDGM
        ),
        _verification(
            "UCSF-PDGM-0002", "verified-passthrough", 0.14, cohort=Cohort.UCSF_PDGM
        ),
    ]
    verification_path = tmp_path / "preprocessing_verification_cases.json"
    verification_path.write_text(
        json.dumps({"schema_version": 2, "cases": cases}), encoding="utf-8"
    )

    results = [
        CaseVerification(
            cohort=Cohort(case["cohort"]),
            patient_id=case["patient_id"],
            status=case["status"],
            checks={},
            failure_categories=case["failure_categories"],
            borderline_checks=(),
            brain_voxel_fraction=case["brain_voxel_fraction"],
            cross_sequence_dice={"T1": 1.0},
            segmentation_findings={},
        )
        for case in cases
    ]
    status_path = tmp_path / "preprocessing_status.json"
    PreprocessingStatusManifest.from_verification(results).save(status_path)

    index_path = tmp_path / "qc_overlay_index.json"
    index_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "qc_keys": {
                    "qc_0001": {
                        "cohort": "utsw",
                        "patient_id": "UTSW-BT0001",
                    },
                    "qc_0002": {
                        "cohort": "utsw",
                        "patient_id": "UTSW-BT0002",
                    },
                    "qc_0003": {
                        "cohort": "ucsf_pdgm",
                        "patient_id": "UCSF-PDGM-0001",
                    },
                    "qc_0004": {
                        "cohort": "ucsf_pdgm",
                        "patient_id": "UCSF-PDGM-0002",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    review_path = tmp_path / "qc_review_sheet.csv"
    rows = [
        ("qc_0001", "utsw", "stratified", 0.04, "pass", "", "tail note"),
        ("qc_0002", "utsw", "tail", 0.09, "fail", "corrupt", "private note"),
        ("qc_0003", "ucsf_pdgm", "random", 0.07, "pass", "", "ignore this"),
        ("qc_0004", "ucsf_pdgm", "tail", 0.14, "fail", "orientation-wrong", "no copy"),
    ]
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "qc_key",
                "cohort",
                "selection_reason",
                "brain_voxel_fraction",
                "min_cross_sequence_dice",
                "reviewer_verdict",
                "failure_category",
                "notes",
            ]
        )
        for key, cohort, reason, fraction, verdict, category, notes in rows:
            writer.writerow(
                [
                    key,
                    cohort,
                    reason,
                    f"{fraction:.8f}",
                    "1.00000000",
                    verdict,
                    category,
                    notes,
                ]
            )
    return (
        status_path,
        verification_path,
        review_path,
        index_path,
        tmp_path / "report.json",
    )


def _build(tmp_path: Path) -> dict[str, object]:
    status, verification, review, index, output = _inputs(tmp_path)
    return build_qc_report(
        status_path=status,
        verification_path=verification,
        review_path=review,
        overlay_index_path=index,
        output_path=output,
    )


def test_report_has_hand_computed_agreement_and_sensitivity_counts(
    tmp_path: Path,
) -> None:
    report = _build(tmp_path)
    agreement = report["automated_vs_human_agreement"]["by_cohort"]
    assert agreement["utsw"]["automated_flag_vs_human_verdict"] == {
        "automated_flagged__human_pass": 0,
        "automated_flagged__human_fail": 1,
        "automated_clear__human_pass": 1,
        "automated_clear__human_fail": 0,
    }
    assert agreement["ucsf_pdgm"]["automated_flag_vs_human_verdict"] == {
        "automated_flagged__human_pass": 1,
        "automated_flagged__human_fail": 0,
        "automated_clear__human_pass": 0,
        "automated_clear__human_fail": 1,
    }
    assert report["screen_bounds"] == {
        "original_lower_bound": 0.08,
        "current_lower_bound": 0.13,
        "provisional": True,
    }
    interpretation = report["automated_vs_human_agreement"]["interpretation"]
    assert "recalibrated D-031 screen" in interpretation
    assert "in-sample" in interpretation
    sensitivity = report["threshold_sensitivity"][
        "candidate_lower_brain_fraction_bounds"
    ]
    assert sensitivity["0.10"] == {
        "all_cases_below_by_cohort": {"ucsf_pdgm": 1, "utsw": 2},
        "reviewed_cases_below": {"fail": 1, "pass": 2},
    }
    assert report["provenance"]["reviewed_rows_without_verdict"] == 0


def test_agreement_distinguishes_original_and_current_screen_bounds() -> None:
    rows = [
        _ReviewRow("qc_0001", Cohort.UTSW, "tail", 0.05, "fail", "corrupt"),
        _ReviewRow("qc_0002", Cohort.UTSW, "tail", 0.10, "fail", "corrupt"),
    ]
    verification = {
        (Cohort.UTSW, "case-1"): _VerificationCase(
            Cohort.UTSW, "case-1", "verified-borderline", 0.05, ("corrupt",)
        ),
        (Cohort.UTSW, "case-2"): _VerificationCase(
            Cohort.UTSW, "case-2", "verified-borderline", 0.10, ("corrupt",)
        ),
    }

    agreement = _agreement(
        rows,
        {"qc_0001": (Cohort.UTSW, "case-1"), "qc_0002": (Cohort.UTSW, "case-2")},
        verification,
    )
    cohort = agreement["by_cohort"]["utsw"]
    assert cohort["automated_flag_vs_human_verdict"] == {
        "automated_flagged__human_pass": 0,
        "automated_flagged__human_fail": 2,
        "automated_clear__human_pass": 0,
        "automated_clear__human_fail": 0,
    }
    assert cohort["human_failures_flagged_at_original_bound"] == 1
    assert [
        failure["flagged_at_original_bound"] for failure in cohort["human_failures"]
    ] == [True, False]


def test_serialized_report_contains_no_ids_or_notes(tmp_path: Path) -> None:
    _build(tmp_path)
    serialized = (tmp_path / "report.json").read_text(encoding="utf-8")
    assert "UTSW-BT0001" not in serialized
    assert "UCSF-PDGM-0001" not in serialized
    assert "private note" not in serialized
    assert "tail note" not in serialized


def test_unresolved_verdict_is_an_error(tmp_path: Path) -> None:
    status, verification, review, index, output = _inputs(tmp_path)
    content = review.read_text(encoding="utf-8").replace(",pass,", ",,")
    review.write_text(content, encoding="utf-8")
    with pytest.raises(QCReportError, match="without a verdict"):
        build_qc_report(
            status_path=status,
            verification_path=verification,
            review_path=review,
            overlay_index_path=index,
            output_path=output,
        )


def test_cohort_or_fraction_mismatch_is_an_error(tmp_path: Path) -> None:
    status, verification, review, index, output = _inputs(tmp_path)
    content = review.read_text(encoding="utf-8").replace("0.09000000", "0.12000000")
    review.write_text(content, encoding="utf-8")
    with pytest.raises(QCReportError, match="mismatch count: 1"):
        build_qc_report(
            status_path=status,
            verification_path=verification,
            review_path=review,
            overlay_index_path=index,
            output_path=output,
        )

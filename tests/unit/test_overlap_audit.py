"""Synthetic tests for the Phase 03 full overlap matrix."""

from __future__ import annotations

import json
from pathlib import Path

from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.leakage.overlap_audit import (
    BRATS_TEST_SET_CAVEAT,
    EGD_NOT_AVAILABLE_REASON,
    build_overlap_matrix,
    write_overlap_detail_report,
    write_overlap_report,
)


def test_matrix_records_every_requested_cell_and_expected_empty_results() -> None:
    report = build_overlap_matrix(
        {
            Cohort.UTSW: ["BT0001", "BT0002"],
            Cohort.UCSF_PDGM: ["UCSF-PDGM-0002", "UCSF-PDGM-0003"],
            Cohort.BRATS_2021: ["BraTS2021_00001"],
            Cohort.TCGA_GBM: ["TCGA-AA-0001"],
            Cohort.TCGA_LGG: ["TCGA-BB-0001"],
        }
    )

    matrix = report["matrix"]
    assert set(matrix) == {"utsw", "ucsf_pdgm", "egd"}
    assert all(
        set(row) == {"brats2021", "tcga_gbm", "tcga_lgg", "ucsf_pdgm", "egd"}
        for row in matrix.values()
    )
    assert matrix["utsw"]["tcga_gbm"]["status"] == "checked"
    assert matrix["utsw"]["tcga_gbm"]["overlap_count"] == 0
    assert matrix["ucsf_pdgm"]["ucsf_pdgm"]["status"] == "not_applicable"
    assert matrix["egd"]["ucsf_pdgm"]["status"] == "not_yet_available"
    assert matrix["egd"]["ucsf_pdgm"]["reason"] == EGD_NOT_AVAILABLE_REASON
    assert matrix["utsw"]["brats2021"]["brats_coverage_caveat"] == (
        BRATS_TEST_SET_CAVEAT
    )


def test_ucsf_brats_crosswalk_pair_overrides_different_namespaces() -> None:
    report = build_overlap_matrix(
        {
            Cohort.UTSW: ["BT0001"],
            Cohort.UCSF_PDGM: ["UCSF-PDGM-0001"],
            Cohort.BRATS_2021: ["BraTS2021_00001"],
            Cohort.TCGA_GBM: ["TCGA-AA-0001"],
            Cohort.TCGA_LGG: ["TCGA-BB-0001"],
        },
        pair_details={
            (Cohort.UCSF_PDGM, Cohort.BRATS_2021): (
                ("UCSF-PDGM-0001", "BraTS2021_00001"),
            )
        },
        source_notes={"crosscheck": {"status": "disagreement"}},
    )

    cell = report["matrix"]["ucsf_pdgm"]["brats2021"]
    assert cell["status"] == "checked"
    assert cell["overlap_count"] == 1
    assert cell["must_resolve_before_external_use"] is True
    assert cell["comparison_basis"] == "authoritative_crosswalk_pair_intersection"
    assert report["source_notes"]["crosscheck"]["status"] == "disagreement"


def test_reports_write_to_caller_selected_derived_paths_without_roster_in_summary(
    tmp_path: Path,
) -> None:
    report = build_overlap_matrix(
        {
            Cohort.UTSW: ["BT0001"],
            Cohort.UCSF_PDGM: ["UCSF-PDGM-0001"],
            Cohort.BRATS_2021: ["BraTS2021_00001"],
            Cohort.TCGA_GBM: ["TCGA-AA-0001"],
            Cohort.TCGA_LGG: ["TCGA-BB-0001"],
        },
        pair_details={
            (Cohort.UCSF_PDGM, Cohort.BRATS_2021): (
                ("UCSF-PDGM-0001", "BraTS2021_00001"),
            )
        },
    )
    aggregate_path = write_overlap_report(report, tmp_path / "overlap.json")
    detail_path = write_overlap_detail_report(
        {"pairs": {"ucsf_pdgm|brats2021": [["SYNTHETIC-A", "SYNTHETIC-B"]]}},
        tmp_path / "detail.json",
    )

    aggregate = json.loads(aggregate_path.read_text(encoding="utf-8"))
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    assert aggregate["matrix"]["utsw"]["brats2021"]["overlap_count"] == 0
    assert "SYNTHETIC-A" not in aggregate_path.read_text(encoding="utf-8")
    assert detail["pairs"]["ucsf_pdgm|brats2021"] == [["SYNTHETIC-A", "SYNTHETIC-B"]]

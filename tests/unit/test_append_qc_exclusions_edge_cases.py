"""Mutation-targeted edge-case tests for the Phase 04 QC append operation."""

from __future__ import annotations

import copy
from typing import cast

import pytest

from glioma_selective.leakage.exclusions import (
    ExclusionReportError,
    append_qc_exclusions,
)


def _base_manifest() -> dict[str, object]:
    return {
        "manifest_version": 1,
        "generated_by": "T03.10 exclusion manifest",
        "exclusions": [
            {
                "cohort": "utsw",
                "patient_id": "BT0001",
                "reason": "label:idh_unavailable",
            },
            {
                "cohort": "ucsf_pdgm",
                "patient_id": "UCSF-PDGM-0001",
                "reason": "overlap:brats2021",
            },
        ],
        "excluded_patient_count": 2,
        "reason_counts": {
            "label:idh_unavailable": 1,
            "overlap:brats2021": 1,
        },
        "cohorts": {
            "utsw": {
                "source_patient_count": 4,
                "excluded_patient_count": 1,
                "retained_patient_count": 3,
                "reason_counts": {"label:idh_unavailable": 1},
            },
            "ucsf_pdgm": {
                "metadata_patient_count": 3,
                "directory_backed_patient_count": 3,
                "no_imaging_patient_count": 0,
                "excluded_patient_count": 1,
                "retained_patient_count": 2,
                "reason_counts": {"overlap:brats2021": 1},
            },
        },
        "accounting_checks": {"pre_qc_check": True},
    }


def _rows(manifest: dict[str, object]) -> list[dict[str, object]]:
    rows = manifest["exclusions"]
    assert isinstance(rows, list)
    return cast(list[dict[str, object]], rows)


def _cohorts(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    cohorts = manifest["cohorts"]
    assert isinstance(cohorts, dict)
    return cast(dict[str, dict[str, object]], cohorts)


def test_normalizes_lowercase_and_padded_ids() -> None:
    updated = append_qc_exclusions(
        _base_manifest(),
        [
            ("utsw", "utsw_bt_0003", ("qc:corrupt",)),
            ("ucsf_pdgm", "ucsf-pdgm-002", ("qc:orientation-wrong",)),
        ],
    )

    assert _rows(updated)[-2:] == [
        {
            "cohort": "ucsf_pdgm",
            "patient_id": "UCSF-PDGM-0002",
            "reason": "qc:orientation-wrong",
        },
        {
            "cohort": "utsw",
            "patient_id": "UTSW-BT0003",
            "reason": "qc:corrupt",
        },
    ]


def test_deduplicates_and_sorts_reasons_for_one_patient() -> None:
    updated = append_qc_exclusions(
        _base_manifest(),
        [
            (
                "utsw",
                "BT0003",
                ("qc:n4-artifact", "qc:corrupt", "qc:n4-artifact"),
            )
        ],
    )

    assert _rows(updated)[-1]["reason"] == "qc:corrupt+qc:n4-artifact"
    assert updated["reason_counts"]["qc:corrupt+qc:n4-artifact"] == 1


def test_updates_one_cohort_without_changing_the_other() -> None:
    original = _base_manifest()
    updated = append_qc_exclusions(
        original,
        [("ucsf_pdgm", "UCSF-PDGM-002", ("qc:corrupt",))],
    )

    cohorts = _cohorts(updated)
    assert cohorts["utsw"]["reason_counts"] == {"label:idh_unavailable": 1}
    assert cohorts["utsw"]["excluded_patient_count"] == 1
    assert cohorts["utsw"]["retained_patient_count"] == 3
    assert cohorts["utsw"]["qc_excluded_patient_count"] == 0
    assert cohorts["ucsf_pdgm"]["qc_excluded_patient_count"] == 1


def test_reason_counts_sum_to_excluded_counts_per_cohort() -> None:
    updated = append_qc_exclusions(
        _base_manifest(),
        [
            ("utsw", "BT0002", ("qc:corrupt",)),
            ("utsw", "BT0003", ("qc:n4-artifact",)),
            ("ucsf_pdgm", "UCSF-PDGM-002", ("qc:orientation-wrong",)),
        ],
    )

    cohorts = _cohorts(updated)
    for cohort in ("utsw", "ucsf_pdgm"):
        reasons = cast(dict[str, int], cohorts[cohort]["reason_counts"])
        assert sum(reasons.values()) == cohorts[cohort]["excluded_patient_count"]


def test_does_not_mutate_the_qc_input_or_nested_manifest() -> None:
    manifest = _base_manifest()
    qc_exclusions = [
        ("utsw", "UTSW_BT_0003", ("qc:corrupt",)),
        ("ucsf_pdgm", "UCSF-PDGM-002", ("qc:orientation-wrong",)),
    ]
    original_manifest = copy.deepcopy(manifest)
    original_qc_exclusions = copy.deepcopy(qc_exclusions)

    updated = append_qc_exclusions(manifest, qc_exclusions)

    assert manifest == original_manifest
    assert qc_exclusions == original_qc_exclusions
    assert updated is not manifest
    assert updated["exclusions"] is not manifest["exclusions"]
    _rows(updated)[0]["reason"] = "mutated"
    updated_checks = cast(dict[str, object], updated["accounting_checks"])
    updated_checks["pre_qc_check"] = False
    assert _rows(manifest)[0]["reason"] == "label:idh_unavailable"
    assert manifest["accounting_checks"] == {"pre_qc_check": True}


@pytest.mark.parametrize(
    ("record", "message"),
    [
        (("utsw", "BT01", ("qc:corrupt",)), "invalid QC exclusion patient ID"),
        (("utsw", 123, ("qc:corrupt",)), "patient_id must be a string"),
        (("utsw", "BT0003", "qc:corrupt"), "reasons must be a non-empty tuple"),
        (("utsw", "BT0003"), "each QC exclusion must be"),
    ],
)
def test_rejected_records_raise_the_documented_error_type(
    record: object, message: str
) -> None:
    with pytest.raises(ExclusionReportError, match=message):
        append_qc_exclusions(_base_manifest(), [record])  # type: ignore[list-item]


def test_rejects_malformed_top_level_reason_counts() -> None:
    manifest = _base_manifest()
    manifest["reason_counts"] = {"label:idh_unavailable": -1}

    with pytest.raises(ExclusionReportError, match="reason_counts is malformed"):
        append_qc_exclusions(
            manifest,
            [("utsw", "BT0003", ("qc:corrupt",))],
        )

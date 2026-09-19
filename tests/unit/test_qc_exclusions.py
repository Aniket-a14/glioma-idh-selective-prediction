"""Synthetic tests for the Phase 04 QC exclusion layer."""

from __future__ import annotations

import copy
import json
from typing import cast

import pytest

import glioma_selective.preprocessing.status as status_module
from glioma_selective.leakage.cohort_manifest import build_cohort_manifest
from glioma_selective.leakage.exclusions import (
    QC_CATEGORIES,
    ExclusionReportError,
    append_qc_exclusions,
)
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.qc_exclusions import qc_exclusion_records
from glioma_selective.preprocessing.status import PreprocessingStatusManifest
from glioma_selective.preprocessing.verification import CaseVerification


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


def test_category_constant_matches_status_contract() -> None:
    assert QC_CATEGORIES == status_module._QC_CATEGORIES


def test_append_updates_rows_counts_and_keeps_accounting_untouched() -> None:
    manifest = _base_manifest()
    original = copy.deepcopy(manifest)
    updated = append_qc_exclusions(
        manifest,
        (
            ("utsw", "UTSW_BT_0003", ("qc:skullstrip-over", "qc:corrupt")),
            ("ucsf_pdgm", "UCSF-PDGM-002", ("qc:orientation-wrong",)),
        ),
    )

    assert manifest == original
    assert updated["exclusions"] == [
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
        {
            "cohort": "ucsf_pdgm",
            "patient_id": "UCSF-PDGM-0002",
            "reason": "qc:orientation-wrong",
        },
        {
            "cohort": "utsw",
            "patient_id": "UTSW-BT0003",
            "reason": "qc:corrupt+qc:skullstrip-over",
        },
    ]
    assert updated["excluded_patient_count"] == 4
    assert updated["qc_exclusion_count"] == 2
    assert updated["reason_counts"] == {
        "label:idh_unavailable": 1,
        "overlap:brats2021": 1,
        "qc:corrupt": 1,
        "qc:orientation-wrong": 1,
        "qc:skullstrip-over": 1,
    }
    cohorts = cast(dict[str, dict[str, object]], updated["cohorts"])
    assert cohorts["utsw"]["retained_patient_count"] == 2
    assert cohorts["utsw"]["qc_excluded_patient_count"] == 1
    assert cohorts["ucsf_pdgm"]["retained_patient_count"] == 1
    assert cohorts["ucsf_pdgm"]["qc_excluded_patient_count"] == 1
    assert updated["accounting_checks"] == {"pre_qc_check": True}
    assert updated["accounting_checks_scope"] == "pre-QC"
    assert updated["generated_by"] == "T03.10 exclusion manifest + T04.12 QC exclusions"


@pytest.mark.parametrize(
    ("records", "message"),
    [
        ((("egd", "EGD-1", ("qc:corrupt",)),), "unknown QC exclusion cohort"),
        (
            (("utsw", "BT0002", ("qc:not-a-category",)),),
            "unknown or non-qc reason",
        ),
        ((("utsw", "BT0002", ("corrupt",)),), "unknown or non-qc reason"),
        ((("utsw", "BT0002", ()),), "must not be empty"),
        (
            (
                ("utsw", "BT0002", ("qc:corrupt",)),
                ("utsw", "UTSW_BT_0002", ("qc:n4-artifact",)),
            ),
            "duplicate patient",
        ),
        (
            (("utsw", "BT0001", ("qc:corrupt",)),),
            "already present",
        ),
    ],
)
def test_append_rejects_malformed_or_contradictory_input(
    records: tuple[tuple[str, str, tuple[str, ...]], ...], message: str
) -> None:
    with pytest.raises(ExclusionReportError, match=message):
        append_qc_exclusions(_base_manifest(), records)


def test_append_rejects_a_cohort_count_that_would_go_negative() -> None:
    manifest = _base_manifest()
    cohorts = cast(dict[str, dict[str, object]], manifest["cohorts"])
    cohorts["utsw"]["retained_patient_count"] = 0
    with pytest.raises(ExclusionReportError, match="negative"):
        append_qc_exclusions(manifest, (("utsw", "BT0002", ("qc:corrupt",)),))


def test_empty_qc_input_is_a_copy_with_zero_qc_count() -> None:
    manifest = _base_manifest()
    updated = append_qc_exclusions(manifest, ())
    assert updated is not manifest
    assert updated["exclusions"] == manifest["exclusions"]
    assert updated["qc_exclusion_count"] == 0
    assert updated["cohorts"]["utsw"]["qc_excluded_patient_count"] == 0


def test_post_qc_manifest_round_trip_requires_removing_qc_ids_from_roster() -> None:
    post = append_qc_exclusions(
        _base_manifest(), (("utsw", "BT0002", ("qc:corrupt",)),)
    )
    post_manifest = build_cohort_manifest(
        post,
        {
            Cohort.UTSW: ("BT0003", "BT0004"),
            Cohort.UCSF_PDGM: ("UCSF-PDGM-0002", "UCSF-PDGM-0003"),
        },
        generated_at="2026-09-19T00:00:00+00:00",
    )
    assert post_manifest["cohorts"]["utsw"]["retained_patient_count"] == 2
    with pytest.raises(ValueError, match="retained roster has 3 IDs"):
        build_cohort_manifest(
            post,
            {
                Cohort.UTSW: ("BT0002", "BT0003", "BT0004"),
                Cohort.UCSF_PDGM: ("UCSF-PDGM-0002", "UCSF-PDGM-0003"),
            },
        )


def _verification(
    patient_id: str,
    status: str = "verified-passthrough",
    *,
    cohort: Cohort = Cohort.UTSW,
) -> CaseVerification:
    return CaseVerification(
        cohort=cohort,
        patient_id=patient_id,
        status=status,
        checks={},
        failure_categories=(),
        borderline_checks=(),
        brain_voxel_fraction=None,
        cross_sequence_dice={},
        segmentation_findings={},
    )


def test_qc_records_include_visual_failures_and_explicit_exclusions() -> None:
    status = PreprocessingStatusManifest.from_verification(
        (
            _verification("BT0001"),
            _verification("BT0002"),
            _verification("UCSF-PDGM-0001", cohort=Cohort.UCSF_PDGM),
        )
    )
    status = status.record_visual_qc_verdict("utsw", "BT0001", "failed", "corrupt")
    status = status.record_exclusion("utsw", "BT0002", ("n4-artifact", "corrupt"))
    assert qc_exclusion_records(status) == (
        ("utsw", "BT0001", ("qc:corrupt",)),
        ("utsw", "BT0002", ("qc:n4-artifact", "qc:corrupt")),
    )


def test_qc_records_reject_unresolved_automated_failure_without_id_in_error() -> None:
    status = PreprocessingStatusManifest.from_verification(
        (_verification("BT0099", "failed"),)
    )
    with pytest.raises(ValueError, match="1 automated QC failures") as error:
        qc_exclusion_records(status)
    assert "BT0099" not in str(error.value)


def test_qc_records_without_exclusions_are_empty() -> None:
    status = PreprocessingStatusManifest.from_verification((_verification("BT0001"),))
    assert qc_exclusion_records(status) == ()


def test_qc_records_are_json_safe_and_have_no_unexpected_ids_in_aggregate() -> None:
    status = PreprocessingStatusManifest.from_verification((_verification("BT0001"),))
    assert json.dumps(qc_exclusion_records(status))

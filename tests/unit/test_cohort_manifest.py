"""Synthetic tests for the T03.11 roster hash and committed manifest."""

from __future__ import annotations

import json

import pytest

from glioma_selective.leakage.cohort_manifest import (
    ROSTER_CONSTRUCTION,
    CohortManifestError,
    build_cohort_manifest,
    compute_roster_sha256,
    verify_roster_digest,
)
from glioma_selective.leakage.id_normalization import Cohort


def _synthetic_exclusion_manifest() -> dict[str, object]:
    return {
        "cohorts": {
            "utsw": {
                "retained_patient_count": 2,
                "excluded_patient_count": 1,
                "reason_counts": {"label:idh_unavailable": 1},
            },
            "ucsf_pdgm": {
                "retained_patient_count": 2,
                "excluded_patient_count": 1,
                "reason_counts": {"overlap:brats2021": 1},
            },
        },
        "exclusions": [],
    }


def test_hash_is_sorted_normalized_and_has_no_trailing_newline() -> None:
    digest = compute_roster_sha256(("bt-0002", "UTSW_BT_0001"), Cohort.UTSW)

    assert digest == "84867bce6d14f3b5ef050bb3e98b66b970a390dc36b263f1c3fc5eadc7a47040"
    assert digest == compute_roster_sha256(("BT0001", "BT0002"), Cohort.UTSW)


def test_manifest_contains_only_aggregate_hash_fields_and_verifies() -> None:
    manifest = build_cohort_manifest(
        _synthetic_exclusion_manifest(),
        {
            Cohort.UTSW: ("BT0002", "BT0001"),
            Cohort.UCSF_PDGM: ("UCSF-PDGM-002", "UCSF-PDGM-001"),
        },
        generated_at="2026-09-18T00:00:00+00:00",
    )

    assert manifest["manifest_version"] == 1
    assert manifest["cohorts"]["utsw"]["roster_sha256"] == (
        "84867bce6d14f3b5ef050bb3e98b66b970a390dc36b263f1c3fc5eadc7a47040"
    )
    assert manifest["cohorts"]["ucsf_pdgm"]["roster_sha256"] == (
        "9994c08367838894af32b7ef3564fd088da723699862c4b3f44c229f622ba151"
    )
    assert manifest["cohorts"]["utsw"]["roster_construction"] == ROSTER_CONSTRUCTION
    serialized = json.dumps(manifest)
    assert "patient_id" not in serialized
    assert "BT0001" not in serialized
    assert "UCSF-PDGM-0001" not in serialized

    assert (
        verify_roster_digest(manifest, Cohort.UTSW, ("BT0001", "BT0002"))["status"]
        == "verified"
    )
    assert (
        verify_roster_digest(
            manifest, Cohort.UCSF_PDGM, ("UCSF-PDGM-001", "UCSF-PDGM-002")
        )["status"]
        == "verified"
    )


def test_verifier_rejects_a_changed_roster() -> None:
    manifest = build_cohort_manifest(
        _synthetic_exclusion_manifest(),
        {
            Cohort.UTSW: ("BT0001", "BT0002"),
            Cohort.UCSF_PDGM: ("UCSF-PDGM-001", "UCSF-PDGM-002"),
        },
    )

    with pytest.raises(CohortManifestError, match="digest mismatch"):
        verify_roster_digest(manifest, Cohort.UTSW, ("BT0001", "BT0003"))

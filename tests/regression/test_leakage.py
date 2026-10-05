"""Phase 03 leakage regression guards.

The real-data tests run for real, against real cohort data, on any machine
that has ``GLIOMA_STORAGE_ROOT`` configured and the governed inventories on
disk (a developer's machine, the GPU server) — they deliberately fail rather
than pass silently if that data is present but inconsistent. On a bare CI
runner with no access to the external SSD (this project's data never leaves
local machines by design, per ``DATA_GOVERNANCE_PROTOCOL.md``), those same
checks skip with an explicit reason instead of erroring the whole suite —
skipping honestly reflects "this environment cannot check this," which is
different from "this was checked and passed." The synthetic planted-leakage
test needs no real data and always runs unconditionally, in every
environment, same as every EGD/split-manifest skip already in this file.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import cast

import pytest

from glioma_selective.data.adapters import ucsf_pdgm
from glioma_selective.leakage.cohort_manifest import (
    build_real_cohort_manifest,
    build_real_retained_rosters,
    verify_roster_digest,
)
from glioma_selective.leakage.exclusions import (
    ExclusionReportError,
    build_brats_exclusion_report,
    build_real_exclusion_manifest,
    verify_post_exclusion_no_brats_overlap,
)
from glioma_selective.leakage.id_normalization import Cohort, normalize_identifier
from glioma_selective.leakage.overlap_audit import build_real_overlap_audit
from glioma_selective.preprocessing.qc_exclusions import qc_exclusion_records
from glioma_selective.preprocessing.status import PreprocessingStatusManifest
from glioma_selective.utils import paths
from glioma_selective.utils.paths import PathResolutionError

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COHORT_MANIFEST_PATH = (
    REPOSITORY_ROOT / "docs" / "research" / "manifests" / "cohort_manifest.json"
)
SPLIT_MANIFEST_PATH = REPOSITORY_ROOT / "data" / "manifests" / "splits.json"
POST_QC_COHORT_MANIFEST_PATH = (
    REPOSITORY_ROOT / "docs" / "research" / "manifests" / "cohort_manifest_post_qc.json"
)


def _json_object(value: object, context: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssertionError(f"{context} must be a JSON object")
    return cast(dict[str, object], value)


@pytest.fixture(scope="session")
def real_phase03_artifacts() -> dict[str, object]:
    """Build all Phase 03 guards from the configured real inventories.

    Skips the whole real-data suite when the governed cohort data isn't
    reachable in this environment (``GLIOMA_STORAGE_ROOT`` unset, or set but
    the raw/external directories this task depends on aren't actually
    present — both expected on a bare CI runner). Any other failure inside
    this fixture is a real defect and must propagate, not be swallowed.
    """

    try:
        committed_manifest = _json_object(
            json.loads(COHORT_MANIFEST_PATH.read_text(encoding="utf-8")),
            "cohort manifest",
        )
        exclusion_manifest = build_real_exclusion_manifest()
        overlap_summary, overlap_details = build_real_overlap_audit()
        fresh_cohort_manifest = build_real_cohort_manifest()
        retained_rosters = build_real_retained_rosters(exclusion_manifest)
        brats_exclusion_report = build_brats_exclusion_report(overlap_details)
    except (PathResolutionError, FileNotFoundError, NotADirectoryError) as error:
        pytest.skip(
            "governed Phase 03 cohort data not reachable in this environment "
            f"(GLIOMA_STORAGE_ROOT unset or unmounted): {error}"
        )
    return {
        "committed_manifest": committed_manifest,
        "exclusion_manifest": exclusion_manifest,
        "overlap_summary": overlap_summary,
        "overlap_details": overlap_details,
        "fresh_cohort_manifest": fresh_cohort_manifest,
        "retained_rosters": retained_rosters,
        "brats_exclusion_report": brats_exclusion_report,
    }


def test_real_cohort_manifest_digests_match_fresh_rosters(
    real_phase03_artifacts: dict[str, object],
) -> None:
    """The committed roster-free manifest must match a fresh real rebuild."""

    committed = _json_object(real_phase03_artifacts["committed_manifest"], "committed")
    fresh = _json_object(real_phase03_artifacts["fresh_cohort_manifest"], "fresh")
    rosters = real_phase03_artifacts["retained_rosters"]
    assert isinstance(rosters, dict)

    assert _json_object(committed["cohorts"], "committed.cohorts") == _json_object(
        fresh["cohorts"], "fresh.cohorts"
    )
    for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
        verification = verify_roster_digest(committed, cohort, rosters[cohort])
        assert verification["status"] == "verified"


def test_real_utsw_and_ucsf_pdgm_are_disjoint(
    real_phase03_artifacts: dict[str, object],
) -> None:
    """The real normalized UTSW/UCSF-PDGM intersection remains empty."""

    summary = _json_object(real_phase03_artifacts["overlap_summary"], "overlap")
    matrix = _json_object(summary["matrix"], "overlap.matrix")
    utsw_row = _json_object(matrix["utsw"], "overlap.matrix.utsw")
    cell = _json_object(utsw_row["ucsf_pdgm"], "overlap.matrix.utsw.ucsf_pdgm")
    assert cell["status"] == "checked"
    assert cell["overlap_count"] == 0


def test_real_ucsf_pdgm_has_no_post_exclusion_brats_overlap(
    real_phase03_artifacts: dict[str, object],
) -> None:
    """The real UCSF-PDGM inventory is clean after the shipped exclusion."""

    details = _json_object(real_phase03_artifacts["overlap_details"], "overlap_details")
    report = _json_object(
        real_phase03_artifacts["brats_exclusion_report"], "brats_exclusion_report"
    )
    verification = verify_post_exclusion_no_brats_overlap(
        (item.patient_id for item in ucsf_pdgm.discover_files()),
        report,
        details,
    )
    assert verification["status"] == "verified"
    assert verification["remaining_brats_overlap_count"] == 0


def test_real_excluded_ids_are_absent_from_retained_rosters(
    real_phase03_artifacts: dict[str, object],
) -> None:
    """No ID excluded by T03.10 may re-enter either retained roster."""

    exclusion_manifest = _json_object(
        real_phase03_artifacts["exclusion_manifest"], "exclusion_manifest"
    )
    rosters = real_phase03_artifacts["retained_rosters"]
    assert isinstance(rosters, dict)
    excluded_by_cohort: dict[Cohort, set[str]] = {
        Cohort.UTSW: set(),
        Cohort.UCSF_PDGM: set(),
    }
    exclusions = exclusion_manifest["exclusions"]
    assert isinstance(exclusions, list)
    for raw_entry in exclusions:
        entry = _json_object(raw_entry, "exclusion entry")
        cohort = Cohort(entry["cohort"])
        if cohort in excluded_by_cohort:
            excluded_by_cohort[cohort].add(
                normalize_identifier(entry["patient_id"], cohort)
            )

    for cohort, excluded_ids in excluded_by_cohort.items():
        assert excluded_ids.isdisjoint(set(rosters[cohort]))


def test_real_pre_and_post_qc_roster_digests_remain_consistent() -> None:
    """Verify both frozen stages when the SSD post-QC artifact is available."""

    try:
        manifests_dir = paths.manifests_dir()
    except PathResolutionError as error:
        pytest.skip(f"post-QC SSD manifest is unavailable: {error}")
    post_exclusion_path = manifests_dir / "exclusion_manifest_post_qc.json"
    if not post_exclusion_path.exists() or not POST_QC_COHORT_MANIFEST_PATH.exists():
        pytest.skip(
            "post-QC exclusion and committed cohort manifests are not both available"
        )
    status_path = manifests_dir / "preprocessing_status.json"
    if not status_path.exists():
        pytest.skip("preprocessing status manifest is unavailable for QC IDs")

    post_exclusion = _json_object(
        json.loads(post_exclusion_path.read_text(encoding="utf-8")),
        "post-QC exclusion manifest",
    )
    post_cohort_manifest = _json_object(
        json.loads(POST_QC_COHORT_MANIFEST_PATH.read_text(encoding="utf-8")),
        "post-QC cohort manifest",
    )
    pre_cohort_manifest = _json_object(
        json.loads(COHORT_MANIFEST_PATH.read_text(encoding="utf-8")),
        "pre-QC cohort manifest",
    )
    records = qc_exclusion_records(PreprocessingStatusManifest.load(status_path))
    qc_ids: dict[Cohort, set[str]] = {}
    for cohort_name, patient_id, _ in records:
        cohort = Cohort(cohort_name)
        qc_ids.setdefault(cohort, set()).add(normalize_identifier(patient_id, cohort))

    pre_exclusion = build_real_exclusion_manifest()
    pre_rosters = build_real_retained_rosters(pre_exclusion)
    post_rosters = build_real_retained_rosters(post_exclusion)
    for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
        assert set(post_rosters[cohort]) == set(pre_rosters[cohort]) - qc_ids.get(
            cohort, set()
        )
        assert (
            verify_roster_digest(pre_cohort_manifest, cohort, pre_rosters[cohort])[
                "status"
            ]
            == "verified"
        )
        assert (
            verify_roster_digest(post_cohort_manifest, cohort, post_rosters[cohort])[
                "status"
            ]
            == "verified"
        )


def test_planted_leakage_fails_closed() -> None:
    """A synthetic missing exclusion must raise instead of passing silently."""

    overlap_details = {
        "pairs": {
            "ucsf_pdgm|brats2021": [
                ["UCSF-PDGM-9999", "BraTS2021_99999"],
            ]
        }
    }
    correct_report = build_brats_exclusion_report(overlap_details)
    planted_leakage_report = {**correct_report, "exclusions": []}

    with pytest.raises(
        ExclusionReportError,
        match="exclusion roster does not equal the T03.4 UCSF source-ID pair set",
    ):
        verify_post_exclusion_no_brats_overlap(
            ["UCSF-PDGM-9999", "UCSF-PDGM-9998"],
            planted_leakage_report,
            overlap_details,
        )


def test_egd_overlap_check_is_deferred_until_egd_arrives() -> None:
    """EGD is unavailable under D-018, so this check is explicitly deferred."""

    pytest.skip("EGD not downloaded — D-018")


def test_split_leakage_checks_wait_for_phase_05_manifest(
    request: pytest.FixtureRequest,
) -> None:
    """Run the split assertions whenever the frozen split manifest is available."""

    if not SPLIT_MANIFEST_PATH.exists():
        pytest.skip("frozen split manifest not found (storage not mounted?)")

    real_phase03_artifacts = cast(
        dict[str, object], request.getfixturevalue("real_phase03_artifacts")
    )

    split_document = _json_object(
        json.loads(SPLIT_MANIFEST_PATH.read_text(encoding="utf-8")),
        "split manifest",
    )
    split_mapping = split_document.get("splits")
    if not isinstance(split_mapping, dict):
        raise AssertionError("split manifest must contain a splits object")
    expected_names = {"train", "calibration", "internal_test"}
    assert set(split_mapping) == expected_names

    split_sets: dict[str, set[str]] = {}
    for split_name, raw_ids in split_mapping.items():
        if not isinstance(raw_ids, list) or not all(
            isinstance(patient_id, str) for patient_id in raw_ids
        ):
            raise AssertionError(f"split {split_name} must contain string patient IDs")
        split_sets[split_name] = set(raw_ids)

    for left, right in combinations(sorted(split_sets), 2):
        assert split_sets[left].isdisjoint(split_sets[right])

    rosters = real_phase03_artifacts["retained_rosters"]
    assert isinstance(rosters, dict)
    utsw_roster = set(rosters[Cohort.UTSW])
    all_split_ids = set().union(*split_sets.values())
    assert all_split_ids <= utsw_roster

    exclusion_manifest = _json_object(
        real_phase03_artifacts["exclusion_manifest"], "exclusion_manifest"
    )
    excluded_utsw = {
        normalize_identifier(entry["patient_id"], Cohort.UTSW)
        for raw_entry in exclusion_manifest["exclusions"]
        if (entry := _json_object(raw_entry, "exclusion entry"))["cohort"]
        == Cohort.UTSW.value
    }
    assert all_split_ids.isdisjoint(excluded_utsw)

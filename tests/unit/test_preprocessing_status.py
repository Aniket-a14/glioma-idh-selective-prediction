"""Unit tests for the Phase 04 preprocessing status manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
import scripts.build_preprocessing_status as status_script

import glioma_selective.preprocessing.status as status_module
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.status import (
    PreprocessingStatusManifest,
)
from glioma_selective.preprocessing.verification import (
    CaseVerification,
    FailureCategory,
)


def _verification(
    patient_id: str,
    status: str,
    *,
    cohort: Cohort = Cohort.UTSW,
    failure_categories: tuple[str, ...] = (),
    borderline_checks: tuple[str, ...] = (),
) -> CaseVerification:
    return CaseVerification(
        cohort=cohort,
        patient_id=patient_id,
        status=status,
        checks={},
        failure_categories=cast(tuple[FailureCategory, ...], failure_categories),
        borderline_checks=borderline_checks,
        brain_voxel_fraction=None,
        cross_sequence_dice={},
        segmentation_findings={},
    )


def _manifest(
    *results: CaseVerification,
) -> PreprocessingStatusManifest:
    return PreprocessingStatusManifest.from_verification(results)


def test_from_verification_maps_statuses_and_initial_stages() -> None:
    manifest = _manifest(
        _verification("case-clean", "verified-passthrough"),
        _verification(
            "case-borderline",
            "verified-borderline",
            borderline_checks=("T1ce.brain_fraction",),
        ),
        _verification(
            "case-failed",
            "failed",
            failure_categories=("corrupt",),
        ),
        _verification("case-not-run", "not-run"),
    )

    assert manifest.cases[("utsw", "case-clean")].visual_qc == "not-required"
    assert manifest.cases[("utsw", "case-borderline")].visual_qc == "pending"
    assert manifest.cases[("utsw", "case-failed")].visual_qc == "pending"
    assert manifest.cases[("utsw", "case-not-run")].visual_qc == "not-required"
    assert manifest.cases[("utsw", "case-clean")].stages["verify"].state == "done"
    assert manifest.cases[("utsw", "case-clean")].stages["mask"].state == "pending"
    assert "normalize" not in manifest.cases[("utsw", "case-clean")].stages


def test_mask_stage_can_be_updated_and_round_trips(tmp_path: Path) -> None:
    manifest = _manifest(_verification("case-mask", "verified-passthrough"))
    updated = manifest.update_stage("utsw", "case-mask", "mask", "done", "mask-key")

    path = tmp_path / "preprocessing_status.json"
    updated.save(path)
    loaded = PreprocessingStatusManifest.load(path)

    assert loaded.cases[("utsw", "case-mask")].stages["mask"].cache_key == "mask-key"


def test_qc_reason_accepts_only_current_categories() -> None:
    assert status_module.qc_reason("registration-failed") == "qc:registration-failed"
    with pytest.raises(ValueError, match="unknown Phase 04 QC category"):
        status_module.qc_reason("skullstrip-failed")
    with pytest.raises(ValueError, match="unknown Phase 04 QC category"):
        status_module.qc_reason("made-up-category")


def test_automated_failure_is_only_an_exclusion_candidate() -> None:
    manifest = _manifest(
        _verification("candidate", "failed", failure_categories=("corrupt",))
    )
    candidate = manifest.cases[("utsw", "candidate")]
    assert candidate.visual_qc == "pending"
    assert candidate.qc_reasons == ()

    decided = manifest.record_exclusion("utsw", "candidate", "corrupt")
    assert decided.cases[("utsw", "candidate")].visual_qc == "failed"
    assert decided.cases[("utsw", "candidate")].qc_reasons == ("qc:corrupt",)

    passed = manifest.record_visual_qc_verdict("utsw", "candidate", "passed")
    assert passed.cases[("utsw", "candidate")].qc_reasons == ()


def test_pending_cases_shrink_and_survive_save_load(tmp_path: Path) -> None:
    manifest = _manifest(
        _verification("a", "verified-passthrough"),
        _verification("b", "verified-passthrough"),
    )
    assert [case.patient_id for case in manifest.pending_cases("reorient")] == [
        "a",
        "b",
    ]
    manifest = manifest.update_stage("utsw", "a", "reorient", "done", "key-a")
    assert [case.patient_id for case in manifest.pending_cases("reorient")] == ["b"]

    path = tmp_path / "preprocessing_status.json"
    manifest.save(path)
    first_bytes = path.read_bytes()
    manifest.save(path)
    assert path.read_bytes() == first_bytes
    loaded = PreprocessingStatusManifest.load(path)
    assert loaded.cases[("utsw", "a")].stages["reorient"].cache_key == "key-a"
    assert [case.patient_id for case in loaded.pending_cases("reorient")] == ["b"]
    assert list(tmp_path.glob(".preprocessing_status.json.*.tmp")) == []


def test_merge_passthrough_to_borderline_resets_visual_qc() -> None:
    original = _manifest(_verification("a", "verified-passthrough"))

    merged = original.merge_verification(
        (
            _verification(
                "a",
                "verified-borderline",
                borderline_checks=("T1ce.brain_fraction",),
            ),
        )
    )
    case = merged.cases[("utsw", "a")]
    assert case.verification_status == "verified-borderline"
    assert case.visual_qc == "pending"
    assert case.qc_reasons == ()


def test_merge_passthrough_to_failed_resets_visual_qc() -> None:
    original = _manifest(_verification("a", "verified-passthrough"))

    merged = original.merge_verification(
        (_verification("a", "failed", failure_categories=("corrupt",)),)
    )
    case = merged.cases[("utsw", "a")]
    assert case.verification_status == "failed"
    assert case.visual_qc == "pending"
    assert case.qc_reasons == ()


def test_merge_identical_borderline_keeps_verdict_and_stage_records() -> None:
    original = _manifest(
        _verification(
            "a",
            "verified-borderline",
            borderline_checks=("check",),
        )
    )
    original = original.update_stage("utsw", "a", "n4", "done", "n4-key")
    original = original.record_visual_qc_verdict("utsw", "a", "passed")
    refreshed = _verification(
        "a",
        "verified-borderline",
        borderline_checks=("check",),
    )

    merged = original.merge_verification((refreshed,))
    case = merged.cases[("utsw", "a")]
    assert case.verification_status == "verified-borderline"
    assert case.borderline_checks == ("check",)
    assert case.stages["n4"].cache_key == "n4-key"
    assert case.visual_qc == "passed"
    assert case.qc_reasons == ()


def test_merge_changed_borderline_resets_failed_verdict_and_reasons() -> None:
    original = _manifest(
        _verification(
            "a",
            "verified-borderline",
            borderline_checks=("T1ce.brain_fraction",),
        )
    )
    original = original.update_stage("utsw", "a", "reorient", "done", "key")
    original = original.record_visual_qc_verdict("utsw", "a", "failed", "n4-artifact")

    merged = original.merge_verification(
        (
            _verification(
                "a",
                "verified-borderline",
                borderline_checks=("cross_sequence.mask_dice",),
            ),
        )
    )
    case = merged.cases[("utsw", "a")]
    assert case.visual_qc == "pending"
    assert case.qc_reasons == ()
    assert case.stages["reorient"].cache_key == "key"


def test_merge_borderline_to_clean_resets_pending_visual_qc() -> None:
    original = _manifest(
        _verification(
            "a",
            "verified-borderline",
            borderline_checks=("T1ce.brain_fraction",),
        )
    )
    assert original.cases[("utsw", "a")].visual_qc == "pending"

    merged = original.merge_verification((_verification("a", "verified-passthrough"),))
    case = merged.cases[("utsw", "a")]
    assert case.visual_qc == "not-required"
    assert case.qc_reasons == ()


def test_build_and_merge_script_is_byte_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    private_dir = tmp_path / "private"
    manifests_dir = tmp_path / "manifests"
    private_dir.mkdir()
    payload = {
        "schema_version": 2,
        "cases": [
            {
                "cohort": "utsw",
                "patient_id": "case-a",
                "status": "verified-passthrough",
                "failure_categories": [],
                "borderline_checks": [],
            },
            {
                "cohort": "ucsf_pdgm",
                "patient_id": "case-b",
                "status": "verified-borderline",
                "failure_categories": [],
                "borderline_checks": ["T1ce.brain_fraction"],
            },
        ],
    }
    (private_dir / "preprocessing_verification_cases.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    monkeypatch.setattr(status_script.paths, "private_data_dir", lambda: private_dir)
    monkeypatch.setattr(status_script.paths, "manifests_dir", lambda: manifests_dir)

    assert status_script.main() == 0
    destination = manifests_dir / "preprocessing_status.json"
    first_bytes = destination.read_bytes()
    assert status_script.main() == 0
    assert destination.read_bytes() == first_bytes


def test_atomic_save_keeps_previous_file_when_write_is_interrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "preprocessing_status.json"
    manifest = _manifest(_verification("a", "verified-passthrough"))
    manifest.save(path)
    previous = path.read_bytes()

    def interrupted_write(*args: object, **kwargs: object) -> None:
        raise OSError("simulated interrupted write")

    monkeypatch.setattr(status_module.json, "dump", interrupted_write)
    with pytest.raises(OSError, match="simulated interrupted write"):
        manifest.save(path)
    assert path.read_bytes() == previous
    assert list(tmp_path.glob(".preprocessing_status.json.*.tmp")) == []


def test_load_rejects_bad_schema_and_unknown_state_or_category(
    tmp_path: Path,
) -> None:
    path = tmp_path / "preprocessing_status.json"
    base = _manifest(_verification("a", "verified-passthrough"))
    base.save(path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    payload["schema_version"] = 99
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported preprocessing status schema"):
        PreprocessingStatusManifest.load(path)

    base.save(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cases"][0]["stages"]["n4"]["state"] = "unknown"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown preprocessing stage state"):
        PreprocessingStatusManifest.load(path)

    base.save(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["cases"][0]["failure_categories"] = ["skullstrip-failed"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown failure category"):
        PreprocessingStatusManifest.load(path)


def test_summary_is_aggregate_only_and_stop_flag_uses_both_rates() -> None:
    ten = tuple(
        _verification(
            f"ten-{index}",
            "failed" if index < 2 else "verified-passthrough",
            failure_categories=("corrupt",) if index < 2 else (),
        )
        for index in range(10)
    )
    twenty = tuple(
        _verification(
            f"twenty-{index}",
            "failed" if index == 0 else "verified-passthrough",
            cohort=Cohort.UCSF_PDGM,
            failure_categories=("corrupt",) if index == 0 else (),
        )
        for index in range(20)
    )
    summary = _manifest(*ten, *twenty).summary()
    encoded = json.dumps(summary)
    cohorts = cast(dict[str, dict[str, object]], summary["cohorts"])
    assert "ten-" not in encoded
    assert "twenty-" not in encoded
    assert "/" not in encoded
    assert cohorts["utsw"]["automated_failure_rate"] == 0.2
    assert cohorts["utsw"]["exceeds_stop_threshold"] is True
    assert cohorts["ucsf_pdgm"]["automated_failure_rate"] == 0.05
    assert cohorts["ucsf_pdgm"]["exceeds_stop_threshold"] is False

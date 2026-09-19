"""Synthetic tests for the post-QC manifest builder script."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import scripts.build_post_qc_manifests as script

from glioma_selective.leakage.id_normalization import Cohort
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


def _verification(
    patient_id: str,
    *,
    status: str = "verified-passthrough",
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


def _status_with_one_qc_exclusion(path: Path) -> None:
    status = PreprocessingStatusManifest.from_verification(
        (
            *(_verification(f"BT{index:04d}") for index in range(2, 12)),
            _verification("UCSF-PDGM-0002", cohort=Cohort.UCSF_PDGM),
            _verification("UCSF-PDGM-0003", cohort=Cohort.UCSF_PDGM),
        )
    )
    status = status.record_visual_qc_verdict("utsw", "BT0002", "failed", "corrupt")
    status.save(path)


def test_main_writes_post_qc_outputs_and_prints_aggregate_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    storage_manifests = tmp_path / "ssd" / "manifests"
    storage_manifests.mkdir(parents=True)
    status_path = tmp_path / "status.json"
    _status_with_one_qc_exclusion(status_path)
    post_exclusion_path = storage_manifests / "exclusion_manifest_post_qc.json"
    post_manifest_path = tmp_path / "docs" / "cohort_manifest_post_qc.json"

    base = _base_manifest()
    pre_rosters = {
        Cohort.UTSW: ("UTSW-BT0002", "UTSW-BT0003", "UTSW-BT0004"),
        Cohort.UCSF_PDGM: ("UCSF-PDGM-0002", "UCSF-PDGM-0003"),
    }
    post_rosters = {
        Cohort.UTSW: ("UTSW-BT0003", "UTSW-BT0004"),
        Cohort.UCSF_PDGM: ("UCSF-PDGM-0002", "UCSF-PDGM-0003"),
    }

    monkeypatch.setattr(script.paths, "manifests_dir", lambda: storage_manifests)
    monkeypatch.setattr(script, "build_real_exclusion_manifest", lambda: base)

    def fake_rosters(manifest: object) -> dict[Cohort, tuple[str, ...]]:
        if isinstance(manifest, dict) and manifest.get("qc_exclusion_count"):
            return post_rosters
        return pre_rosters

    monkeypatch.setattr(script, "build_real_retained_rosters", fake_rosters)

    assert (
        script.main(
            [
                "--status-path",
                str(status_path),
                "--exclusion-output",
                str(post_exclusion_path),
                "--manifest-output",
                str(post_manifest_path),
            ]
        )
        == 0
    )
    output = capsys.readouterr().out
    summary = json.loads(output)
    assert summary["cohorts"]["utsw"]["retained_pre_qc"] == 3
    assert summary["cohorts"]["utsw"]["qc_excluded"] == 1
    assert summary["cohorts"]["utsw"]["retained_post_qc"] == 2
    assert summary["qc_reason_counts"] == {"qc:corrupt": 1}
    assert "BT0002" not in output
    assert post_exclusion_path.exists()
    assert post_manifest_path.exists()
    written_post = json.loads(post_manifest_path.read_text(encoding="utf-8"))
    assert written_post["stage"] == "post_qc"
    assert written_post["pre_qc_manifest"] == "cohort_manifest.json"
    assert "EGD is not included yet" in written_post["note"]
    assert "T04.12 QC exclusions" in written_post["note"]


def test_main_refuses_frozen_phase03_outputs_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    status_path = tmp_path / "status.json"
    _status_with_one_qc_exclusion(status_path)
    monkeypatch.setattr(script.paths, "manifests_dir", lambda: manifests)
    assert (
        script.main(
            [
                "--status-path",
                str(status_path),
                "--exclusion-output",
                str(manifests / "exclusion_manifest_post_qc.json"),
                "--manifest-output",
                str(
                    script.REPOSITORY_ROOT
                    / "docs/research/manifests/cohort_manifest.json"
                ),
            ]
        )
        == 1
    )
    assert not (manifests / "exclusion_manifest_post_qc.json").exists()


def test_main_refuses_stop_threshold_before_building_or_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    status = PreprocessingStatusManifest.from_verification(
        tuple(
            _verification(
                f"BT{index:04d}",
                status="failed" if index < 2 else "verified-passthrough",
            )
            for index in range(10)
        )
    )
    status_path = tmp_path / "status.json"
    status.save(status_path)
    output = tmp_path / "post.json"
    monkeypatch.setattr(script.paths, "manifests_dir", lambda: tmp_path / "ssd")

    def fail_if_called() -> dict[str, object]:
        raise AssertionError("real exclusion builder must not run")

    monkeypatch.setattr(script, "build_real_exclusion_manifest", fail_if_called)
    assert (
        script.main(
            [
                "--status-path",
                str(status_path),
                "--exclusion-output",
                str(tmp_path / "post-exclusion.json"),
                "--manifest-output",
                str(output),
            ]
        )
        == 1
    )
    assert not output.exists()


def test_main_rejects_a_qc_id_absent_from_pre_qc_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    status_path = tmp_path / "status.json"
    _status_with_one_qc_exclusion(status_path)
    monkeypatch.setattr(script.paths, "manifests_dir", lambda: tmp_path / "ssd")
    monkeypatch.setattr(script, "build_real_exclusion_manifest", _base_manifest)
    monkeypatch.setattr(
        script,
        "build_real_retained_rosters",
        lambda _: {
            Cohort.UTSW: ("BT0003", "BT0004"),
            Cohort.UCSF_PDGM: ("UCSF-PDGM-0002", "UCSF-PDGM-0003"),
        },
    )
    assert (
        script.main(
            [
                "--status-path",
                str(status_path),
                "--exclusion-output",
                str(tmp_path / "post-exclusion.json"),
                "--manifest-output",
                str(tmp_path / "post.json"),
            ]
        )
        == 1
    )
    assert not (tmp_path / "post-exclusion.json").exists()


def test_main_checks_canonical_form_against_retained_roster(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    status = PreprocessingStatusManifest.from_verification(
        (_verification("UCSF-PDGM-002", cohort=Cohort.UCSF_PDGM),)
    )
    status = status.record_visual_qc_verdict(
        "ucsf_pdgm", "UCSF-PDGM-002", "failed", "corrupt"
    )
    status_path = tmp_path / "status.json"
    status.save(status_path)
    monkeypatch.setattr(script.paths, "manifests_dir", lambda: tmp_path / "ssd")
    monkeypatch.setattr(script, "build_real_exclusion_manifest", _base_manifest)
    monkeypatch.setattr(
        script,
        "build_real_retained_rosters",
        lambda _: {
            Cohort.UTSW: ("BT0002", "BT0003", "BT0004"),
            Cohort.UCSF_PDGM: ("UCSF-PDGM-0002", "UCSF-PDGM-0003"),
        },
    )
    assert (
        script.main(
            [
                "--status-path",
                str(status_path),
                "--exclusion-output",
                str(tmp_path / "post-exclusion.json"),
                "--manifest-output",
                str(tmp_path / "post.json"),
            ]
        )
        == 1
    )

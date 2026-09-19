"""Tests for the thin Phase 04 report script wrappers."""

from __future__ import annotations

from pathlib import Path

import scripts.audit_preprocessing_outputs as audit_script
import scripts.build_qc_report as qc_script


def test_audit_script_propagates_failed_report(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        audit_script,
        "audit_preprocessing_outputs",
        lambda **_: {"passed": False},
    )
    assert (
        audit_script.main(
            [
                "--outputs",
                str(tmp_path / "outputs.json"),
                "--cohort-manifest",
                str(tmp_path / "manifest.json"),
                "--output",
                str(tmp_path / "audit.json"),
                "--cache-root",
                str(tmp_path / "cache"),
            ]
        )
        == 1
    )


def test_qc_script_returns_zero_for_a_built_report(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        qc_script,
        "build_qc_report",
        lambda **_: {"schema_version": 1},
    )
    assert (
        qc_script.main(
            [
                "--status",
                str(tmp_path / "status.json"),
                "--verification",
                str(tmp_path / "verification.json"),
                "--review-sheet",
                str(tmp_path / "review.csv"),
                "--overlay-index",
                str(tmp_path / "index.json"),
                "--output",
                str(tmp_path / "report.json"),
            ]
        )
        == 0
    )

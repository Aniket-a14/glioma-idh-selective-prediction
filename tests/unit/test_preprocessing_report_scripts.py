"""Tests for the thin Phase 04 report script wrappers."""

from __future__ import annotations

from pathlib import Path

import pytest
import scripts.audit_preprocessing_outputs as audit_script
import scripts.build_qc_report as qc_script

from glioma_selective.preprocessing.output_audit import OutputAuditError
from glioma_selective.preprocessing.qc_report import QCReportError


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


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (
            OutputAuditError("output index has invalid cohort data"),
            "output index has invalid cohort data",
        ),
        (ValueError("internal detail"), "audit failed"),
    ],
)
def test_audit_script_reports_curated_and_generic_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    exception: Exception,
    message: str,
) -> None:
    def fail(**_: object) -> dict[str, object]:
        raise exception

    monkeypatch.setattr(audit_script, "audit_preprocessing_outputs", fail)
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
    stderr = capsys.readouterr().err
    assert message in stderr
    if isinstance(exception, ValueError) and not isinstance(
        exception, OutputAuditError
    ):
        assert str(exception) not in stderr


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (
            QCReportError("QC review sheet has an invalid verdict"),
            "QC review sheet has an invalid verdict",
        ),
        (ValueError("internal detail"), "report build failed"),
    ],
)
def test_qc_script_reports_curated_and_generic_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    exception: Exception,
    message: str,
) -> None:
    def fail(**_: object) -> dict[str, object]:
        raise exception

    monkeypatch.setattr(qc_script, "build_qc_report", fail)
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
        == 1
    )
    stderr = capsys.readouterr().err
    assert message in stderr
    if isinstance(exception, ValueError) and not isinstance(exception, QCReportError):
        assert str(exception) not in stderr

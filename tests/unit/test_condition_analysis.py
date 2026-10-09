"""Synthetic provenance and metric checks for condition analysis."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from glioma_selective.evaluation.condition_analysis import analyze_conditions
from glioma_selective.tracking.predictions import write_prediction_artifact

RUN_ID = "synthetic-condition-run"
CHECKPOINT = "checkpoint-sha"
CONDITIONS = (
    "full",
    "drop_t1",
    "drop_t1ce",
    "drop_t2",
    "drop_flair",
    "t1ce_flair_only",
)


def _row(
    patient: str, cohort: str, condition: str, label: int, logit: float
) -> dict[str, object]:
    probability = 1.0 / (1.0 + __import__("math").exp(-logit))
    return {
        "patient_id": patient,
        "cohort": cohort,
        "modality_condition": condition,
        "p_hat": probability,
        "logit": logit,
        "label": label,
        "mc_dropout_samples": [
            probability - 0.03,
            probability + 0.02,
            probability - 0.01,
        ],
    }


def _write_meta(directory: Path) -> None:
    payload = json.dumps(
        {"run_id": RUN_ID, "checkpoint_hash": CHECKPOINT}, sort_keys=True
    ).encode()
    (directory / "conditions_meta.json").write_bytes(payload)
    (directory / "conditions_meta.json.sha256").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  conditions_meta.json\n"
    )


def _prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mismatched_condition: str | None = None,
) -> Path:
    artifact_root = tmp_path / "artifacts"
    run_dir = artifact_root / "experiments" / RUN_ID
    conditions_dir = run_dir / "conditions"
    conditions_dir.mkdir(parents=True)
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(artifact_root))
    run_dir.joinpath("record.json").write_text(
        json.dumps(
            {"run_id": RUN_ID, "status": "completed", "checkpoint_hash": CHECKPOINT}
        )
    )
    calibration_labels = [0, 1, 0, 1, 0, 1, 0, 1]
    calibration_logits = [-3.0, 3.0, -2.0, 2.0, -1.0, 1.0, -0.5, 0.5]
    test_labels = [0, 1, 0, 1, 1, 0, 1, 0]
    test_logits = [-2.0, 2.0, -1.3, 1.4, 0.3, -0.2, 1.0, -1.1]
    full_rows = [
        _row(f"cal-{i}", "utsw_calibration", "full", label, logit)
        for i, (label, logit) in enumerate(
            zip(calibration_labels, calibration_logits, strict=True)
        )
    ] + [
        _row(f"test-{i}", "utsw_internal_test", "full", label, logit)
        for i, (label, logit) in enumerate(zip(test_labels, test_logits, strict=True))
    ]
    write_prediction_artifact(
        full_rows,
        run_dir / "predictions.parquet",
        run_id=RUN_ID,
        git_sha="code-sha",
        checkpoint_hash=CHECKPOINT,
    )
    for condition in CONDITIONS:
        rows = []
        for i, (label, logit) in enumerate(
            zip(calibration_labels, calibration_logits, strict=True)
        ):
            # Inverting only this calibration condition gives q_refit near 0.5, while
            # carried-over full scores have q_full near 0: with n=8 and alpha=.20,
            # k=ceil((8+1)*(1-.20))=8, so each quantile is its largest score.
            altered = -logit if condition == "drop_t1ce" else logit
            rows.append(_row(f"cal-{i}", "utsw_calibration", condition, label, altered))
        for i, (label, logit) in enumerate(zip(test_labels, test_logits, strict=True)):
            rows.append(
                _row(f"test-{i}", "utsw_internal_test", condition, label, logit)
            )
        if condition == mismatched_condition:
            rows[-1] = _row("other-test", "utsw_internal_test", condition, 0, -0.3)
        write_prediction_artifact(
            rows,
            conditions_dir / f"{condition}.parquet",
            run_id=RUN_ID,
            git_sha="code-sha",
            checkpoint_hash=CHECKPOINT,
        )
    _write_meta(conditions_dir)
    return run_dir


def test_analysis_reports_two_variants_selective_and_degradation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _prepare(tmp_path, monkeypatch)
    report_path = analyze_conditions(RUN_ID)
    report = json.loads(report_path.read_text())
    assert set(report["conditions"]) == set(CONDITIONS)
    assert set(report["conditions"]["drop_t1"]["recalibration"]) == {
        "carried_over",
        "refit",
    }
    carried = report["conditions"]["drop_t1ce"]["recalibration"]["carried_over"][
        "by_alpha"
    ]["0.2"]["conformal"]["quantile"]
    refit = report["conditions"]["drop_t1ce"]["recalibration"]["refit"]["by_alpha"][
        "0.2"
    ]["conformal"]["quantile"]
    assert carried != refit
    selective = report["conditions"]["full"]["selective"]
    assert "M2_confidence" in selective and "M3_mc_dropout_entropy" in selective
    assert "degradation" in report
    assert set(report["degradation"]["auroc"]) == set(CONDITIONS)
    assert report_path.with_name(report_path.name + ".sha256").exists()
    encoded = report_path.read_text()
    for identifier in [f"cal-{i}" for i in range(8)] + [f"test-{i}" for i in range(8)]:
        assert identifier not in encoded
    assert "patient" not in encoded.lower()
    assert run_dir.exists()


def test_analysis_refuses_tampered_meta_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _prepare(tmp_path, monkeypatch)
    sidecar = run_dir / "conditions" / "conditions_meta.json.sha256"
    sidecar.write_text("0" * 64 + "  conditions_meta.json\n")
    with pytest.raises(ValueError, match="sidecar"):
        analyze_conditions(RUN_ID)


def test_analysis_refuses_internal_test_patient_set_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare(tmp_path, monkeypatch, mismatched_condition="drop_t2")
    with pytest.raises(ValueError, match="patient sets differ"):
        analyze_conditions(RUN_ID)

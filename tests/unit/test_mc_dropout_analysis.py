from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.evaluation import mc_dropout_analysis as analysis
from glioma_selective.evaluation.selective_metrics import selective_risk_at_coverage
from glioma_selective.selective.aurc import aurc_mean_over_cutoffs
from glioma_selective.tracking.predictions import write_prediction_artifact
from glioma_selective.utils import paths

RUN_ID = "01K6JQY7YGXSP6ZBZD3YF8QXPT"
CHECKPOINT = "c" * 64


def _fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    pred_run_id: str = RUN_ID,
    mc_run_id: str = RUN_ID,
    pred_hash: str = CHECKPOINT,
    mc_hash: str = CHECKPOINT,
    mc_patient_suffix: str | None = None,
) -> Path:
    run_dir = tmp_path / "experiments" / RUN_ID
    run_dir.mkdir(parents=True)
    (run_dir / "record.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "status": "completed",
                "checkpoint_hash": CHECKPOINT,
            }
        ),
        encoding="utf-8",
    )
    pred_rows = []
    mc_rows = []
    for cohort in ("utsw_calibration", "utsw_internal_test"):
        for i, label in enumerate((0, 1, 0, 1)):
            logit = (-1.0 if label == 0 else 1.0) * (0.4 + i * 0.25)
            p_hat = 1 / (1 + np.exp(-logit))
            patient = f"{cohort}-{i}"
            pred_rows.append(
                {
                    "patient_id": patient,
                    "cohort": cohort,
                    "modality_condition": "full",
                    "p_hat": p_hat,
                    "logit": logit,
                    "label": label,
                }
            )
            mc_rows.append(
                {
                    "patient_id": (
                        patient + "-changed"
                        if mc_patient_suffix
                        and cohort == "utsw_internal_test"
                        and i == 0
                        else patient
                    ),
                    "cohort": cohort,
                    "modality_condition": "full",
                    "p_hat": p_hat,
                    "logit": logit,
                    "label": label,
                    "mc_dropout_samples": [
                        p_hat - 0.12,
                        p_hat - 0.04,
                        p_hat + 0.04,
                        p_hat + 0.12,
                    ],
                }
            )
    write_prediction_artifact(
        pred_rows,
        run_dir / "predictions.parquet",
        run_id=pred_run_id,
        git_sha="a" * 40,
        checkpoint_hash=pred_hash,
    )
    write_prediction_artifact(
        mc_rows,
        run_dir / "mc_dropout.parquet",
        run_id=mc_run_id,
        git_sha="a" * 40,
        checkpoint_hash=mc_hash,
    )
    monkeypatch.setattr(paths, "experiments_dir", lambda: tmp_path / "experiments")
    return run_dir


def test_analysis_writes_comparable_metrics_and_valid_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _fixture(tmp_path, monkeypatch)
    path = analysis.analyze_mc_dropout(RUN_ID)
    document = json.loads(path.read_text())
    assert document["provenance"]["internal_test_p_hat_max_abs_difference"] == 0.0
    assert document["provenance"]["splits"]["internal_test"]["passes"] == 4
    assert set(document["views"]) == {
        "M2_temperature_scaled",
        "M3_mc_dropout",
        "aurc_mean_over_cutoffs_M3_minus_M2",
    }
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert (
        path.with_name(path.name + ".sha256").read_text() == f"{digest}  {path.name}\n"
    )
    assert "patient" not in path.read_text().lower()
    assert "patient" not in (run_dir / "mc_dropout_analysis.json").read_text().lower()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"mc_run_id": "01K6JQY7YGXSP6ZBZD3YF8QXPV"}, "run_id"),
        ({"mc_hash": "d" * 64}, "checkpoint_hash"),
        ({"mc_patient_suffix": "x"}, "patient sets differ"),
    ],
)
def test_analysis_rejects_provenance_or_patient_set_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, str],
    message: str,
) -> None:
    _fixture(tmp_path, monkeypatch, **kwargs)
    with pytest.raises(ValueError, match=message):
        analysis.analyze_mc_dropout(RUN_ID)


def test_analysis_rejects_tampered_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _fixture(tmp_path, monkeypatch)
    sidecar = run_dir / "mc_dropout.parquet.sha256"
    sidecar.write_text("0" * 64 + "  mc_dropout.parquet\n")
    with pytest.raises(ValueError, match="sidecar"):
        analysis.analyze_mc_dropout(RUN_ID)


def test_selective_arithmetic_hand_check() -> None:
    # Descending scores accept losses 0,1,0,1: AURC=(0+1/2+1/3+1/2)/4=1/3;
    # at 0.5 coverage the first two cases have risk 1/2.
    scores, losses = [4, 3, 2, 1], [0, 1, 0, 1]
    assert aurc_mean_over_cutoffs(scores, losses) == pytest.approx(1 / 3)
    assert selective_risk_at_coverage(scores, losses, 0.5) == (0.5, 0.5)

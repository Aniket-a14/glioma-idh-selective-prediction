from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.evaluation import internal_analysis
from glioma_selective.evaluation.internal_analysis import analyze_internal
from glioma_selective.evaluation.selective_metrics import selective_risk_at_coverage
from glioma_selective.selective.aurc import aurc_mean_over_cutoffs
from glioma_selective.tracking.predictions import write_prediction_artifact
from glioma_selective.utils import paths


def _analysis_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: str = "completed",
    calibration_labels: list[int] | None = None,
    test_labels: list[int] | None = None,
    metadata_run_id: str | None = None,
    metadata_checkpoint_hash: str | None = None,
) -> tuple[str, Path]:
    run_id = "01K6JQY7YGXSP6ZBZD3YF8QXPT"
    run_dir = tmp_path / "experiments" / run_id
    run_dir.mkdir(parents=True)
    checkpoint_hash = "c" * 64
    record = {
        "run_id": run_id,
        "status": status,
        "checkpoint_hash": checkpoint_hash,
        "metrics": {"best_epoch": 4, "prior": 7},
    }
    (run_dir / "record.json").write_text(json.dumps(record), encoding="utf-8")
    calibration_targets = calibration_labels or [index % 2 for index in range(20)]
    test_targets = test_labels or [index % 2 for index in range(20)]
    rows: list[dict[str, object]] = []
    for cohort, labels in (
        ("utsw_calibration", calibration_targets),
        ("utsw_internal_test", test_targets),
    ):
        for index, label in enumerate(labels):
            # The scores are under-confident for these perfectly ordered labels;
            # fitting should sharpen them (T < 1), reducing test ECE as well.
            logit = 0.8 if label else -0.8
            probability = 1.0 / (1.0 + np.exp(-logit))
            rows.append(
                {
                    "patient_id": f"{cohort}-patient-{index}",
                    "cohort": cohort,
                    "modality_condition": "full",
                    "p_hat": float(probability),
                    "logit": float(logit),
                    "label": label,
                }
            )
    write_prediction_artifact(
        rows,
        run_dir / "predictions.parquet",
        run_id=metadata_run_id or run_id,
        git_sha="a" * 40,
        checkpoint_hash=metadata_checkpoint_hash or checkpoint_hash,
    )
    monkeypatch.setattr(paths, "experiments_dir", lambda: tmp_path / "experiments")
    return run_id, run_dir


def test_analysis_writes_report_sidecar_and_merges_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run_id, run_dir = _analysis_fixture(tmp_path, monkeypatch)
    report_path = analyze_internal(run_id)
    payload = report_path.read_bytes()
    report = json.loads(payload)
    assert report["provenance"]["temperature"] < 1.0
    assert (
        report["views"]["M2_scaled"]["classification"]["ece"]["10"]
        <= report["views"]["M1_raw"]["classification"]["ece"]["10"]
    )
    assert report["provenance"]["splits"]["calibration"] == {
        "n": 20,
        "positives": 10,
        "negatives": 10,
    }
    digest = hashlib.sha256(payload).hexdigest()
    sidecar = report_path.with_name(report_path.name + ".sha256")
    assert sidecar.read_text(encoding="ascii") == f"{digest}  {report_path.name}\n"
    record = json.loads((run_dir / "record.json").read_text(encoding="utf-8"))
    assert record["metrics"]["best_epoch"] == 4
    assert record["metrics"]["prior"] == 7
    assert (
        record["metrics"]["internal_analysis"]["alpha_0.10"]["coverage"]
        == report["conformal"]["0.1"]["coverage"]
    )
    assert "patient" not in payload.decode().lower()
    assert "patient" not in capsys.readouterr().out.lower()


def test_analysis_serializes_infinite_conformal_quantile_as_string(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _run_id, _run_dir = _analysis_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(internal_analysis, "_ALPHA_GRID", (0.001, 0.10))
    # n=20: ceil((20 + 1) * (1 - .001)) = 21, so K2 requires +inf.
    report_path = analyze_internal("01K6JQY7YGXSP6ZBZD3YF8QXPT")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["conformal"]["0.001"]["quantile"] == "inf"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"status": "running"}, "status=completed"),
        (
            {"metadata_run_id": "01K6JQY7YGXSP6ZBZD3YF8QXPV"},
            "run_id",
        ),
        ({"metadata_checkpoint_hash": "d" * 64}, "checkpoint_hash"),
        ({"test_labels": [1] * 20}, "utsw_internal_test.*two classes"),
        ({"calibration_labels": [0] * 20}, "utsw_calibration.*two classes"),
    ],
)
def test_analysis_rejects_invalid_provenance_or_one_class_split(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, object],
    message: str,
) -> None:
    run_id, _run_dir = _analysis_fixture(tmp_path, monkeypatch, **kwargs)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=message):
        analyze_internal(run_id)


@pytest.mark.parametrize(
    "existing", ["internal_analysis.json", "internal_analysis.json.sha256"]
)
def test_analysis_refuses_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: str
) -> None:
    run_id, run_dir = _analysis_fixture(tmp_path, monkeypatch)
    (run_dir / existing).write_text("existing", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        analyze_internal(run_id)


def test_analysis_refuses_tampered_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id, run_dir = _analysis_fixture(tmp_path, monkeypatch)
    with (run_dir / "predictions.parquet").open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="sidecar"):
        analyze_internal(run_id)


def test_selective_arithmetic_matches_hand_checked_tiny_case() -> None:
    # Ordered losses are 0, 1, 0, 0: cutoff risks are 0, 1/2, 1/3, 1/4.
    # Their mean is 13/48; accepting the first two patients gives risk 1/2.
    scores = [0.9, 0.8, 0.7, 0.6]
    losses = [0, 1, 0, 0]
    assert aurc_mean_over_cutoffs(scores, losses) == pytest.approx(13 / 48)
    assert selective_risk_at_coverage(scores, losses, 0.5) == (0.5, 0.5)

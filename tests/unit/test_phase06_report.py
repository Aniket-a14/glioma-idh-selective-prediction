from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from glioma_selective.evaluation.phase06_report import (
    average_precision,
    bootstrap_intervals,
    criterion_flags,
    report_phase06,
)
from glioma_selective.tracking.predictions import write_prediction_artifact
from glioma_selective.training.metrics import binary_auroc
from glioma_selective.utils import paths


def _brute_auc(scores: list[float], labels: list[int]) -> float:
    wins = 0.0
    positive = negative = 0
    for score, label in zip(scores, labels, strict=True):
        if label:
            positive += 1
            wins += sum(
                1.0 if score > other else 0.5 if score == other else 0.0
                for other, other_label in zip(scores, labels, strict=True)
                if not other_label
            )
        else:
            negative += 1
    return wins / (positive * negative)


def test_auroc_matches_pairwise_count_with_ties() -> None:
    rng = np.random.default_rng(41)
    for size in range(4, 30):
        labels = [index % 2 for index in range(size)]
        scores = rng.integers(0, 5, size=size).astype(float).tolist()
        expected = _brute_auc(scores, labels)
        assert binary_auroc(np.asarray(scores), np.asarray(labels)) == pytest.approx(
            expected, abs=1e-12
        )


def test_average_precision_hand_fixture_groups_a_tied_threshold() -> None:
    # Six patients sorted by score: + at .9, (-,+) tied at .8, - at .4,
    # + at .2, - at .1. Threshold contributions are 1/3, 2/9, and 1/5.
    scores = np.asarray([0.9, 0.8, 0.8, 0.4, 0.2, 0.1])
    labels = np.asarray([1, 0, 1, 0, 1, 0])
    assert average_precision(scores, labels) == pytest.approx(34 / 45, abs=1e-12)


def test_bootstrap_is_deterministic_ordered_and_counts_skips() -> None:
    labels = np.asarray([1, 0])
    scores = np.asarray([0.9, 0.1])
    first = bootstrap_intervals(scores, labels, iterations=100, seed=3)
    second = bootstrap_intervals(scores, labels, iterations=100, seed=3)
    assert first == second
    assert first["skipped_resamples"] > 0
    assert first["auroc_ci"][0] <= first["auroc_ci"][1]
    assert first["auprc_ci"][0] <= first["auprc_ci"][1]


def test_criterion_flags_cover_perfect_random_and_inverted_scores() -> None:
    labels = np.asarray([0] * 20 + [1] * 20)
    perfect = np.arange(40, dtype=np.float64)
    random = np.random.default_rng(17).random(40)
    inverted = -perfect

    perfect_ci = bootstrap_intervals(perfect, labels, iterations=500)["auroc_ci"]
    random_ci = bootstrap_intervals(random, labels, iterations=500)["auroc_ci"]
    inverted_ci = bootstrap_intervals(inverted, labels, iterations=500)["auroc_ci"]
    assert criterion_flags(binary_auroc(perfect, labels), perfect_ci)["criterion_6_met"]
    assert not criterion_flags(binary_auroc(random, labels), random_ci)[
        "criterion_6_met"
    ]
    assert not criterion_flags(binary_auroc(inverted, labels), inverted_ci)[
        "criterion_6_met"
    ]


def _report_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    status: str = "completed",
    labels: list[int] | None = None,
    metadata_run_id: str | None = None,
    metadata_checkpoint_hash: str | None = None,
) -> tuple[str, Path, dict[str, object]]:
    run_id = "01K6JQY7YGXSP6ZBZD3YF8QXPT"
    run_dir = tmp_path / "experiments" / run_id
    run_dir.mkdir(parents=True)
    checkpoint_hash = "c" * 64
    record: dict[str, object] = {
        "run_id": run_id,
        "status": status,
        "checkpoint_hash": checkpoint_hash,
        "metrics": {"best_epoch": 4, "stopped_early": True, "prior": 7},
    }
    (run_dir / "record.json").write_text(json.dumps(record), encoding="utf-8")
    chosen_labels = labels or [0, 1, 0, 1]
    rows = []
    for index, label in enumerate(chosen_labels):
        probability = [0.1, 0.9, 0.2, 0.8][index % 4]
        logit = float(np.log(probability / (1 - probability)))
        rows.append(
            {
                "patient_id": f"patient-{index}",
                "cohort": "utsw_internal_test",
                "modality_condition": "full",
                "p_hat": probability,
                "logit": logit,
                "label": label,
            }
        )
    if len(chosen_labels) >= 2:
        rows.append(
            {
                "patient_id": "calibration-patient",
                "cohort": "utsw_calibration",
                "modality_condition": "full",
                "p_hat": 0.99,
                "logit": float(np.log(0.99 / 0.01)),
                "label": 0,
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
    return run_id, run_dir, record


def test_report_rejects_incomplete_record_and_metadata_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id, _run_dir, _record = _report_fixture(tmp_path, monkeypatch, status="running")
    with pytest.raises(ValueError, match="status=completed"):
        report_phase06(run_id)

    other_root = tmp_path / "other"
    run_id, _run_dir, _record = _report_fixture(
        other_root, monkeypatch, metadata_run_id="01K6JQY7YGXSP6ZBZD3YF8QXPV"
    )
    with pytest.raises(ValueError, match="run_id"):
        report_phase06(run_id)

    other_root = tmp_path / "checkpoint"
    run_id, _run_dir, _record = _report_fixture(
        other_root, monkeypatch, metadata_checkpoint_hash="d" * 64
    )
    with pytest.raises(ValueError, match="checkpoint_hash"):
        report_phase06(run_id)


def test_report_rejects_one_class_existing_report_and_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "one-class"
    run_id, _run_dir, _record = _report_fixture(root, monkeypatch, labels=[1, 1, 1])
    with pytest.raises(ValueError, match="exactly two classes"):
        report_phase06(run_id)

    root = tmp_path / "existing"
    run_id, run_dir, _record = _report_fixture(root, monkeypatch)
    (run_dir / "phase06_report.json").write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        report_phase06(run_id)

    root = tmp_path / "tampered"
    run_id, run_dir, _record = _report_fixture(root, monkeypatch)
    with (run_dir / "predictions.parquet").open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(ValueError, match="sidecar"):
        report_phase06(run_id)


def test_report_merges_metrics_and_writes_hash_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    run_id, run_dir, _record = _report_fixture(tmp_path, monkeypatch)
    report_path = report_phase06(run_id)
    result = json.loads(report_path.read_text(encoding="utf-8"))
    assert result["n"] == 4
    assert result["positives"] == 2
    assert result["negatives"] == 2
    assert result["auroc"] == pytest.approx(1.0)
    assert result["auprc"] == pytest.approx(1.0)
    assert result["segmentation_dice"].startswith("not_available")
    sidecar = report_path.with_name(report_path.name + ".sha256")
    expected = hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert sidecar.read_text(encoding="ascii") == f"{expected}  {report_path.name}\n"
    record = json.loads((run_dir / "record.json").read_text(encoding="utf-8"))
    assert record["metrics"]["best_epoch"] == 4
    assert record["metrics"]["stopped_early"] is True
    assert record["metrics"]["prior"] == 7
    assert record["metrics"]["internal_test"]["n"] == 4
    assert "patient-" not in capsys.readouterr().out


def test_report_includes_verified_dice_and_rejects_a_tampered_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id, run_dir, _record = _report_fixture(tmp_path / "good", monkeypatch)
    document = {
        "run_id": run_id,
        "git_sha": "a" * 40,
        "checkpoint_hash": "c" * 64,
        "splits": {"internal_test": {"mean": 0.5}},
    }
    payload = (json.dumps(document, sort_keys=True) + "\n").encode()
    dice_path = run_dir / "segmentation_dice.json"
    dice_path.write_bytes(payload)
    dice_path.with_name(dice_path.name + ".sha256").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  {dice_path.name}\n", encoding="ascii"
    )
    result = json.loads(report_phase06(run_id).read_text(encoding="utf-8"))
    assert result["segmentation_dice"]["splits"]["internal_test"]["mean"] == 0.5

    run_id, run_dir, _record = _report_fixture(tmp_path / "bad", monkeypatch)
    dice_path = run_dir / "segmentation_dice.json"
    dice_path.write_bytes(payload)
    dice_path.with_name(dice_path.name + ".sha256").write_text(
        f"{'0' * 64}  {dice_path.name}\n", encoding="ascii"
    )
    with pytest.raises(ValueError, match="sidecar"):
        report_phase06(run_id)

    run_id, run_dir, _record = _report_fixture(tmp_path / "other", monkeypatch)
    wrong = dict(document, run_id="01K6JQY7YGXSP6ZBZD3YF8QXPV")
    wrong_payload = (json.dumps(wrong, sort_keys=True) + "\n").encode()
    dice_path = run_dir / "segmentation_dice.json"
    dice_path.write_bytes(wrong_payload)
    dice_path.with_name(dice_path.name + ".sha256").write_text(
        f"{hashlib.sha256(wrong_payload).hexdigest()}  {dice_path.name}\n",
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="provenance"):
        report_phase06(run_id)

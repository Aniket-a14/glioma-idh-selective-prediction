"""Synthetic frozen-artifact tests for the Phase 09 results assembler."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from glioma_selective.evaluation.phase09_analysis import (
    CONDITIONS,
    _random_control,
    analyze_phase09,
)
from glioma_selective.selective.aurc import aurc_mean_over_cutoffs, oracle_aurc
from glioma_selective.tracking.predictions import write_prediction_artifact

CHECKPOINT = "c" * 64
CONDITIONS_META = {"run_id": "", "checkpoint_hash": CHECKPOINT}


def _row(
    patient: str, cohort: str, condition: str, label: int, p: float
) -> dict[str, Any]:
    probability = min(0.999, max(0.001, p))
    logit = math.log(probability / (1 - probability))
    return {
        "patient_id": patient,
        "cohort": cohort,
        "modality_condition": condition,
        "p_hat": probability,
        "logit": logit,
        "label": label,
        "mc_dropout_samples": [
            min(0.999, max(0.001, probability + delta))
            for delta in (-0.02, -0.01, 0.0, 0.01, 0.02)
        ]
        * 6,
    }


def _condition_rows(
    condition: str,
    test_labels: list[int],
    test_probabilities: list[float],
    calibration_labels: list[int],
) -> list[dict[str, Any]]:
    rows = [
        _row(f"cal-{i}", "utsw_calibration", condition, label, 0.9 if label else 0.1)
        for i, label in enumerate(calibration_labels)
    ]
    for i, (label, probability) in enumerate(
        zip(test_labels, test_probabilities, strict=True)
    ):
        row = _row(f"test-{i:03d}", "utsw_internal_test", condition, label, probability)
        jitter = (i % 9 - 4) * 0.007
        row["mc_dropout_samples"] = [
            min(0.999, max(0.001, value + jitter))
            for value in row["mc_dropout_samples"]
        ]
        rows.append(row)
    return rows


def _write_meta(
    directory: Path, run_id: str, filename: str = "conditions_meta.json"
) -> None:
    payload = json.dumps({**CONDITIONS_META, "run_id": run_id}, sort_keys=True).encode()
    (directory / filename).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    (directory / f"{filename}.sha256").write_text(
        f"{digest}  {filename}\n", encoding="ascii"
    )


def _test_probabilities(ordering: str) -> tuple[list[int], list[int], list[float]]:
    calibration_labels = [i % 2 for i in range(40)]
    labels = [i % 2 for i in range(50)]
    if ordering == "perfect":
        probabilities = _perfect_probabilities(labels)
    elif ordering == "reversed":
        probabilities = _reversed_probabilities(labels)
    else:
        probabilities = [0.45 + i * 0.002 for i in range(50)]
    return calibration_labels, labels, probabilities


def _perfect_probabilities(labels: list[int]) -> list[float]:
    values = [0.9 if label else 0.1 for label in labels]
    for offset, i in enumerate(range(45, 50)):
        confidence = 0.51 + offset * 0.01
        values[i] = confidence if labels[i] == 0 else 1 - confidence
    return values


def _reversed_probabilities(labels: list[int]) -> list[float]:
    values = [0.625 if label else 0.375 for label in labels]
    for i in range(5):
        values[i] = 0.99 if labels[i] == 0 else 0.01
    return values


def _write_run_artifacts(
    run_dir: Path,
    conditions_dir: Path,
    run_id: str,
    calibration_labels: list[int],
    test_labels: list[int],
    test_probabilities: list[float],
    mismatch: str | None,
) -> None:
    prediction_rows = _condition_rows(
        "full", test_labels, test_probabilities, calibration_labels
    )
    _write_artifact(prediction_rows, run_dir / "predictions.parquet", run_id)
    for condition in CONDITIONS:
        probabilities = _condition_probabilities(condition, test_probabilities)
        rows = _condition_rows(
            condition, test_labels, probabilities, calibration_labels
        )
        if condition == mismatch:
            rows[-1]["patient_id"] = "different-final-patient"
        _write_artifact(rows, conditions_dir / f"{condition}.parquet", run_id)
    mc_rows = [row for row in prediction_rows if row["cohort"] == "utsw_internal_test"]
    _write_artifact(mc_rows, run_dir / "mc_dropout.parquet", run_id)
    _write_meta(conditions_dir, run_id)
    _write_meta(run_dir, run_id, "mc_dropout_meta.json")


def _condition_probabilities(condition: str, baseline: list[float]) -> list[float]:
    if condition == "full":
        return list(baseline)
    return [
        min(0.999, max(0.001, p + (0.015 if i % 2 else -0.015)))
        for i, p in enumerate(baseline)
    ]


def _write_artifact(rows: list[dict[str, Any]], path: Path, run_id: str) -> None:
    write_prediction_artifact(
        rows,
        path,
        run_id=run_id,
        git_sha="code-sha",
        checkpoint_hash=CHECKPOINT,
    )


def _prepare(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    run_id: str,
    *,
    ordering: str = "perfect",
    mismatch: str | None = None,
) -> Path:
    artifact_root = root / "artifacts"
    run_dir = artifact_root / "experiments" / run_id
    conditions_dir = run_dir / "conditions"
    conditions_dir.mkdir(parents=True)
    monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(artifact_root))
    (run_dir / "record.json").write_text(
        json.dumps(
            {"run_id": run_id, "status": "completed", "checkpoint_hash": CHECKPOINT}
        ),
        encoding="utf-8",
    )
    calibration_labels, test_labels, probabilities = _test_probabilities(ordering)
    _write_run_artifacts(
        run_dir,
        conditions_dir,
        run_id,
        calibration_labels,
        test_labels,
        probabilities,
        mismatch,
    )
    return run_dir


def _document(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _assert_cell_completeness(cells: dict[str, Any]) -> None:
    for mechanism in ("M1", "M2", "M3", "M5"):
        cell = cells[mechanism]
        assert cell["n"] == 50
        assert len(cell["rc_points"]) > 0
        assert set(cell["selective_risk_at_coverage"]) == {
            str(x) for x in (0.9, 0.8, 0.7, 0.6, 0.5)
        }
        assert len(cell["adjacent_grid_risk_differences"]) == 4
        assert len(cell["enrichment"]) == 5
        assert "monotonicity" in cell and "aurc_bootstrap_95_interval" in cell


def _assert_condition_outputs(result: dict[str, Any]) -> None:
    assert set(result["conditions"]) == set(CONDITIONS)
    required = {"M1", "M2", "M3", "M4", "M5", "M6", "random_confidence_control"}
    for condition in CONDITIONS:
        cells = result["conditions"][condition]
        assert set(cells) == required
        _assert_cell_completeness(cells)
        assert cells["M4"]["absent"] is True
        assert cells["M6"]["absent"] is True
        assert cells["M4"]["reason"] == "ensemble members R3-R6 not yet frozen"
        assert cells["M6"]["reason"] == "needs its own training run, D-006"
        assert cells["random_confidence_control"]["claim_attached"] is False


def _assert_conformal_outputs(result: dict[str, Any]) -> None:
    for condition in CONDITIONS:
        assert set(result["conformal"][condition]) == {"carried_over", "refit"}
        for variant in ("carried_over", "refit"):
            assert set(result["conformal"][condition][variant]) == {
                "0.05",
                "0.1",
                "0.2",
            }


def test_analysis_writes_every_condition_mechanism_and_absence_reasons(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir = _prepare(tmp_path, monkeypatch, "phase09-main")
    path = analyze_phase09("phase09-main", iterations=50, permutations=200, passes=30)
    result = _document(path)
    _assert_condition_outputs(result)
    assert all("reason" in x for x in result["results_summary"]["absent_cells"])
    _assert_conformal_outputs(result)
    text = path.read_text(encoding="utf-8").lower()
    assert "ucsf_pdgm" not in text and "egd" not in text
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert (
        path.with_name(path.name + ".sha256").read_text() == f"{digest}  {path.name}\n"
    )
    with pytest.raises(FileExistsError):
        analyze_phase09("phase09-main", iterations=50, permutations=200, passes=30)
    assert run_dir.exists()


def test_analysis_adds_ensemble_cells_when_members_are_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    main = _prepare(tmp_path, monkeypatch, "phase09-main-ensemble")
    _prepare(tmp_path, monkeypatch, "phase09-member-a")
    _prepare(tmp_path, monkeypatch, "phase09-member-b")
    path = analyze_phase09(
        "phase09-main-ensemble",
        ensemble_run_ids=["phase09-member-a", "phase09-member-b"],
        iterations=50,
        permutations=200,
        passes=30,
    )
    result = _document(path)
    assert all(
        "absent" not in result["conditions"][condition]["M4"]
        for condition in CONDITIONS
    )
    assert result["conditions"]["full"]["M4"]["n"] == 50
    assert len(result["provenance"]["ensemble_checkpoint_hashes"]) == 3
    assert main.exists()


def test_seed_reproducibility_and_different_seed_changes_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare(tmp_path, monkeypatch, "phase09-seed-a", ordering="mixed")
    _prepare(tmp_path, monkeypatch, "phase09-seed-b", ordering="mixed")
    _prepare(tmp_path, monkeypatch, "phase09-seed-c", ordering="mixed")
    first = _document(
        analyze_phase09(
            "phase09-seed-a", iterations=50, permutations=200, seed=7, passes=30
        )
    )
    same = _document(
        analyze_phase09(
            "phase09-seed-b", iterations=50, permutations=200, seed=7, passes=30
        )
    )
    other = _document(
        analyze_phase09(
            "phase09-seed-c", iterations=50, permutations=200, seed=8, passes=30
        )
    )
    assert first["conditions"] == same["conditions"]
    assert (
        first["conditions"]["full"]["M5"]["aurc_bootstrap_95_interval"]
        != other["conditions"]["full"]["M5"]["aurc_bootstrap_95_interval"]
    )


def test_planted_rankings_match_oracle_and_claim_decisions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare(tmp_path, monkeypatch, "phase09-perfect", ordering="perfect")
    _prepare(tmp_path, monkeypatch, "phase09-reversed", ordering="reversed")
    perfect = _document(
        analyze_phase09("phase09-perfect", iterations=50, permutations=200, passes=30)
    )
    reversed_result = _document(
        analyze_phase09("phase09-reversed", iterations=50, permutations=200, passes=30)
    )
    perfect_cell = perfect["conditions"]["full"]["M5"]
    reversed_cell = reversed_result["conditions"]["full"]["M5"]
    errors = [0] * 45 + [1] * 5
    assert perfect_cell["aurc_mean_over_cutoffs"] == pytest.approx(oracle_aurc(errors))
    assert perfect["claims"]["C1"]["worst_status"] == "supported"
    assert reversed_result["claims"]["C1"]["worst_status"] == "refuted"
    assert reversed_cell["monotonicity"]["magnitude"] > 0
    assert reversed_cell["aurc_mean_over_cutoffs"] > aurc_mean_over_cutoffs(
        list(reversed(range(50))), errors
    )


def test_patient_set_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare(tmp_path, monkeypatch, "phase09-mismatch", mismatch="drop_t2")
    with pytest.raises(ValueError, match="patient sets differ"):
        analyze_phase09("phase09-mismatch", iterations=50, permutations=200, passes=30)


def test_random_confidence_risk_is_flat_on_large_cohort() -> None:
    rng = np.random.default_rng(51)
    losses = (rng.random(10_000) < 0.18).astype(np.int64)
    scores = rng.uniform(size=len(losses)).tolist()
    report = _random_control(scores, losses)
    assert report["claim_attached"] is False
    assert report["maximum_absolute_grid_risk_gap_from_always_predict"] < 0.02

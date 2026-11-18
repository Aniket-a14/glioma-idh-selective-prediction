"""Phase 07 acceptance criterion 3: every fitted parameter uses calibration data only.

Each analysis entry point is run twice on identical calibration rows with a
completely different internal-test split (other labels, other logits). Every
fitted parameter in the report (temperature, conformal quantile, CRC threshold)
must be identical. A control run changes the calibration rows instead and must
change them, so the comparison cannot pass vacuously.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest
from tests.unit import test_condition_analysis as condition_fixture

from glioma_selective.evaluation.condition_analysis import analyze_conditions
from glioma_selective.evaluation.internal_analysis import analyze_internal
from glioma_selective.tracking.predictions import write_prediction_artifact
from glioma_selective.utils import paths

_FITTED_KEYS = {"temperature", "quantile", "tau", "threshold"}


def _fitted(node: Any, path: str = "") -> dict[str, Any]:
    """Every fitted parameter in a report, keyed by its JSON path."""
    found: dict[str, Any] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}/{key}"
            if key in _FITTED_KEYS and not isinstance(value, dict | list):
                found[child] = value
            else:
                found.update(_fitted(value, child))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.update(_fitted(value, f"{path}[{index}]"))
    return found


_RUN_ID = "01K6JQY7YGXSP6ZBZD3YF8QXPT"
_CAL_LABELS = [0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0]
_CAL_LOGITS = [
    -1.2, 0.9, -0.3, 1.5, -0.4, 0.2, 2.0, -0.8, 0.6, 1.1,
    0.4, -1.7, 0.8, -0.1, -2.2, 0.3, 1.9, -0.6, 0.5, -1.0,
]  # fmt: skip
_TEST_LABELS = [1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1]
_TEST_LOGITS = [
    0.2, 1.4, -0.5, 2.6, -1.1, 0.7, 0.3, -2.4, -0.2, 1.8,
    0.9, -0.3, 1.2, 0.6, -1.5, 2.1, -0.7, 0.4, -0.9, 1.3,
]  # fmt: skip


def _internal_report(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    calibration: tuple[list[int], list[float]],
    test: tuple[list[int], list[float]],
) -> dict[str, Any]:
    run_dir = root / "experiments" / _RUN_ID
    run_dir.mkdir(parents=True)
    checkpoint_hash = "c" * 64
    (run_dir / "record.json").write_text(
        json.dumps(
            {
                "run_id": _RUN_ID,
                "status": "completed",
                "checkpoint_hash": checkpoint_hash,
            }
        ),
        encoding="utf-8",
    )
    rows = []
    for cohort, (labels, logits) in (
        ("utsw_calibration", calibration),
        ("utsw_internal_test", test),
    ):
        for index, (label, logit) in enumerate(zip(labels, logits, strict=True)):
            rows.append(
                {
                    "patient_id": f"{cohort}-{index}",
                    "cohort": cohort,
                    "modality_condition": "full",
                    "p_hat": 1.0 / (1.0 + math.exp(-logit)),
                    "logit": logit,
                    "label": label,
                }
            )
    write_prediction_artifact(
        rows,
        run_dir / "predictions.parquet",
        run_id=_RUN_ID,
        git_sha="a" * 40,
        checkpoint_hash=checkpoint_hash,
    )
    monkeypatch.setattr(paths, "experiments_dir", lambda: root / "experiments")
    return json.loads(analyze_internal(_RUN_ID).read_text(encoding="utf-8"))


def test_internal_fits_ignore_the_test_split(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calibration = (_CAL_LABELS, _CAL_LOGITS)
    base = _internal_report(
        tmp_path / "a",
        monkeypatch,
        calibration=calibration,
        test=(_TEST_LABELS, _TEST_LOGITS),
    )
    other = _internal_report(
        tmp_path / "b",
        monkeypatch,
        calibration=calibration,
        test=([1 - label for label in _TEST_LABELS], [-x * 2.5 for x in _TEST_LOGITS]),
    )
    fitted = _fitted(base)
    assert len(fitted) >= 3  # temperature, conformal quantiles, CRC thresholds
    assert fitted == _fitted(other)
    # The test-split results do differ, so the two runs were not the same data.
    assert base["views"] != other["views"]


def test_internal_fits_do_respond_to_the_calibration_split(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test = (_TEST_LABELS, _TEST_LOGITS)
    base = _internal_report(
        tmp_path / "a", monkeypatch, calibration=(_CAL_LABELS, _CAL_LOGITS), test=test
    )
    shifted = _internal_report(
        tmp_path / "b",
        monkeypatch,
        calibration=(_CAL_LABELS, [x * 3.0 for x in _CAL_LOGITS]),
        test=test,
    )
    assert _fitted(base) != _fitted(shifted)


def _condition_report(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    test_labels: list[int] | None = None,
    test_logits: list[float] | None = None,
    calibration_logits: list[float] | None = None,
) -> dict[str, Any]:
    root.mkdir(parents=True)
    condition_fixture._prepare(
        root,
        monkeypatch,
        test_labels=test_labels,
        test_logits=test_logits,
        calibration_logits=calibration_logits,
    )
    return json.loads(
        analyze_conditions(condition_fixture.RUN_ID).read_text(encoding="utf-8")
    )


def test_condition_fits_ignore_the_test_split(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _condition_report(tmp_path / "a", monkeypatch)
    other = _condition_report(
        tmp_path / "b",
        monkeypatch,
        test_labels=[1, 0, 1, 0, 0, 1, 0, 1],
        test_logits=[2.5, -2.5, 0.7, -0.4, 1.9, 0.1, -1.6, 0.9],
    )
    fitted = _fitted(base)
    assert len(fitted) >= 12  # per condition: temperature, quantiles, thresholds
    assert fitted == _fitted(other)


def test_condition_fits_do_respond_to_the_calibration_split(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _condition_report(tmp_path / "a", monkeypatch)
    shifted = _condition_report(
        tmp_path / "b",
        monkeypatch,
        calibration_logits=[-0.2, 0.3, -2.2, 0.1, -0.9, 3.1, -0.5, 0.4],
    )
    assert _fitted(base) != _fitted(shifted)

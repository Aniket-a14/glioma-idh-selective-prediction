"""CPU-only contracts for the Phase 06 authorization harness."""

from __future__ import annotations

import errno
import json
from pathlib import Path
from typing import Literal

import pytest

from glioma_selective.training import authorization as auth


def _result(
    name: str,
    status: Literal["passed", "failed", "not_run"] = "passed",
    detail: str = "ok",
) -> auth.StepResult:
    return auth.StepResult(name, status, detail, 0.01)


def _mock_all_steps(
    monkeypatch: pytest.MonkeyPatch, *, failure: int | None = None
) -> list[str]:
    calls: list[str] = []
    names = auth.STEP_NAMES
    funcs = (
        "step_cpu_unit_tests",
        "step_data_sample",
        "step_tiny_forward",
        "step_tiny_overfit",
        "step_gpu_memory",
        "step_checkpoint_equivalence",
    )
    for index, (function, name) in enumerate(zip(funcs, names, strict=False)):

        def fake(*args, _index=index, _name=name, **kwargs):  # type: ignore[no-untyped-def]
            del args, kwargs
            calls.append(_name)
            status: Literal["passed", "failed"] = (
                "failed" if failure == _index else "passed"
            )
            return _result(_name, status)

        monkeypatch.setattr(auth, function, fake)

    def logging_step(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        calls.append(names[6])
        status: Literal["passed", "failed"] = "failed" if failure == 6 else "passed"
        return _result(names[6], status)

    monkeypatch.setattr(auth, "step_deterministic_logging", logging_step)
    monkeypatch.setattr(auth, "_frozen_hashes", lambda: {"splits.json": "a" * 64})
    return calls


def test_run_harness_uses_the_seven_steps_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _mock_all_steps(monkeypatch)
    report = auth.run_harness(device="cpu", synthetic=False, run_cpu_tests=True)

    assert calls == list(auth.STEP_NAMES)
    assert tuple(result.name for result in report.results) == auth.STEP_NAMES


def test_run_harness_stops_at_first_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _mock_all_steps(monkeypatch, failure=2)
    report = auth.run_harness(device="cpu", run_cpu_tests=True)

    assert calls == list(auth.STEP_NAMES[:3])
    assert report.results[2].status == "failed"
    assert all(result.status == "not_run" for result in report.results[3:])
    assert not report.authorized


def test_not_run_is_not_a_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _mock_all_steps(monkeypatch)

    def not_run_data() -> auth.StepResult:
        calls.append(auth.STEP_NAMES[1])
        return _result(auth.STEP_NAMES[1], "not_run", "no data")

    monkeypatch.setattr(auth, "step_data_sample", not_run_data)
    report = auth.run_harness(device="cpu", run_cpu_tests=True)

    assert calls == list(auth.STEP_NAMES)
    assert report.results[1].status == "not_run"
    assert report.authorized is False


def test_report_round_trip_and_write_once(tmp_path: Path) -> None:
    report = auth.HarnessReport(
        results=(_result(auth.STEP_NAMES[0]),),
        authorized=False,
        device="cpu",
        git_sha="sha",
        git_dirty=False,
        config_sha256="config",
        frozen_hashes={"splits.json": "split"},
        timestamp_utc="2026-09-30T00:00:00Z",
        harness_version=auth.HARNESS_VERSION,
        authorization_run_id="01K6AZE69H5X32FK2PB1YNJ0MZ",
    )
    path = tmp_path / "authorization_report.json"
    assert auth.write_harness_report(report, path) == path
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["authorized"] is False
    assert stored["results"][0]["name"] == auth.STEP_NAMES[0]
    with pytest.raises(FileExistsError, match="already exists"):
        auth.write_harness_report(report, path)


def test_report_writer_uses_atomic_rename_without_hard_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = auth.HarnessReport(
        results=(),
        authorized=False,
        device="cpu",
        git_sha="sha",
        git_dirty=False,
        config_sha256="config",
        frozen_hashes={},
        timestamp_utc="2026-09-30T00:00:00Z",
        harness_version=auth.HARNESS_VERSION,
        authorization_run_id="01K6AZE69H5X32FK2PB1YNJ0MZ",
    )
    path = tmp_path / "authorization_report.json"

    def unsupported_hardlink(*args, **kwargs):  # type: ignore[no-untyped-def]
        del args, kwargs
        raise OSError(errno.EOPNOTSUPP, "hard links are unavailable")

    monkeypatch.setattr(auth.os, "link", unsupported_hardlink)
    auth.write_harness_report(report, path)

    assert json.loads(path.read_text(encoding="utf-8"))["authorized"] is False
    with pytest.raises(FileExistsError, match="already exists"):
        auth.write_harness_report(report, path)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"git_sha": "wrong"}, "git SHA"),
        ({"config_sha256": "wrong"}, "config hash"),
        ({"device": "cpu"}, "CUDA"),
        ({"authorized": False}, "not authorized"),
    ],
)
def test_assert_authorized_rejects_mismatches(
    tmp_path: Path, changes: dict[str, object], message: str
) -> None:
    report = {
        "authorized": True,
        "synthetic": False,
        "device": "cuda:0",
        "git_sha": "current",
        "config_sha256": "config",
        "results": [{"name": name, "status": "passed"} for name in auth.STEP_NAMES],
    }
    report.update(changes)
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        auth.assert_authorized(path, git_sha="current", config_sha256="config")


def test_synthetic_harness_is_never_authorized(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _mock_all_steps(monkeypatch)
    report = auth.run_harness(device="cpu", synthetic=True, run_cpu_tests=True)

    assert calls == [auth.STEP_NAMES[0], *auth.STEP_NAMES[2:]]
    assert report.synthetic is True
    assert report.authorized is False
    assert "synthetic" in report.results[-1].detail


def test_dry_run_lists_steps_without_running_harness(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import authorize_training

    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("dry-run invoked the harness")

    monkeypatch.setattr(auth, "run_harness", forbidden)
    assert authorize_training.main(["--dry-run"]) == 0
    output = capsys.readouterr().out
    assert all(name in output for name in auth.STEP_NAMES)
    assert output.count("not_run") == 7


def test_tiny_overfit_fails_when_learning_rate_is_zero() -> None:
    result = auth.step_tiny_overfit(
        "cpu", synthetic=True, max_steps=2, overfit_threshold=0.05, learning_rate=0.0
    )

    assert result.status == "failed"
    assert "final_loss=" in result.detail


def test_report_contains_no_fixture_patient_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_all_steps(monkeypatch)
    report = auth.run_harness(device="cpu", run_cpu_tests=True)
    rendered = json.dumps(auth.asdict(report))

    for patient_id in ("UTSW-BT0001", "UTSW-BT0002", "UTSW-BT0003", "UTSW-BT0004"):
        assert patient_id not in rendered

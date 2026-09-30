"""Tests for launch-time capture and run-record lifecycle handling."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from glioma_selective.tracking import run_record


def _synthetic_repo(root: Path) -> Path:
    root.mkdir(parents=True)
    subprocess.run(("git", "init", "-q", str(root)), check=True)
    subprocess.run(
        ("git", "-C", str(root), "config", "user.email", "test@example.com"),
        check=True,
    )
    subprocess.run(
        ("git", "-C", str(root), "config", "user.name", "Unit Test"),
        check=True,
    )
    tracked = root / "tracked.txt"
    tracked.write_text("initial\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(root), "add", "tracked.txt"), check=True)
    subprocess.run(("git", "-C", str(root), "commit", "-qm", "initial"), check=True)
    return root


def _environment_fingerprint() -> dict[str, str]:
    return {
        "python": "3.12.test",
        "dependency_lock_hash": "lock-digest",
        "pytorch": "2.test",
        "monai": "1.test",
        "gpu_model": "not available (test)",
        "vram": "not available (test)",
        "cuda_runtime": "not available (test)",
        "driver": "not available (test)",
    }


def _build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, repo: Path | None = None
) -> run_record.RunRecord:
    storage = tmp_path / "storage"
    manifests = storage / "data" / "manifests"
    manifests.mkdir(parents=True, exist_ok=True)
    split_digest = hashlib.sha256(b"split").hexdigest()
    (manifests / "splits.json.sha256").write_text(
        f"{split_digest}  splits.json\n", encoding="ascii"
    )
    monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(storage))
    monkeypatch.delenv("GLIOMA_DATA_ROOT", raising=False)
    monkeypatch.delenv("GLIOMA_ARTIFACT_ROOT", raising=False)
    monkeypatch.setattr(
        run_record,
        "capture_environment",
        lambda _repo_root: _environment_fingerprint(),
    )
    repository = repo or _synthetic_repo(tmp_path / "repo")
    return run_record.build_run_record(
        dataset_manifest_hash="dataset-digest",
        exclusion_list_hash="exclusion-digest",
        config={"model": {"resolved": True}},
        seed=17,
        preprocessing_version="standard-1mm-v1",
        parameter_hash="parameter-digest",
        normalization_stats_sha256="normalization-digest",
        repo_root=repository,
    )


def _complete_data(record: run_record.RunRecord) -> dict[str, Any]:
    data = run_record._record_data(record)
    data.update(
        {
            "checkpoint_hash": "checkpoint-digest",
            "training_history": [{"epoch": 1, "loss": 0.5}],
            "predictions_path": "not_applicable: no predictions in this phase",
            "calibration_params": "not_applicable: always-predict baseline",
            "selective_thresholds": "not_applicable: always-predict baseline",
            "metrics": {"loss": 0.5},
            "log_path": "run.log",
        }
    )
    return data


def test_build_captures_exact_launch_keys_and_embeds_normalization_hash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    record = _build(monkeypatch, tmp_path)
    data = run_record._record_data(record)

    assert tuple(key for key in run_record.MANDATORY_KEYS if key in data) == (
        *run_record.LAUNCH_KEYS,
        *run_record.END_KEYS,
    )
    assert set(data) == set(run_record.MANDATORY_KEYS) | set(run_record.LIFECYCLE_KEYS)
    assert record.git_dirty is False
    assert record.dataset_manifest_hash == "dataset-digest"
    assert record.split_manifest_hash == hashlib.sha256(b"split").hexdigest()
    assert record.exclusion_list_hash == "exclusion-digest"
    assert record.config == {"model": {"resolved": True}}
    assert record.python_version == "3.12.test"
    assert record.torch_version == "2.test"
    assert record.monai_version == "1.test"
    assert record.preprocessing_version == {
        "version": "standard-1mm-v1",
        "parameter_hash": "parameter-digest",
        "normalization_stats_sha256": "normalization-digest",
    }
    assert run_record.validate_run_record(record) == list(run_record.END_KEYS)
    run_record.assert_launch_ready(record)


@pytest.mark.parametrize("missing_key", run_record.MANDATORY_KEYS)
def test_validate_reports_each_missing_mandatory_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing_key: str
) -> None:
    record = _build(monkeypatch, tmp_path)
    data = _complete_data(record)
    del data[missing_key]

    assert run_record.validate_run_record(data) == [missing_key]


def test_validate_treats_none_and_empty_values_as_missing() -> None:
    record: dict[str, Any] = {key: "value" for key in run_record.MANDATORY_KEYS}
    record["training_history"] = None
    record["metrics"] = {}
    record["log_path"] = ""

    assert run_record.validate_run_record(record) == [
        "training_history",
        "metrics",
        "log_path",
    ]


def test_launch_ready_requires_clean_bool_git_state() -> None:
    launch: dict[str, Any] = {key: "value" for key in run_record.LAUNCH_KEYS}
    launch["git_dirty"] = False
    run_record.assert_launch_ready(launch)
    launch["git_dirty"] = "false"
    with pytest.raises(ValueError, match="git_dirty must be a bool"):
        run_record.assert_launch_ready(launch)
    launch["git_dirty"] = True
    with pytest.raises(ValueError, match="clean"):
        run_record.assert_launch_ready(launch)


def test_assert_complete_accepts_explicit_not_applicable_values() -> None:
    record: dict[str, Any] = {key: "value" for key in run_record.MANDATORY_KEYS}
    record["calibration_params"] = "not_applicable: uncalibrated baseline"
    record["selective_thresholds"] = "not_applicable: always-predict baseline"

    run_record.assert_complete(record)


def test_dirty_state_uses_git_status_porcelain_and_ignores_ignored_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _synthetic_repo(tmp_path / "repo")
    (repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(repo), "add", ".gitignore"), check=True)
    subprocess.run(("git", "-C", str(repo), "commit", "-qm", "ignore file"), check=True)
    (repo / "ignored.txt").write_text("ignored\n", encoding="utf-8")
    record = _build(monkeypatch, tmp_path, repo=repo)
    assert record.git_dirty is False

    (repo / "tracked.txt").write_text("modified\n", encoding="utf-8")
    dirty_record = _build(monkeypatch, tmp_path, repo=repo)
    assert dirty_record.git_dirty is True


def test_untracked_file_makes_git_dirty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _synthetic_repo(tmp_path / "repo")
    (repo / "untracked.txt").write_text("new\n", encoding="utf-8")

    assert _build(monkeypatch, tmp_path, repo=repo).git_dirty is True


def test_write_is_atomic_write_once_and_round_trips_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    record = _build(monkeypatch, tmp_path)
    path = run_record.write_run_record(record, record.run_id)

    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored == run_record._record_data(record)
    storage = tmp_path / "storage"
    assert path.is_relative_to(storage)
    stored_paths = sorted(
        item.relative_to(storage).as_posix() for item in storage.rglob("*")
    )
    assert stored_paths == [
        "artifacts",
        "artifacts/experiments",
        f"artifacts/experiments/{record.run_id}",
        f"artifacts/experiments/{record.run_id}/record.json",
        "data",
        "data/manifests",
        "data/manifests/splits.json.sha256",
    ]
    assert list(path.parent.iterdir()) == [path]
    with pytest.raises(FileExistsError, match="already exists"):
        run_record.write_run_record(record)


def test_update_only_sets_end_and_lifecycle_fields_and_can_complete(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    record = _build(monkeypatch, tmp_path)
    path = run_record.write_run_record(record)

    with pytest.raises(ValueError, match="cannot change fields"):
        run_record.update_run_record(record.run_id, seed=99)
    with pytest.raises(ValueError, match="cannot change fields"):
        run_record.update_run_record(record.run_id, git_dirty=True)

    updated = run_record.update_run_record(
        record.run_id,
        checkpoint_hash="checkpoint-digest",
        training_history=[{"epoch": 1, "loss": 0.5}],
        predictions_path="not_applicable: no predictions in this phase",
        calibration_params="not_applicable: always-predict baseline",
        selective_thresholds="not_applicable: always-predict baseline",
        metrics={"loss": 0.5},
        log_path="run.log",
        status="completed",
        end_time_utc="2026-09-30T12:00:00Z",
    )

    assert updated == path
    final = json.loads(path.read_text(encoding="utf-8"))
    assert final["seed"] == record.seed
    assert final["status"] == "completed"
    assert final["end_time_utc"] == "2026-09-30T12:00:00Z"
    assert run_record.validate_run_record(path) == []
    run_record.assert_complete(final)
    assert list(path.parent.iterdir()) == [path]


def test_run_id_is_monotonic_unique_and_crockford_base32(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(run_record, "_LAST_ULID_TIME", -1)
    monkeypatch.setattr(run_record, "_LAST_ULID_RANDOM", -1)
    monkeypatch.setattr(run_record.time, "time", lambda: 1_800_000_000.0)

    first = run_record.generate_run_id()
    second = run_record.generate_run_id()

    alphabet = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
    assert len(first) == 26
    assert set(first) <= alphabet
    assert first < second
    assert len({first, second, run_record.generate_run_id()}) == 3


def test_sha256_file_matches_standard_digest(tmp_path: Path) -> None:
    file_path = tmp_path / "manifest.json"
    file_path.write_bytes(b'{"manifest":true}\n')

    expected = hashlib.sha256(file_path.read_bytes()).hexdigest()
    assert run_record.sha256_file(file_path) == expected

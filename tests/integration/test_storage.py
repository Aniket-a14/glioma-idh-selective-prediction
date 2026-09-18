"""Integration tests for the external-storage bootstrap script."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_SCRIPT = REPOSITORY_ROOT / "scripts" / "bootstrap_storage.py"


@pytest.fixture(autouse=True)
def _repository_links_are_clean() -> None:
    """Keep subprocess tests from sharing repository-level link state."""

    links = (REPOSITORY_ROOT / "data", REPOSITORY_ROOT / "artifacts")
    for link in links:
        if link.exists() or link.is_symlink():
            pytest.fail(f"integration test path is already present: {link}")
    yield
    for link in links:
        if link.is_symlink():
            link.unlink()


def _run_bootstrap(
    storage_root: Path | None,
    *,
    data_root: Path | None = None,
    artifact_root: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment.pop("GLIOMA_STORAGE_ROOT", None)
    environment.pop("GLIOMA_DATA_ROOT", None)
    environment.pop("GLIOMA_ARTIFACT_ROOT", None)
    if storage_root is not None:
        environment["GLIOMA_STORAGE_ROOT"] = str(storage_root)
    if data_root is not None:
        environment["GLIOMA_DATA_ROOT"] = str(data_root)
    if artifact_root is not None:
        environment["GLIOMA_ARTIFACT_ROOT"] = str(artifact_root)
    return subprocess.run(
        [sys.executable, str(BOOTSTRAP_SCRIPT)],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_bootstrap_is_idempotent_and_preserves_external_symlink(
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    external_volume = tmp_path / "external-volume"
    external_volume.mkdir()
    data_target = storage_root / "data"
    data_target.mkdir()
    external_link = data_target / "external"
    external_link.symlink_to(external_volume, target_is_directory=True)

    first = _run_bootstrap(storage_root)
    second = _run_bootstrap(storage_root)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first.stdout == second.stdout
    assert (REPOSITORY_ROOT / "data").is_symlink()
    assert (REPOSITORY_ROOT / "data").resolve() == data_target.resolve()
    assert (REPOSITORY_ROOT / "artifacts").is_symlink()
    assert (REPOSITORY_ROOT / "artifacts").resolve() == (
        storage_root / "artifacts"
    ).resolve()
    assert external_link.is_symlink()
    assert external_link.resolve() == external_volume.resolve()


def test_bootstrap_creates_missing_targets(
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "new-storage"

    result = _run_bootstrap(storage_root)

    assert result.returncode == 0, result.stderr
    assert (storage_root / "data").is_dir()
    assert (storage_root / "artifacts").is_dir()


def test_bootstrap_refuses_to_overwrite_non_symlink(
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    data_entry = REPOSITORY_ROOT / "data"
    data_entry.mkdir()
    marker = data_entry / "keep.txt"
    marker.write_text("do not overwrite", encoding="utf-8")

    try:
        result = _run_bootstrap(storage_root)

        assert result.returncode != 0
        assert "Refusing to overwrite non-symlink" in result.stderr
        assert marker.read_text(encoding="utf-8") == "do not overwrite"
    finally:
        marker.unlink()
        data_entry.rmdir()


def test_bootstrap_refuses_to_replace_symlink_to_wrong_target(
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    wrong_target = tmp_path / "wrong-target"
    wrong_target.mkdir()
    data_entry = REPOSITORY_ROOT / "data"
    data_entry.symlink_to(wrong_target, target_is_directory=True)

    result = _run_bootstrap(storage_root)

    assert result.returncode != 0
    assert "Refusing to overwrite symlink" in result.stderr


def test_bootstrap_reports_broken_managed_symlink(
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    data_entry = REPOSITORY_ROOT / "data"
    data_entry.symlink_to(tmp_path / "missing-data", target_is_directory=True)

    result = _run_bootstrap(storage_root)

    assert result.returncode != 0
    assert "broken symlink" in result.stderr.lower()

    data_entry.unlink()


def test_bootstrap_reports_broken_external_symlink(
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "storage"
    data_target = storage_root / "data"
    data_target.mkdir(parents=True)
    (storage_root / "artifacts").mkdir()
    missing_external = data_target / "external"
    missing_external.symlink_to(tmp_path / "missing-external", target_is_directory=True)

    result = _run_bootstrap(storage_root)

    assert result.returncode != 0
    assert "broken symlink" in result.stderr.lower()

    (REPOSITORY_ROOT / "data").unlink(missing_ok=True)
    (REPOSITORY_ROOT / "artifacts").unlink(missing_ok=True)


def test_bootstrap_fails_clearly_when_storage_root_is_unset() -> None:
    result = _run_bootstrap(None)

    assert result.returncode != 0
    assert "GLIOMA_STORAGE_ROOT" in result.stderr
    assert "not set" in result.stderr

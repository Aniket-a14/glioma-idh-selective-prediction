"""Unit tests for glioma_selective.utils.paths — the canonical root abstraction.

Covers Phase 00 acceptance criterion 5: resolution from environment, a clear
and actionable error when a required variable is unset, ``Path`` objects
returned, and no absolute path leaking into the return for an unset root.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from glioma_selective.utils import paths


@pytest.fixture(autouse=True)
def _clear_root_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test starts with none of the three root variables set."""
    for var in ("GLIOMA_STORAGE_ROOT", "GLIOMA_DATA_ROOT", "GLIOMA_ARTIFACT_ROOT"):
        monkeypatch.delenv(var, raising=False)


class TestStorageRoot:
    def test_resolves_from_environment(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "storage-root"
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(storage_root))
        assert paths.storage_root() == storage_root

    def test_returns_path_instance(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(tmp_path / "storage-root"))
        assert isinstance(paths.storage_root(), Path)

    def test_expands_user_home(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "~/glioma-storage")
        assert "~" not in str(paths.storage_root())

    def test_missing_variable_raises_actionable_error(self) -> None:
        with pytest.raises(paths.PathResolutionError) as excinfo:
            paths.storage_root()
        message = str(excinfo.value)
        assert "GLIOMA_STORAGE_ROOT" in message
        assert ".env" in message

    def test_empty_string_treated_as_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "")
        with pytest.raises(paths.PathResolutionError):
            paths.storage_root()

    def test_no_leaked_default_when_unset(self) -> None:
        """An unset root must raise, never silently resolve to some path
        (e.g. the current working directory) that could cause data to be
        written inside the repository."""
        with pytest.raises(paths.PathResolutionError):
            paths.storage_root()

    def test_relative_path_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "relative/storage-root")
        with pytest.raises(paths.PathResolutionError):
            paths.storage_root()

    def test_trailing_slash_is_normalized(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "storage-root"
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", f"{storage_root}/")
        assert paths.storage_root() == storage_root

    def test_nonexistent_parent_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "missing-parent" / "storage-root"
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(storage_root))
        with pytest.raises(paths.PathResolutionError):
            paths.storage_root()


class TestDataRoot:
    def test_defaults_to_storage_root_slash_data(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "storage-root"
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(storage_root))
        assert paths.data_root() == storage_root / "data"

    def test_override_takes_precedence(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(tmp_path / "storage-root"))
        fast_data = tmp_path / "fast-data"
        monkeypatch.setenv("GLIOMA_DATA_ROOT", str(fast_data))
        assert paths.data_root() == fast_data

    def test_override_alone_does_not_require_storage_root(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        fast_data = tmp_path / "fast-data"
        monkeypatch.setenv("GLIOMA_DATA_ROOT", str(fast_data))
        assert paths.data_root() == fast_data

    def test_raises_when_neither_set(self) -> None:
        with pytest.raises(paths.PathResolutionError):
            paths.data_root()


class TestArtifactRoot:
    def test_defaults_to_storage_root_slash_artifacts(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "storage-root"
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(storage_root))
        assert paths.artifact_root() == storage_root / "artifacts"

    def test_override_takes_precedence(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(tmp_path / "storage-root"))
        fast_artifacts = tmp_path / "fast-artifacts"
        monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", str(fast_artifacts))
        assert paths.artifact_root() == fast_artifacts


@pytest.mark.parametrize(
    ("accessor_name", "expected_suffix"),
    [
        ("raw_data_dir", "data/raw"),
        ("external_data_dir", "data/external"),
        ("interim_data_dir", "data/interim"),
        ("processed_data_dir", "data/processed"),
        ("manifests_dir", "data/manifests"),
        ("private_data_dir", "data/private"),
        ("cache_dir", "artifacts/cache"),
        ("checkpoints_dir", "artifacts/checkpoints"),
        ("experiments_dir", "artifacts/experiments"),
        ("predictions_dir", "artifacts/predictions"),
        ("figures_dir", "artifacts/figures"),
        ("logs_dir", "artifacts/logs"),
        ("mlflow_dir", "artifacts/mlflow"),
    ],
)
def test_subdirectory_accessors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    accessor_name: str,
    expected_suffix: str,
) -> None:
    storage_root = tmp_path / "storage-root"
    monkeypatch.setenv("GLIOMA_STORAGE_ROOT", str(storage_root))
    accessor = getattr(paths, accessor_name)
    result = accessor()
    assert isinstance(result, Path)
    assert result == storage_root / expected_suffix


def test_all_public_names_are_exported() -> None:
    for name in paths.__all__:
        assert hasattr(paths, name)

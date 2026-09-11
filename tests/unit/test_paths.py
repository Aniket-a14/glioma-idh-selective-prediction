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
    def test_resolves_from_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "/Volumes/GliomaSSD")
        assert paths.storage_root() == Path("/Volumes/GliomaSSD")

    def test_returns_path_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "/Volumes/GliomaSSD")
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

    def test_empty_string_treated_as_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "")
        with pytest.raises(paths.PathResolutionError):
            paths.storage_root()

    def test_no_leaked_default_when_unset(self) -> None:
        """An unset root must raise, never silently resolve to some path
        (e.g. the current working directory) that could cause data to be
        written inside the repository."""
        with pytest.raises(paths.PathResolutionError):
            paths.storage_root()


class TestDataRoot:
    def test_defaults_to_storage_root_slash_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "/Volumes/GliomaSSD")
        assert paths.data_root() == Path("/Volumes/GliomaSSD/data")

    def test_override_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "/Volumes/GliomaSSD")
        monkeypatch.setenv("GLIOMA_DATA_ROOT", "/mnt/fast-data")
        assert paths.data_root() == Path("/mnt/fast-data")

    def test_override_alone_does_not_require_storage_root(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GLIOMA_DATA_ROOT", "/mnt/fast-data")
        assert paths.data_root() == Path("/mnt/fast-data")

    def test_raises_when_neither_set(self) -> None:
        with pytest.raises(paths.PathResolutionError):
            paths.data_root()


class TestArtifactRoot:
    def test_defaults_to_storage_root_slash_artifacts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "/Volumes/GliomaSSD")
        assert paths.artifact_root() == Path("/Volumes/GliomaSSD/artifacts")

    def test_override_takes_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "/Volumes/GliomaSSD")
        monkeypatch.setenv("GLIOMA_ARTIFACT_ROOT", "/mnt/fast-artifacts")
        assert paths.artifact_root() == Path("/mnt/fast-artifacts")


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
    monkeypatch: pytest.MonkeyPatch, accessor_name: str, expected_suffix: str
) -> None:
    monkeypatch.setenv("GLIOMA_STORAGE_ROOT", "/Volumes/GliomaSSD")
    accessor = getattr(paths, accessor_name)
    result = accessor()
    assert isinstance(result, Path)
    assert result == Path("/Volumes/GliomaSSD") / expected_suffix


def test_all_public_names_are_exported() -> None:
    for name in paths.__all__:
        assert hasattr(paths, name)

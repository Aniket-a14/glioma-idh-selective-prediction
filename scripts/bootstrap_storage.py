#!/usr/bin/env python3
"""Create the repository's links to external data and artifact storage."""

from __future__ import annotations

import sys
from pathlib import Path

# Running ``python scripts/bootstrap_storage.py`` does not put the repository's
# ``src/`` directory on ``sys.path``. Add this worktree's source tree before
# importing the canonical path abstraction, so the script does not depend on
# whichever checkout happens to be installed in the interpreter.
REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.utils import paths  # noqa: E402  # bootstrap source path


class StorageBootstrapError(RuntimeError):
    """Raised when storage cannot be prepared without overwriting user data."""


def _ensure_target_directory(target: Path) -> None:
    """Create *target* if needed and verify that it is a directory."""

    if target.is_symlink():
        if not target.exists():
            raise StorageBootstrapError(f"Storage target is a broken symlink: {target}")
        if not target.is_dir():
            raise StorageBootstrapError(f"Storage target is not a directory: {target}")
        return

    if target.exists():
        if not target.is_dir():
            raise StorageBootstrapError(f"Storage target is not a directory: {target}")
        return

    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise StorageBootstrapError(
            f"Could not create storage target directory {target}: {exc}"
        ) from exc

    if not target.is_dir():
        raise StorageBootstrapError(
            f"Storage target does not exist as a directory after creation: {target}"
        )


def _resolve_existing_link(link: Path) -> Path:
    """Resolve an existing link, reporting a dangling link clearly."""

    try:
        return link.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as exc:
        raise StorageBootstrapError(f"Found a broken symlink: {link}") from exc


def _ensure_managed_symlink(link: Path, target: Path) -> None:
    """Create *link* or accept it only when it already targets *target*."""

    if link.is_symlink():
        actual = _resolve_existing_link(link)
        expected = target.resolve(strict=False)
        if actual == expected:
            _ensure_target_directory(target)
            return
        raise StorageBootstrapError(
            f"Refusing to overwrite symlink {link}: it points to {actual}, "
            f"not the configured target {expected}"
        )

    if link.exists():
        raise StorageBootstrapError(
            f"Refusing to overwrite non-symlink at {link}; move it aside "
            "before running storage bootstrap"
        )

    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        raise StorageBootstrapError(
            f"Could not create storage symlink {link} -> {target}: {exc}"
        ) from exc


def _validate_external_link(data_target: Path) -> None:
    """Preserve a separately managed ``data/external`` symlink if present."""

    external = data_target / "external"
    if not external.exists() and not external.is_symlink():
        return

    if not external.is_symlink():
        raise StorageBootstrapError(
            f"Refusing to replace data/external because it is not a symlink: {external}"
        )

    _resolve_existing_link(external)


def bootstrap_storage(repository_root: Path) -> None:
    """Prepare external storage and the repository-level symlinks.

    ``GLIOMA_STORAGE_ROOT`` is required even when optional root overrides are
    present. The target directories are created when absent; existing
    repository entries are never replaced.
    """

    paths.storage_root()
    data_target = paths.data_root()
    artifact_target = paths.artifact_root()

    managed_links = (
        (repository_root / "data", data_target),
        (repository_root / "artifacts", artifact_target),
    )
    for link, target in managed_links:
        if not link.is_symlink() and link.exists():
            raise StorageBootstrapError(
                f"Refusing to overwrite non-symlink at {link}; move it aside "
                "before running storage bootstrap"
            )
        if link.is_symlink():
            _resolve_existing_link(link)
        else:
            _ensure_target_directory(target)
        _ensure_managed_symlink(link, target)

    _validate_external_link(data_target)


def main() -> int:
    """Run storage bootstrap and return a process status code."""

    try:
        bootstrap_storage(REPOSITORY_ROOT)
    except (OSError, paths.PathResolutionError, StorageBootstrapError) as exc:
        print(f"Storage bootstrap failed: {exc}", file=sys.stderr)
        return 1

    print("Storage bootstrap complete: data/ and artifacts/ are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

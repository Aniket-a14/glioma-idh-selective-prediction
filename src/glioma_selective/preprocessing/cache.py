"""Content-addressed, resumable cache for preprocessing stages."""

from __future__ import annotations

import errno
import hashlib
import json
import math
import os
import shutil
import tempfile
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from glioma_selective.utils import paths

_HASH_CHUNK_SIZE: Final[int] = 1024 * 1024
_MANIFEST_NAME: Final[str] = "manifest.json"
type _JSONValue = (
    None | bool | int | float | str | list[_JSONValue] | dict[str, _JSONValue]
)
type ComputeFunction = Callable[[Path], object]


def _canonicalize(value: object, *, location: str = "$") -> _JSONValue:
    """Return a JSON-compatible value with deterministic container ordering."""

    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite float at {location} is not cacheable")
        return value
    if isinstance(value, Mapping):
        result: dict[str, _JSONValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"cache parameters require string mapping keys; "
                    f"found {key!r} at {location}"
                )
            result[key] = _canonicalize(item, location=f"{location}.{key}")
        return result
    if isinstance(value, list | tuple):
        return [
            _canonicalize(item, location=f"{location}[{index}]")
            for index, item in enumerate(value)
        ]
    raise TypeError(
        f"value at {location} is not JSON-serialisable: {type(value).__name__}"
    )


def _canonical_json_bytes(value: object) -> bytes:
    canonical_value = _canonicalize(value)
    try:
        encoded = json.dumps(
            canonical_value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise type(error)(
            f"cache value is not canonically JSON-serialisable: {error}"
        ) from error
    return encoded.encode("utf-8")


def stage_cache_key(
    stage: str,
    stage_version: str,
    params: Mapping[str, object],
    input_keys: Sequence[str],
) -> str:
    """Return the SHA-256 key for one stage invocation.

    The digest covers the stage name and version, canonicalized parameters, and
    the ordered keys of all direct inputs.  An upstream stage key can therefore
    be supplied as an input key to invalidate every downstream stage.
    """

    if not isinstance(stage, str) or not isinstance(stage_version, str):
        raise TypeError("stage and stage_version must be strings")
    normalized_input_keys = list(input_keys)
    if any(not isinstance(input_key, str) for input_key in normalized_input_keys):
        raise TypeError("input_keys must contain only strings")
    payload = {
        "input_keys": normalized_input_keys,
        "params": params,
        "stage": stage,
        "stage_version": stage_version,
    }
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def hash_file(path: Path) -> str:
    """Return a streaming SHA-256 digest for ``path``."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


class StageCache:
    """Store complete preprocessing-stage outputs under a content key."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else paths.processed_data_dir()

    def get(self, stage: str, key: str) -> Path | None:
        """Return a valid output directory, or ``None`` for a cache miss."""

        target = self._entry_path(stage, key)
        if not target.is_dir():
            return None
        manifest_path = target / _MANIFEST_NAME
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        if not isinstance(manifest, dict) or manifest.get("stage") != stage:
            return None
        outputs = manifest.get("outputs")
        if not isinstance(outputs, dict):
            return None
        for relative_name, expected_hash in outputs.items():
            if not isinstance(relative_name, str) or not isinstance(expected_hash, str):
                return None
            output_path = self._safe_output_path(target, relative_name)
            if (
                output_path is None
                or output_path.is_symlink()
                or not output_path.is_file()
            ):
                return None
            try:
                if hash_file(output_path) != expected_hash:
                    return None
            except OSError:
                return None
        return target

    def put(
        self,
        stage: str,
        key: str,
        output_dir: Path,
        *,
        stage_version: str | None = None,
        params: Mapping[str, object] | None = None,
        input_keys: Sequence[str] = (),
    ) -> Path:
        """Copy outputs from ``output_dir`` and atomically publish the entry."""

        normalized_params = _canonicalize({} if params is None else params)
        if not isinstance(normalized_params, dict):
            raise TypeError("cache params must be a mapping")
        normalized_input_keys = self._validate_input_keys(input_keys)
        self._validate_key_metadata(
            stage,
            key,
            stage_version=stage_version,
            params=params,
            input_keys=normalized_input_keys,
        )
        source = Path(output_dir)
        if not source.is_dir():
            raise ValueError(f"cache output directory does not exist: {source}")
        temporary = self._temporary_directory(stage, key)
        try:
            self._copy_outputs(source, temporary)
            return self._publish(
                stage,
                key,
                temporary,
                stage_version=stage_version,
                params=normalized_params,
                input_keys=normalized_input_keys,
            )
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    def get_or_compute(
        self,
        stage: str,
        key: str,
        compute_fn: ComputeFunction,
        *,
        stage_version: str | None = None,
        params: Mapping[str, object] | None = None,
        input_keys: Sequence[str] = (),
    ) -> Path:
        """Get a valid entry or compute and atomically publish a new one."""

        normalized_params = _canonicalize({} if params is None else params)
        if not isinstance(normalized_params, dict):
            raise TypeError("cache params must be a mapping")
        normalized_input_keys = self._validate_input_keys(input_keys)
        self._validate_key_metadata(
            stage,
            key,
            stage_version=stage_version,
            params=params,
            input_keys=normalized_input_keys,
        )
        cached = self.get(stage, key)
        if cached is not None:
            return cached

        temporary = self._temporary_directory(stage, key)
        try:
            compute_fn(temporary)
            return self._publish(
                stage,
                key,
                temporary,
                stage_version=stage_version,
                params=normalized_params,
                input_keys=normalized_input_keys,
            )
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    def _entry_path(self, stage: str, key: str) -> Path:
        self._validate_component(stage, "stage")
        self._validate_component(key, "key")
        return self.root / stage / key[:2] / key

    def _temporary_directory(self, stage: str, key: str) -> Path:
        entry_parent = self._entry_path(stage, key).parent
        entry_parent.mkdir(parents=True, exist_ok=True)
        return Path(
            tempfile.mkdtemp(prefix=f".{key}.", suffix=".tmp", dir=entry_parent)
        )

    @staticmethod
    def _validate_component(value: str, name: str) -> None:
        if not isinstance(value, str) or not value or value in {".", ".."}:
            raise ValueError(f"cache {name} must be one non-empty path component")
        if Path(value).name != value or "/" in value or "\\" in value:
            raise ValueError(f"cache {name} must be one non-empty path component")

    @staticmethod
    def _validate_input_keys(input_keys: Sequence[str]) -> list[str]:
        normalized = list(input_keys)
        if any(not isinstance(input_key, str) for input_key in normalized):
            raise TypeError("input_keys must contain only strings")
        return normalized

    @staticmethod
    def _validate_key_metadata(
        stage: str,
        key: str,
        *,
        stage_version: str | None,
        params: Mapping[str, object] | None,
        input_keys: Sequence[str],
    ) -> None:
        if stage_version is None or params is None:
            return
        expected_key = stage_cache_key(stage, stage_version, params, input_keys)
        if expected_key != key:
            raise ValueError(
                "cache key does not match stage_version, params, and input_keys"
            )

    @staticmethod
    def _copy_outputs(source: Path, destination: Path) -> None:
        for source_path in source.rglob("*"):
            relative_path = source_path.relative_to(source)
            if relative_path.as_posix() == _MANIFEST_NAME:
                raise ValueError(f"{_MANIFEST_NAME} is reserved for the cache manifest")
            destination_path = destination / relative_path
            if source_path.is_symlink():
                raise ValueError("cache outputs must not contain symbolic links")
            if source_path.is_dir():
                destination_path.mkdir(parents=True, exist_ok=True)
            elif source_path.is_file():
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination_path)
            else:
                raise ValueError(f"unsupported cache output: {source_path}")

    def _publish(
        self,
        stage: str,
        key: str,
        temporary: Path,
        *,
        stage_version: str | None,
        params: Mapping[str, object],
        input_keys: Sequence[str],
    ) -> Path:
        outputs: dict[str, str] = {}
        for output_path in temporary.rglob("*"):
            relative_name = output_path.relative_to(temporary).as_posix()
            if relative_name == _MANIFEST_NAME:
                raise ValueError(f"{_MANIFEST_NAME} is reserved for the cache manifest")
            if output_path.is_symlink() or not output_path.is_file():
                continue
            outputs[relative_name] = hash_file(output_path)

        manifest = {
            "stage": stage,
            "version": stage_version,
            "params": params,
            "input_keys": list(input_keys),
            "outputs": outputs,
            "created_at": datetime.now(UTC).isoformat(),
        }
        (temporary / _MANIFEST_NAME).write_bytes(_canonical_json_bytes(manifest))

        target = self._entry_path(stage, key)
        try:
            os.rename(temporary, target)
        except OSError as error:
            if not self._is_target_exists_error(error):
                raise
            return self._recover_publish(stage, key, temporary, target, error)
        return target

    def _recover_publish(
        self,
        stage: str,
        key: str,
        temporary: Path,
        target: Path,
        initial_collision: OSError,
    ) -> Path:
        """Resolve a target collision with at most two replacement attempts."""

        stale_paths: list[Path] = []
        collision = initial_collision
        try:
            for _ in range(2):
                if self.get(stage, key) is not None:
                    shutil.rmtree(temporary, ignore_errors=True)
                    return target

                stale = target.parent / f".{key}.{uuid.uuid4().hex}.stale"
                os.rename(target, stale)
                stale_paths.append(stale)
                try:
                    os.rename(temporary, target)
                except OSError as error:
                    if not self._is_target_exists_error(error):
                        raise
                    collision = error
                    continue
                return target

            if self.get(stage, key) is not None:
                shutil.rmtree(temporary, ignore_errors=True)
                return target
            raise collision
        finally:
            for stale in stale_paths:
                shutil.rmtree(stale, ignore_errors=True)

    @staticmethod
    def _is_target_exists_error(error: OSError) -> bool:
        return isinstance(error, FileExistsError) or error.errno in {
            errno.EEXIST,
            errno.ENOTEMPTY,
        }

    @staticmethod
    def _safe_output_path(target: Path, relative_name: str) -> Path | None:
        relative_path = Path(relative_name)
        if (
            relative_path.is_absolute()
            or not relative_path.parts
            or any(part in {"", ".", ".."} for part in relative_path.parts)
        ):
            return None
        return target / relative_path


__all__ = ["StageCache", "hash_file", "stage_cache_key"]

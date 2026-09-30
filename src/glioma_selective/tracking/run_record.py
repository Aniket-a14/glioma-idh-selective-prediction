"""Build and persist the Phase 06 reproducibility run record."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import subprocess
import tempfile
import threading
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

from scripts.capture_environment import capture_environment

from glioma_selective.utils import paths

__all__ = [
    "RunRecord",
    "assert_complete",
    "assert_launch_ready",
    "build_run_record",
    "generate_run_id",
    "sha256_file",
    "update_run_record",
    "validate_run_record",
    "write_run_record",
]

MANDATORY_KEYS: Final[tuple[str, ...]] = (
    "run_id",
    "timestamp_utc",
    "git_sha",
    "git_dirty",
    "dataset_manifest_hash",
    "split_manifest_hash",
    "exclusion_list_hash",
    "config",
    "seed",
    "python_version",
    "dependency_lock_hash",
    "torch_version",
    "monai_version",
    "gpu_info",
    "preprocessing_version",
    "checkpoint_hash",
    "training_history",
    "predictions_path",
    "calibration_params",
    "selective_thresholds",
    "metrics",
    "log_path",
)
LAUNCH_KEYS: Final[tuple[str, ...]] = MANDATORY_KEYS[:15]
END_KEYS: Final[tuple[str, ...]] = MANDATORY_KEYS[15:]
LIFECYCLE_KEYS: Final[tuple[str, ...]] = (
    "status",
    "end_time_utc",
    "failure_reason",
)
_ULID_ALPHABET: Final[str] = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
_ULID_LOCK = threading.Lock()
_LAST_ULID_TIME = -1
_LAST_ULID_RANDOM = -1


@dataclass(frozen=True)
class RunRecord:
    """JSON run record with protocol keys and separate lifecycle metadata."""

    run_id: str
    timestamp_utc: str
    git_sha: str
    git_dirty: bool
    dataset_manifest_hash: str
    split_manifest_hash: str
    exclusion_list_hash: str
    config: Any
    seed: int
    python_version: str
    dependency_lock_hash: str
    torch_version: str
    monai_version: str
    gpu_info: Mapping[str, str]
    preprocessing_version: Mapping[str, str]
    checkpoint_hash: Any
    training_history: Any
    predictions_path: Any
    calibration_params: Any
    selective_thresholds: Any
    metrics: Any
    log_path: Any
    status: str = "running"
    end_time_utc: str | None = None
    failure_reason: str | None = None


def _utc_now() -> str:
    """Return the current UTC instant in ISO-8601 form."""

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def generate_run_id() -> str:
    """Generate a monotonic ULID using the standard library only."""

    global _LAST_ULID_RANDOM, _LAST_ULID_TIME
    current_ms = int(time.time() * 1000)
    with _ULID_LOCK:
        if current_ms > _LAST_ULID_TIME:
            random_part = secrets.randbits(80)
            _LAST_ULID_TIME = current_ms
            _LAST_ULID_RANDOM = random_part
        else:
            current_ms = _LAST_ULID_TIME
            _LAST_ULID_RANDOM += 1
            if _LAST_ULID_RANDOM >= 1 << 80:
                current_ms += 1
                _LAST_ULID_TIME = current_ms
                _LAST_ULID_RANDOM = secrets.randbits(80)
            random_part = _LAST_ULID_RANDOM
        value = (current_ms << 80) | random_part
    encoded = ["0"] * 26
    for index in range(25, -1, -1):
        encoded[index] = _ULID_ALPHABET[value & 0x1F]
        value >>= 5
    return "".join(encoded)


def sha256_file(path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file, reading it in bounded chunks."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_value(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _split_manifest_hash() -> str:
    sidecar = paths.manifests_dir() / "splits.json.sha256"
    try:
        digest = sidecar.read_text(encoding="ascii").split()[0]
    except (OSError, IndexError) as exc:
        raise ValueError(f"could not read frozen split hash from {sidecar}") from exc
    if not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError(f"invalid SHA-256 in frozen split sidecar: {sidecar}")
    return digest.lower()


def build_run_record(
    *,
    dataset_manifest_hash: str,
    exclusion_list_hash: str,
    config: Any,
    seed: int,
    preprocessing_version: str,
    parameter_hash: str,
    normalization_stats_sha256: str,
    repo_root: str | Path | None = None,
) -> RunRecord:
    """Capture launch-time keys 1–14; final result keys remain unset."""

    root = (
        Path(repo_root).resolve()
        if repo_root is not None
        else Path(__file__).resolve().parents[3]
    )
    environment = capture_environment(root)
    dirty = bool(_git_value(root, "status", "--porcelain"))
    preprocessing = {
        "version": preprocessing_version,
        "parameter_hash": parameter_hash,
        "normalization_stats_sha256": normalization_stats_sha256,
    }
    return RunRecord(
        run_id=generate_run_id(),
        timestamp_utc=_utc_now(),
        git_sha=_git_value(root, "rev-parse", "HEAD"),
        git_dirty=dirty,
        dataset_manifest_hash=dataset_manifest_hash,
        split_manifest_hash=_split_manifest_hash(),
        exclusion_list_hash=exclusion_list_hash,
        config=config,
        seed=seed,
        python_version=environment["python"],
        dependency_lock_hash=environment["dependency_lock_hash"],
        torch_version=environment["pytorch"],
        monai_version=environment["monai"],
        gpu_info={
            "model": environment["gpu_model"],
            "vram": environment["vram"],
            "cuda_runtime": environment["cuda_runtime"],
            "driver": environment["driver"],
        },
        preprocessing_version=preprocessing,
        checkpoint_hash=None,
        training_history=None,
        predictions_path=None,
        calibration_params=None,
        selective_thresholds=None,
        metrics=None,
        log_path=None,
    )


def _record_data(record: RunRecord | Mapping[str, Any]) -> dict[str, Any]:
    return asdict(record) if isinstance(record, RunRecord) else dict(record)


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or value == {} or value == []


def validate_run_record(
    record_or_path: RunRecord | Mapping[str, Any] | str | Path,
) -> list[str]:
    """Return mandatory key names that are absent, null, or empty."""

    if isinstance(record_or_path, str | Path):
        try:
            data = json.loads(Path(record_or_path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"could not load run record {record_or_path}") from exc
    else:
        data = _record_data(record_or_path)
    if not isinstance(data, dict):
        raise ValueError("run record JSON must contain an object")
    return [key for key in MANDATORY_KEYS if key not in data or _is_missing(data[key])]


def _assert_launch_data(
    record_or_mapping: RunRecord | Mapping[str, Any],
) -> dict[str, Any]:
    data = _record_data(record_or_mapping)
    missing = [key for key in LAUNCH_KEYS if key not in data or _is_missing(data[key])]
    if missing:
        message = ", ".join(missing)
        raise ValueError(f"run record is missing launch-time fields: {message}")
    return data


def assert_launch_ready(record: RunRecord | Mapping[str, Any]) -> None:
    """Require launch keys 1–14 and a clean Git checkout."""

    data = _assert_launch_data(record)
    if not isinstance(data["git_dirty"], bool):
        raise ValueError("git_dirty must be a bool")
    if data["git_dirty"]:
        raise ValueError("Gate C requires a clean checkout with git_dirty false")


def assert_complete(record: RunRecord | Mapping[str, Any]) -> None:
    """Require all 22 protocol keys, accepting explicit not-applicable values."""

    missing = validate_run_record(record)
    if missing:
        raise ValueError(f"run record is incomplete: {', '.join(missing)}")


def _record_path(run_id: str) -> Path:
    if not _ULID_RE.fullmatch(run_id):
        raise ValueError("run_id must be a 26-character Crockford-base32 ULID")
    return paths.experiments_dir() / run_id / "record.json"


def _write_json_atomic(path: Path, data: Mapping[str, Any], *, exclusive: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    descriptor, temp_name = tempfile.mkstemp(
        prefix=".record-", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if exclusive:
            try:
                os.link(temp_path, path)
            except FileExistsError:
                raise FileExistsError(f"run record already exists: {path}") from None
            temp_path.unlink()
        else:
            os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def write_run_record(record: RunRecord, run_id: str | None = None) -> Path:
    """Write the launch record once, refusing to replace an existing record."""

    identifier = record.run_id if run_id is None else run_id
    if identifier != record.run_id:
        raise ValueError("run_id argument must match record.run_id")
    path = _record_path(identifier)
    _write_json_atomic(path, _record_data(record), exclusive=True)
    return path


def update_run_record(run_id: str, **fields: Any) -> Path:
    """Fill only end-of-run keys and lifecycle metadata in an existing record."""

    allowed = set(END_KEYS) | set(LIFECYCLE_KEYS)
    unknown = set(fields) - allowed
    if unknown:
        message = ", ".join(sorted(unknown))
        raise ValueError(f"update_run_record cannot change fields: {message}")
    if "status" in fields and fields["status"] not in {
        "running",
        "completed",
        "failed",
    }:
        raise ValueError("status must be running, completed, or failed")
    path = _record_path(run_id)
    try:
        current = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not load existing run record {path}") from exc
    if current.get("run_id") != run_id:
        raise ValueError(f"run record run_id does not match path: {path}")
    current.update(fields)
    _write_json_atomic(path, current, exclusive=False)
    return path

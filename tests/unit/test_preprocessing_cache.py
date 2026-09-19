"""Unit tests for the Phase 04 content-addressed stage cache."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from glioma_selective.preprocessing.cache import (
    StageCache,
    hash_file,
    stage_cache_key,
)


def _write_output(output_dir: Path, content: bytes = b"synthetic output") -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "volume.bin").write_bytes(content)


def _key(*, parameter: int = 1, version: str = "v1", input_key: str = "raw") -> str:
    return stage_cache_key(
        "resample",
        version,
        {"parameter": parameter},
        [input_key],
    )


def test_stage_cache_key_is_canonical_and_process_stable() -> None:
    expected = "4e1de598e12c1d2107b5d27105026feea4e0cbf2b41f4ad30fd3186fc8bb8489"
    first = stage_cache_key(
        "resample",
        "v1",
        {"tuple": ("x", "y"), "nested": [1, 2], "alpha": 0.5},
        ["upstream-key"],
    )
    second = stage_cache_key(
        "resample",
        "v1",
        {"alpha": 0.5, "nested": [1, 2], "tuple": ["x", "y"]},
        ["upstream-key"],
    )
    assert first == expected
    assert second == expected

    script = (
        "from glioma_selective.preprocessing.cache import stage_cache_key; "
        "print(stage_cache_key('resample', 'v1', "
        "{'alpha': 0.5, 'nested': [1, 2], 'tuple': ('x', 'y')}, "
        "['upstream-key']))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": str(Path(__file__).parents[2] / "src"),
        },
    )
    assert result.stdout.strip() == expected


def test_stage_cache_reuses_identical_parameters(tmp_path: Path) -> None:
    cache = StageCache(tmp_path / "processed")
    calls = 0

    def compute(output_dir: Path) -> None:
        nonlocal calls
        calls += 1
        _write_output(output_dir)

    key = _key()
    first = cache.get_or_compute(
        "resample",
        key,
        compute,
        stage_version="v1",
        params={"parameter": 1},
        input_keys=["raw"],
    )
    second = cache.get_or_compute(
        "resample",
        key,
        compute,
        stage_version="v1",
        params={"parameter": 1},
        input_keys=["raw"],
    )

    assert first == second
    assert calls == 1
    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "resample"
    assert manifest["version"] == "v1"
    assert manifest["params"] == {"parameter": 1}
    assert manifest["input_keys"] == ["raw"]
    assert manifest["outputs"] == {"volume.bin": hash_file(first / "volume.bin")}
    assert isinstance(manifest["created_at"], str)


@pytest.mark.parametrize(
    ("parameter", "version", "input_key"),
    [
        (2, "v1", "raw"),
        (1, "v2", "raw"),
        (1, "v1", "changed-raw"),
    ],
)
def test_changed_key_inputs_recompute(
    tmp_path: Path, parameter: int, version: str, input_key: str
) -> None:
    cache = StageCache(tmp_path / "processed")
    calls = 0

    def compute(output_dir: Path) -> None:
        nonlocal calls
        calls += 1
        _write_output(output_dir, str(calls).encode())

    cache.get_or_compute(
        "resample",
        _key(),
        compute,
        stage_version="v1",
        params={"parameter": 1},
        input_keys=["raw"],
    )
    changed = _key(parameter=parameter, version=version, input_key=input_key)
    result = cache.get_or_compute(
        "resample",
        changed,
        compute,
        stage_version=version,
        params={"parameter": parameter},
        input_keys=[input_key],
    )

    assert result.is_dir()
    assert calls == 2


def test_failed_compute_leaves_no_entry_and_next_call_recomputes(
    tmp_path: Path,
) -> None:
    cache = StageCache(tmp_path / "processed")
    key = _key()
    calls = 0

    def crash(output_dir: Path) -> None:
        nonlocal calls
        calls += 1
        _write_output(output_dir)
        raise RuntimeError("synthetic interruption")

    with pytest.raises(RuntimeError, match="synthetic interruption"):
        cache.get_or_compute("resample", key, crash)
    assert cache.get("resample", key) is None

    result = cache.get_or_compute(
        "resample", key, lambda output_dir: _write_output(output_dir)
    )
    assert result.is_dir()
    assert calls == 1
    assert not list(result.parent.glob(f".{key}.*.tmp"))


def test_corrupt_or_deleted_output_is_a_miss(tmp_path: Path) -> None:
    cache = StageCache(tmp_path / "processed")
    key = _key()
    result = cache.get_or_compute(
        "resample", key, lambda output_dir: _write_output(output_dir)
    )
    output = result / "volume.bin"
    output.write_bytes(b"corrupted")
    assert cache.get("resample", key) is None

    output.unlink()
    assert cache.get("resample", key) is None


def test_invalid_json_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="non-finite float"):
        stage_cache_key("resample", "v1", {"threshold": float("nan")}, [])
    with pytest.raises(TypeError, match="not JSON-serialisable"):
        stage_cache_key("resample", "v1", {"value": {1, 2}}, [])


def test_hash_file_matches_hashlib_for_multiple_chunks(tmp_path: Path) -> None:
    path = tmp_path / "multi-chunk.bin"
    content = (bytes(range(256)) * (2 * 1024 * 1024 // 256 + 1))[
        : 2 * 1024 * 1024 + 123
    ]
    path.write_bytes(content)

    assert hash_file(path) == hashlib.sha256(content).hexdigest()


def test_put_copies_outputs_into_content_addressed_layout(tmp_path: Path) -> None:
    cache_root = tmp_path / "processed"
    source = tmp_path / "source"
    _write_output(source)
    cache = StageCache(cache_root)
    key = _key()

    result = cache.put("resample", key, source)

    assert result == cache_root / "resample" / key[:2] / key
    assert cache.get("resample", key) == result

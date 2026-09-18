"""Unit tests for the Phase 01 environment fingerprint script."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from scripts import capture_environment


def _patch_non_probe_fields(
    monkeypatch: pytest.MonkeyPatch, *, git_sha: str = "abc123"
) -> None:
    """Make tests independent of the host's installed hardware and packages."""

    monkeypatch.setattr(
        capture_environment,
        "_capture_nvidia_smi",
        lambda: capture_environment._absent_gpu_fields("test host"),
    )
    monkeypatch.setattr(
        capture_environment,
        "_capture_torch_info",
        lambda: {
            "pytorch": capture_environment.NOT_INSTALLED,
            "monai": capture_environment.NOT_INSTALLED,
            "cuda_runtime": f"{capture_environment.NOT_AVAILABLE} (test host)",
            "torch_cuda_capability": (
                f"{capture_environment.NOT_AVAILABLE} (test host)"
            ),
        },
    )
    monkeypatch.setattr(
        capture_environment,
        "_run_command",
        lambda command, cwd=None: git_sha,
    )


def test_capture_has_exactly_fourteen_fields_and_explicit_absence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_non_probe_fields(monkeypatch)

    fingerprint = capture_environment.capture_environment(tmp_path)

    assert tuple(fingerprint) == capture_environment.REQUIRED_FIELDS
    assert len(fingerprint) == 14
    assert fingerprint["gpu_model"] == "not available (test host)"
    assert fingerprint["pytorch"] == "not installed"
    assert fingerprint["monai"] == "not installed"
    assert fingerprint["dependency_lock_hash"] == "not yet generated"


def test_capture_reports_sha256_when_lock_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_non_probe_fields(monkeypatch)
    lock_path = tmp_path / "requirements.lock.txt"
    lock_contents = b"# generated lock\npackage==1.2.3\n"
    lock_path.write_bytes(lock_contents)

    fingerprint = capture_environment.capture_environment(tmp_path)

    assert (
        fingerprint["dependency_lock_hash"] == hashlib.sha256(lock_contents).hexdigest()
    )


def test_nvidia_probe_is_non_fatal_when_executable_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(capture_environment.shutil, "which", lambda name: None)

    fields = capture_environment._capture_nvidia_smi()

    assert fields == {
        "nvidia_smi": "not available (nvidia-smi was not found)",
        "gpu_model": "not available (nvidia-smi was not found)",
        "vram": "not available (nvidia-smi was not found)",
        "cuda_runtime": "not available (nvidia-smi was not found)",
        "driver": "not available (nvidia-smi was not found)",
    }


def test_nvidia_probe_parses_all_gpu_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        capture_environment.shutil, "which", lambda name: "/usr/bin/nvidia-smi"
    )

    def fake_run(command: tuple[str, ...], *, cwd: Path | None = None) -> str:
        if len(command) == 1:
            return "CUDA Version: 12.4\nDriver Version: 550.54.14"
        return "RTX A5000, 24576, 550.54.14\nRTX 4090, 24564, 550.54.14"

    monkeypatch.setattr(capture_environment, "_run_command", fake_run)

    fields = capture_environment._capture_nvidia_smi()

    assert fields["gpu_model"] == "RTX A5000; RTX 4090"
    assert fields["vram"] == "24576 MiB; 24564 MiB"
    assert fields["driver"] == "550.54.14; 550.54.14"
    assert fields["cuda_runtime"] == "12.4"


def test_cuda_runtime_preserves_driver_and_pytorch_versions() -> None:
    combined = capture_environment._combine_cuda_runtime("12.4", "12.1")

    assert combined == "12.4 (nvidia-smi); 12.1 (PyTorch build)"

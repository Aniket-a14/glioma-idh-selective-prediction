#!/usr/bin/env python3
"""Capture the reproducibility fingerprint for the current checkout.

The output is a JSON object with the fourteen fields required by Phase 01
T01.3.  Hardware probes are deliberately best-effort on CPU-only machines:
GPU-related fields contain an explicit ``not available`` state when no
``nvidia-smi`` executable or CUDA device is present.  The dependency lock is
the repository-root ``requirements.lock.txt``; until T01.5 generates it, its
field is explicitly ``not yet generated``.

Examples:
    python scripts/capture_environment.py
    python scripts/capture_environment.py --output environment.json
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

NOT_AVAILABLE: Final = "not available"
NOT_INSTALLED: Final = "not installed"
LOCK_NOT_GENERATED: Final = "not yet generated"

REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "nvidia_smi",
    "gpu_model",
    "vram",
    "cuda_runtime",
    "driver",
    "cpu",
    "ram",
    "free_disk",
    "python",
    "pytorch",
    "monai",
    "torch_cuda_capability",
    "git_sha",
    "dependency_lock_hash",
)


class EnvironmentCaptureError(RuntimeError):
    """Raised when a required environment fingerprint probe cannot run."""


def _run_command(command: Sequence[str], *, cwd: Path | None = None) -> str:
    """Run *command* and return trimmed stdout, raising on command failure."""

    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise EnvironmentCaptureError(
            f"could not run {' '.join(command)!r}: {exc}"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise EnvironmentCaptureError(
            f"command {' '.join(command)!r} failed with exit code "
            f"{completed.returncode}: {detail}"
        )
    return completed.stdout.strip()


def _repository_root() -> Path:
    """Return the checkout root containing this script."""

    return Path(__file__).resolve().parents[1]


def _format_bytes(value: int) -> str:
    """Format a byte count with an exact byte value and binary-unit value."""

    gibibytes = value / (1024**3)
    return f"{value} bytes ({gibibytes:.2f} GiB)"


def _absent_gpu_fields(reason: str) -> dict[str, str]:
    """Return explicit values for all fields unavailable without an NVIDIA GPU."""

    unavailable = f"{NOT_AVAILABLE} ({reason})"
    return {
        "nvidia_smi": unavailable,
        "gpu_model": unavailable,
        "vram": unavailable,
        "cuda_runtime": unavailable,
        "driver": unavailable,
    }


def _capture_nvidia_smi() -> dict[str, str]:
    """Capture NVIDIA hardware fields, or explicit absence on CPU-only hosts."""

    executable = shutil.which("nvidia-smi")
    if executable is None:
        return _absent_gpu_fields("nvidia-smi was not found")

    full_output = _run_command((executable,))
    query_output = _run_command(
        (
            executable,
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        )
    )
    rows = [line.strip() for line in query_output.splitlines() if line.strip()]
    if not rows:
        raise EnvironmentCaptureError(
            "nvidia-smi returned no GPU rows for the hardware query"
        )

    models: list[str] = []
    memory: list[str] = []
    drivers: list[str] = []
    for row in rows:
        columns = [column.strip() for column in row.split(",")]
        if len(columns) != 3:
            raise EnvironmentCaptureError(
                f"nvidia-smi hardware query returned an unexpected row: {row!r}"
            )
        model, memory_mib, driver = columns
        models.append(model)
        memory.append(f"{memory_mib} MiB")
        drivers.append(driver)

    cuda_match = re.search(r"CUDA Version:\s*([^\s|]+)", full_output)
    cuda_runtime = (
        cuda_match.group(1)
        if cuda_match
        else f"{NOT_AVAILABLE} (nvidia-smi did not report a CUDA version)"
    )
    return {
        "nvidia_smi": full_output,
        "gpu_model": "; ".join(models),
        "vram": "; ".join(memory),
        "cuda_runtime": cuda_runtime,
        "driver": "; ".join(drivers),
    }


def _package_version(distribution: str) -> str:
    """Return an installed distribution version or an explicit absence state."""

    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return NOT_INSTALLED


def _capture_torch_info() -> dict[str, str]:
    """Capture PyTorch, MONAI, CUDA runtime, and capability fields."""

    pytorch_version = _package_version("torch")
    monai_version = _package_version("monai")
    if pytorch_version == NOT_INSTALLED:
        return {
            "pytorch": NOT_INSTALLED,
            "monai": monai_version,
            "cuda_runtime": f"{NOT_AVAILABLE} (PyTorch is not installed)",
            "torch_cuda_capability": (f"{NOT_AVAILABLE} (PyTorch is not installed)"),
        }

    try:
        import torch
    except ImportError as exc:
        raise EnvironmentCaptureError(
            f"PyTorch distribution {pytorch_version} is installed but cannot be "
            f"imported: {exc}"
        ) from exc

    torch_cuda_version = torch.version.cuda
    if torch_cuda_version is None:
        cuda_runtime = f"{NOT_AVAILABLE} (PyTorch was built without CUDA)"
    else:
        cuda_runtime = str(torch_cuda_version)

    if not torch.cuda.is_available():
        capability = f"{NOT_AVAILABLE} (torch.cuda.is_available() is False)"
    else:
        major, minor = torch.cuda.get_device_capability()
        capability = f"{major}.{minor}"

    return {
        "pytorch": pytorch_version,
        "monai": monai_version,
        "cuda_runtime": cuda_runtime,
        "torch_cuda_capability": capability,
    }


def _combine_cuda_runtime(nvidia_runtime: str, torch_runtime: str) -> str:
    """Keep both the driver probe and PyTorch's CUDA build information."""

    nvidia_available = not nvidia_runtime.startswith(NOT_AVAILABLE)
    torch_available = not torch_runtime.startswith(NOT_AVAILABLE)
    if nvidia_available and torch_available:
        return f"{nvidia_runtime} (nvidia-smi); {torch_runtime} (PyTorch build)"
    if nvidia_available:
        return nvidia_runtime
    return torch_runtime


def _capture_cpu() -> str:
    """Capture a human-readable CPU model on macOS, Linux, or fallback hosts."""

    if sys.platform == "darwin":
        try:
            result = _run_command(("sysctl", "-n", "machdep.cpu.brand_string"))
        except EnvironmentCaptureError:
            result = ""
    elif Path("/proc/cpuinfo").is_file():
        result = ""
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                result = line.split(":", 1)[1].strip()
                break
    else:
        result = ""

    return result or platform.processor() or platform.machine() or NOT_AVAILABLE


def _capture_ram() -> str:
    """Capture total physical RAM with platform-native fallbacks."""

    if sys.platform == "darwin":
        try:
            return _format_bytes(int(_run_command(("sysctl", "-n", "hw.memsize"))))
        except (EnvironmentCaptureError, ValueError):
            pass

    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                kibibytes = int(line.split()[1])
                return _format_bytes(kibibytes * 1024)

    return f"{NOT_AVAILABLE} (total physical RAM could not be detected)"


def _capture_free_disk(repo_root: Path) -> str:
    """Capture free space on the filesystem containing the repository."""

    try:
        free_bytes = shutil.disk_usage(repo_root).free
    except OSError as exc:
        raise EnvironmentCaptureError(
            f"could not determine free disk space for {repo_root}: {exc}"
        ) from exc
    return f"{_format_bytes(free_bytes)} on {repo_root}"


def _sha256(path: Path) -> str:
    """Hash *path* in bounded-size chunks."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _capture_lock_hash(repo_root: Path) -> str:
    """Return the lock hash or the explicit pre-T01.5 absence state."""

    lock_path = repo_root / "requirements.lock.txt"
    if not lock_path.exists():
        return LOCK_NOT_GENERATED
    if not lock_path.is_file():
        raise EnvironmentCaptureError(
            f"dependency lock path exists but is not a file: {lock_path}"
        )
    return _sha256(lock_path)


def capture_environment(repo_root: Path | None = None) -> dict[str, str]:
    """Return the fourteen-field environment fingerprint for *repo_root*."""

    root = (repo_root or _repository_root()).resolve()
    nvidia_fields = _capture_nvidia_smi()
    torch_fields = _capture_torch_info()
    fingerprint = {
        **nvidia_fields,
        "cpu": _capture_cpu(),
        "ram": _capture_ram(),
        "free_disk": _capture_free_disk(root),
        "python": sys.version.splitlines()[0],
        "pytorch": torch_fields["pytorch"],
        "monai": torch_fields["monai"],
        "torch_cuda_capability": torch_fields["torch_cuda_capability"],
        "git_sha": _run_command(("git", "rev-parse", "HEAD"), cwd=root),
        "dependency_lock_hash": _capture_lock_hash(root),
    }
    fingerprint["cuda_runtime"] = _combine_cuda_runtime(
        nvidia_fields["cuda_runtime"], torch_fields["cuda_runtime"]
    )

    missing_fields = set(REQUIRED_FIELDS) - fingerprint.keys()
    unexpected_fields = fingerprint.keys() - set(REQUIRED_FIELDS)
    if missing_fields or unexpected_fields:
        raise EnvironmentCaptureError(
            "fingerprint schema mismatch: "
            f"missing={sorted(missing_fields)}, "
            f"unexpected={sorted(unexpected_fields)}"
        )
    return fingerprint


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and optionally write the JSON fingerprint to a file."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="also write the JSON fingerprint to this path",
    )
    args = parser.parse_args(argv)

    try:
        fingerprint = capture_environment()
        rendered = json.dumps(fingerprint, indent=2, sort_keys=True)
        if args.output is not None:
            args.output.write_text(rendered + "\n", encoding="utf-8")
    except (EnvironmentCaptureError, OSError) as exc:
        print(f"capture_environment.py: error: {exc}", file=sys.stderr)
        return 1

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

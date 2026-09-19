"""Thin command wrapper for the pinned HD-BET release.

The wrapper is intentionally untested against the real HD-BET binary until
the first real use; that is expected because inference downloads model
weights and is too heavy for unit tests.
"""

from __future__ import annotations

import importlib.metadata
import subprocess
from os import PathLike
from pathlib import Path

PINNED_HD_BET_VERSION = "2.0.1"
_VALID_DEVICES = frozenset({"cuda", "cpu", "mps"})


def assert_pinned_version() -> None:
    """Raise if the installed HD-BET distribution is not the pinned release."""

    try:
        installed = importlib.metadata.version("hd-bet")
    except importlib.metadata.PackageNotFoundError as error:
        raise RuntimeError("HD-BET is not installed") from error
    if installed != PINNED_HD_BET_VERSION:
        raise RuntimeError(
            f"HD-BET version {installed!r} is installed; "
            f"expected {PINNED_HD_BET_VERSION!r}"
        )


def build_hd_bet_command(
    input_path: str | PathLike[str],
    output_path: str | PathLike[str],
    *,
    device: str,
    disable_tta: bool,
    save_mask: bool,
) -> list[str]:
    """Build an argv list for HD-BET without invoking a shell."""

    if device not in _VALID_DEVICES:
        raise ValueError(f"unsupported HD-BET device: {device!r}")
    command = [
        "hd-bet",
        "-i",
        str(input_path),
        "-o",
        str(output_path),
        "-device",
        device,
    ]
    if disable_tta:
        command.append("--disable_tta")
    if save_mask:
        command.append("--save_bet_mask")
    command.append("--no_bet_image")
    return command


def run_hd_bet(
    input_path: str | PathLike[str],
    output_path: str | PathLike[str],
    *,
    device: str = "cpu",
    disable_tta: bool = True,
    save_mask: bool = False,
) -> Path:
    """Run pinned HD-BET and return the required output path.

    Real-binary behavior is untested until first use because HD-BET downloads
    model weights; this is expected and inference is never run by unit tests.
    """

    assert_pinned_version()
    output = Path(output_path)
    command = build_hd_bet_command(
        input_path,
        output,
        device=device,
        disable_tta=disable_tta,
        save_mask=save_mask,
    )
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("HD-BET failed while processing the input volume") from error
    if not output.is_file():
        raise RuntimeError(f"HD-BET completed but output is missing: {output}")
    return output

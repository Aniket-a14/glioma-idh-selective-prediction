"""Thin command wrapper for the pinned HD-BET release.

The wrapper is intentionally untested against the real HD-BET binary until
the first real use; that is expected because inference downloads model
weights and is too heavy for unit tests.
"""

from __future__ import annotations

import importlib.metadata
import subprocess
from dataclasses import dataclass
from os import PathLike
from pathlib import Path

PINNED_HD_BET_VERSION = "2.0.1"
_VALID_DEVICES = frozenset({"cuda", "cpu", "mps"})


@dataclass(frozen=True)
class HdBetResult:
    """Paths produced by one HD-BET invocation."""

    image_path: Path | None
    mask_path: Path | None


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
    save_image: bool,
) -> list[str]:
    """Build an argv list for HD-BET without invoking a shell."""

    _validate_nifti_path(input_path, "input")
    _validate_nifti_path(output_path, "output")
    if not save_image and not save_mask:
        raise ValueError("HD-BET must request an image or a mask")
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
    if not save_image:
        command.append("--no_bet_image")
    return command


def hd_bet_mask_path(output_path: str | PathLike[str]) -> Path:
    """Return the mask path HD-BET derives from a single-file output path."""

    output = _validate_nifti_path(output_path, "output")
    return output.with_name(f"{output.name[:-7]}_bet.nii.gz")


def run_hd_bet(
    input_path: str | PathLike[str],
    output_path: str | PathLike[str],
    *,
    device: str = "cpu",
    disable_tta: bool = True,
    save_mask: bool = False,
    save_image: bool = True,
) -> HdBetResult:
    """Run pinned HD-BET and return the required output path.

    Real-binary behavior is untested until first use because HD-BET downloads
    model weights; this is expected and inference is never run by unit tests.
    """

    input = _validate_nifti_path(input_path, "input")
    output = Path(output_path)
    _validate_nifti_path(output, "output")
    if not input.is_file():
        raise FileNotFoundError(f"HD-BET input does not exist: {input}")
    assert_pinned_version()
    command = build_hd_bet_command(
        input_path,
        output,
        device=device,
        disable_tta=disable_tta,
        save_mask=save_mask,
        save_image=save_image,
    )
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("HD-BET failed while processing the input volume") from error

    image = output if save_image else None
    mask = hd_bet_mask_path(output) if save_mask else None
    requested_outputs = (("image", image), ("mask", mask))
    for name, path in requested_outputs:
        if path is not None and not path.is_file():
            raise RuntimeError(
                f"HD-BET completed but requested {name} is missing: {path}"
            )
    return HdBetResult(image_path=image, mask_path=mask)


def _validate_nifti_path(path: str | PathLike[str], label: str) -> Path:
    resolved = Path(path)
    if not str(resolved).endswith(".nii.gz"):
        raise ValueError(f"HD-BET {label} path must end with .nii.gz: {resolved}")
    return resolved

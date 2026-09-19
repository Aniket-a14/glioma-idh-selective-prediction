"""Unit tests for the HD-BET command wrapper."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from glioma_selective.preprocessing import skullstrip


def test_hd_bet_pin_matches_project_dependency() -> None:
    dependency = next(
        line.strip().strip('",')
        for line in Path("pyproject.toml").read_text(encoding="utf-8").splitlines()
        if line.strip().startswith('"hd-bet==')
    )

    assert dependency == f"hd-bet=={skullstrip.PINNED_HD_BET_VERSION}"


def test_build_hd_bet_command_passes_required_flags() -> None:
    command = skullstrip.build_hd_bet_command(
        "input.nii.gz",
        "output.nii.gz",
        device="cpu",
        disable_tta=True,
        save_mask=True,
    )

    assert command == [
        "hd-bet",
        "-i",
        "input.nii.gz",
        "-o",
        "output.nii.gz",
        "-device",
        "cpu",
        "--disable_tta",
        "--save_bet_mask",
        "--no_bet_image",
    ]


def test_build_hd_bet_rejects_unknown_device() -> None:
    with pytest.raises(ValueError, match="unsupported HD-BET device"):
        skullstrip.build_hd_bet_command(
            "input.nii.gz",
            "output.nii.gz",
            device="tpu",
            disable_tta=True,
            save_mask=False,
        )


def test_run_hd_bet_uses_argv_and_requires_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = tmp_path / "brain.nii.gz"
    calls: list[tuple[list[str], bool]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        calls.append((command, check))
        output.touch()

    monkeypatch.setattr(skullstrip.subprocess, "run", fake_run)
    result = skullstrip.run_hd_bet("input.nii.gz", output)

    assert result == output
    assert calls == [
        (
            [
                "hd-bet",
                "-i",
                "input.nii.gz",
                "-o",
                str(output),
                "-device",
                "cpu",
                "--disable_tta",
                "--no_bet_image",
            ],
            True,
        )
    ]


def test_run_hd_bet_reports_process_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], *, check: bool) -> None:
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(skullstrip.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="HD-BET failed"):
        skullstrip.run_hd_bet("input.nii.gz", "missing.nii.gz")


def test_run_hd_bet_reports_missing_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(skullstrip.subprocess, "run", lambda command, check: None)

    with pytest.raises(RuntimeError, match="output is missing"):
        skullstrip.run_hd_bet("input.nii.gz", tmp_path / "missing.nii.gz")

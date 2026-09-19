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
        save_image=True,
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
    ]


def test_hd_bet_mask_path() -> None:
    assert skullstrip.hd_bet_mask_path("nested/brain.nii.gz") == Path(
        "nested/brain_bet.nii.gz"
    )


def test_build_hd_bet_rejects_unknown_device() -> None:
    with pytest.raises(ValueError, match="unsupported HD-BET device"):
        skullstrip.build_hd_bet_command(
            "input.nii.gz",
            "output.nii.gz",
            device="tpu",
            disable_tta=True,
            save_mask=False,
            save_image=True,
        )


def test_build_hd_bet_rejects_requesting_neither_output() -> None:
    with pytest.raises(ValueError, match="must request an image or a mask"):
        skullstrip.build_hd_bet_command(
            "input.nii.gz",
            "output.nii.gz",
            device="cpu",
            disable_tta=True,
            save_mask=False,
            save_image=False,
        )


def test_build_hd_bet_rejects_non_nifti_paths() -> None:
    with pytest.raises(ValueError, match="input path must end with .nii.gz"):
        skullstrip.build_hd_bet_command(
            "input.nii",
            "output.nii.gz",
            device="cpu",
            disable_tta=True,
            save_mask=False,
            save_image=True,
        )

    with pytest.raises(ValueError, match="output path must end with .nii.gz"):
        skullstrip.build_hd_bet_command(
            "input.nii.gz",
            "output.nii",
            device="cpu",
            disable_tta=True,
            save_mask=False,
            save_image=True,
        )


def test_run_hd_bet_default_requests_image_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.nii.gz"
    output = tmp_path / "brain.nii.gz"
    input_path.touch()
    calls: list[tuple[list[str], bool]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        calls.append((command, check))
        output.touch()

    monkeypatch.setattr(skullstrip.subprocess, "run", fake_run)
    result = skullstrip.run_hd_bet(input_path, output)

    assert result == skullstrip.HdBetResult(image_path=output, mask_path=None)
    command = calls[0][0]
    assert "--no_bet_image" not in command
    assert "--save_bet_mask" not in command
    assert calls[0][1] is True


def test_run_hd_bet_save_mask_requests_image_and_mask(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.nii.gz"
    output = tmp_path / "brain.nii.gz"
    mask = skullstrip.hd_bet_mask_path(output)
    input_path.touch()

    captured: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        captured.append(command)
        if "--no_bet_image" not in command:
            output.touch()
        if "--save_bet_mask" in command:
            mask.touch()

    monkeypatch.setattr(skullstrip.subprocess, "run", fake_run)
    result = skullstrip.run_hd_bet(input_path, output, save_mask=True)

    assert result == skullstrip.HdBetResult(image_path=output, mask_path=mask)
    command = captured[0]
    assert "--save_bet_mask" in command
    assert "--no_bet_image" not in command


def test_run_hd_bet_mask_only_requests_only_mask(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.nii.gz"
    output = tmp_path / "brain.nii.gz"
    mask = skullstrip.hd_bet_mask_path(output)
    input_path.touch()
    calls: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        calls.append(command)
        mask.touch()

    monkeypatch.setattr(skullstrip.subprocess, "run", fake_run)
    result = skullstrip.run_hd_bet(input_path, output, save_image=False, save_mask=True)

    assert result == skullstrip.HdBetResult(image_path=None, mask_path=mask)
    assert "--no_bet_image" in calls[0]
    assert "--save_bet_mask" in calls[0]
    assert not output.exists()


def test_run_hd_bet_rejects_missing_input(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="input does not exist"):
        skullstrip.run_hd_bet(tmp_path / "missing.nii.gz", tmp_path / "output.nii.gz")


def test_run_hd_bet_rejects_non_nifti_paths(tmp_path: Path) -> None:
    input_path = tmp_path / "input.nii.gz"
    input_path.touch()
    with pytest.raises(ValueError, match="output path must end with .nii.gz"):
        skullstrip.run_hd_bet(input_path, tmp_path / "output.nii")


def test_run_hd_bet_reports_each_requested_missing_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.nii.gz"
    output = tmp_path / "brain.nii.gz"
    input_path.touch()
    monkeypatch.setattr(skullstrip.subprocess, "run", lambda command, check: None)

    with pytest.raises(RuntimeError, match="requested image is missing"):
        skullstrip.run_hd_bet(input_path, output)

    with pytest.raises(RuntimeError, match="requested mask is missing"):
        skullstrip.run_hd_bet(input_path, output, save_image=False, save_mask=True)


def test_hd_bet_commands_are_string_argv_with_explicit_device(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    input_path = tmp_path / "input.nii.gz"
    output = tmp_path / "brain.nii.gz"
    input_path.touch()
    captured: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> None:
        captured.append(command)
        output.touch()

    monkeypatch.setattr(skullstrip.subprocess, "run", fake_run)
    skullstrip.run_hd_bet(input_path, output, device="mps", disable_tta=False)

    command = captured[0]
    assert command[0] == "hd-bet"
    assert all(isinstance(argument, str) for argument in command)
    device_index = command.index("-device")
    assert command[device_index + 1] == "mps"


def test_run_hd_bet_reports_process_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(command: list[str], *, check: bool) -> None:
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(skullstrip.subprocess, "run", fake_run)

    input_path = tmp_path / "input.nii.gz"
    input_path.touch()
    with pytest.raises(RuntimeError, match="HD-BET failed"):
        skullstrip.run_hd_bet(input_path, tmp_path / "missing.nii.gz")

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from scripts import check_setup as setup


def runner_for(values: dict[tuple[str, ...], tuple[int, str]]):
    def run(args):
        return values.get(tuple(args), (1, ""))

    return run


def project(tmp_path: Path, requirement: str = ">=3.12") -> Path:
    (tmp_path / "pyproject.toml").write_text(
        f"[project]\nname = 'test'\nrequires-python = '{requirement}'\n",
        encoding="utf-8",
    )
    return tmp_path


def git_repo(tmp_path: Path) -> Path:
    subprocess.run(
        ["git", "init", str(tmp_path)], check=True, capture_output=True, text=True
    )
    return tmp_path


def test_python_version_pass_and_fail(tmp_path):
    repo = project(tmp_path)
    assert setup.check_python_version(repo, (3, 12)).status == "PASS"
    assert setup.check_python_version(repo, (3, 11)).status == "FAIL"


def test_virtualenv_pass_and_warn():
    assert setup.check_virtualenv("venv", "base").status == "PASS"
    assert setup.check_virtualenv("same", "same").status == "WARN"


def test_package_import_pass_and_fail(tmp_path):
    repo = project(tmp_path)
    module_file = repo / "src" / "glioma_selective" / "__init__.py"
    module_file.parent.mkdir(parents=True)
    module_file.write_text("", encoding="utf-8")

    def importer(_):
        return type("Module", (), {"__file__": str(module_file)})()

    assert setup.check_package_import(repo, importer).status == "PASS"
    assert (
        setup.check_package_import(
            repo, lambda _: (_ for _ in ()).throw(ImportError())
        ).status
        == "FAIL"
    )


def test_git_pass_warn_and_fail(tmp_path):
    good = runner_for(
        {
            ("git", "--version"): (0, "git version"),
            ("git", "config", "--get", "user.name"): (0, "Contributor"),
            ("git", "config", "--get", "user.email"): (0, "contributor@example.com"),
        }
    )
    identity_missing = runner_for(
        {
            ("git", "--version"): (0, "git version"),
            ("git", "config", "--get", "user.name"): (1, ""),
            ("git", "config", "--get", "user.email"): (0, ""),
        }
    )
    unavailable = runner_for({})
    assert setup.check_git(tmp_path, good).status == "PASS"
    assert setup.check_git_identity(good).status == "PASS"
    assert setup.check_git(tmp_path, identity_missing).status == "PASS"
    assert setup.check_git_identity(identity_missing).status == "WARN"
    assert setup.check_git(tmp_path, unavailable).status == "FAIL"


def test_git_hooks_worktree_path_and_missing(tmp_path):
    repo = git_repo(tmp_path)
    hooks = Path(
        subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    if not hooks.is_absolute():
        hooks = repo / hooks
    hooks.mkdir(parents=True, exist_ok=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\n", encoding="utf-8")
    run = setup._runner_for(repo)
    assert setup.check_git_hooks(repo, run).status == "PASS"
    (hooks / "pre-commit").unlink()
    assert setup.check_git_hooks(repo, run).status == "WARN"


def test_precommit_and_gh_statuses(monkeypatch, tmp_path):
    monkeypatch.setattr(
        setup.shutil,
        "which",
        lambda name: "/bin/tool" if name in {"pre-commit", "gh"} else None,
    )
    assert setup.check_precommit_tool().status == "PASS"
    assert (
        setup.check_gh_auth(runner_for({("gh", "auth", "status"): (0, "ok")})).status
        == "PASS"
    )
    assert (
        setup.check_gh_auth(runner_for({("gh", "auth", "status"): (1, "")})).status
        == "WARN"
    )
    monkeypatch.setattr(setup.shutil, "which", lambda _: None)
    assert setup.check_precommit_tool().status == "WARN"
    assert setup.check_gh_auth(runner_for({})).status == "WARN"


def test_env_file_info_pass_and_fail(tmp_path):
    repo = project(tmp_path)
    missing = runner_for({("git", "ls-files", "--error-unmatch", ".env"): (1, "")})
    assert setup.check_env_file(repo, missing).status == "INFO"
    (repo / ".env").write_text("SECRET=hidden\n", encoding="utf-8")
    assert setup.check_env_file(repo, missing).status == "PASS"
    tracked = runner_for({("git", "ls-files", "--error-unmatch", ".env"): (0, ".env")})
    assert setup.check_env_file(repo, tracked).status == "FAIL"


def test_external_flag_process_and_dotenv_values(tmp_path):
    repo = project(tmp_path)
    assert setup.check_external_eval_flag(repo, {}).status == "PASS"
    assert "unset" in setup.check_external_eval_flag(repo, {}).message
    assert (
        setup.check_external_eval_flag(repo, {setup.EXTERNAL_EVAL_FLAG: "0"}).status
        == "PASS"
    )
    assert (
        setup.check_external_eval_flag(repo, {setup.EXTERNAL_EVAL_FLAG: "1"}).status
        == "FAIL"
    )
    (repo / ".env").write_text(f"{setup.EXTERNAL_EVAL_FLAG}=0\n", encoding="utf-8")
    assert setup.check_external_eval_flag(repo, {}).status == "PASS"
    (repo / ".env").write_text(f"{setup.EXTERNAL_EVAL_FLAG}=yes\n", encoding="utf-8")
    assert setup.check_external_eval_flag(repo, {}).status == "FAIL"
    (repo / ".env").write_text(
        f"export {setup.EXTERNAL_EVAL_FLAG}=0\n", encoding="utf-8"
    )
    assert setup.check_external_eval_flag(repo, {}).status == "PASS"
    (repo / ".env").write_text(
        f"{setup.EXTERNAL_EVAL_FLAG}=0\n{setup.EXTERNAL_EVAL_FLAG}=1\n",
        encoding="utf-8",
    )
    assert setup.check_external_eval_flag(repo, {}).status == "FAIL"
    (repo / ".env").write_text(
        f"{setup.EXTERNAL_EVAL_FLAG}=1\n{setup.EXTERNAL_EVAL_FLAG}=0\n",
        encoding="utf-8",
    )
    assert setup.check_external_eval_flag(repo, {}).status == "FAIL"


def test_wsl_info_and_warn(tmp_path):
    assert setup.check_wsl(tmp_path, "Linux version 6.0").message == "not WSL"
    assert (
        setup.check_wsl(Path("/home/user/repo"), "Microsoft kernel").message
        == "WSL (version not determined)"
    )
    assert setup.check_wsl(Path("/home/user/repo"), "Microsoft WSL2").message == "WSL2"
    wsl_repo = Path(os.sep) / "mnt" / "c" / "repo"
    assert setup.check_wsl(wsl_repo, "Microsoft WSL2").status == "WARN"


def test_line_endings_info_and_warn(tmp_path):
    repo = project(tmp_path)
    (repo / "README.md").write_bytes(b"title\r\n")
    run = runner_for(
        {
            ("git", "config", "--get", "core.autocrlf"): (0, "true"),
            ("git", "config", "--get", "core.eol"): (1, ""),
            (
                "git",
                "ls-files",
                "-z",
                "--",
                "*.md",
                "*.py",
                "*.toml",
                "*.yaml",
                ":(exclude)data/**",
                ":(exclude)artifacts/**",
            ): (0, "README.md\0"),
        }
    )
    assert setup.check_line_endings(repo, run).status == "WARN"
    (repo / "README.md").write_bytes(b"title\n")
    assert setup.check_line_endings(repo, run).status == "INFO"


def test_storage_root_never_exposes_path(tmp_path):
    existing = tmp_path / "storage"
    existing.mkdir()
    result = setup.check_storage_root(tmp_path, {setup.STORAGE_ROOT: str(existing)})
    assert result.status == "INFO"
    assert "set, exists" in result.message
    assert str(existing) not in result.message
    assert "unset" in setup.check_storage_root(tmp_path, {}).message


def test_branch_info_and_main_warning():
    clean = runner_for(
        {
            ("git", "branch", "--show-current"): (0, "feature"),
            ("git", "status", "--porcelain", "--untracked-files=no"): (0, ""),
        }
    )
    dirty_main = runner_for(
        {
            ("git", "branch", "--show-current"): (0, "main"),
            ("git", "status", "--porcelain", "--untracked-files=no"): (0, " M file.py"),
        }
    )
    assert setup.check_branch(clean).status == "INFO"
    assert setup.check_branch(dirty_main).status == "WARN"


def test_json_output_contains_all_checks_and_exit_codes(monkeypatch, capsys, tmp_path):
    checks = [setup.Check("example", "PASS", "ok")]
    monkeypatch.setattr(setup, "collect_checks", lambda _: checks)
    assert setup.main(["--repo", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["checks"][0]["name"] == "example"
    assert payload["summary"]["PASS"] == 1

    monkeypatch.setattr(
        setup, "collect_checks", lambda _: [setup.Check("example", "FAIL", "bad")]
    )
    assert setup.main(["--repo", str(tmp_path)]) == 1
    assert "FAIL  example" in capsys.readouterr().out
    assert setup.main(["--repo", str(tmp_path / "missing")]) == 2


def test_argument_errors_return_two():
    with pytest.raises(SystemExit) as error:
        setup.main(["--unknown"])
    assert error.value.code == 2

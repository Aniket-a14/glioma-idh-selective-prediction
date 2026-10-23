"""Read-only checks for a local contributor setup."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

Status = Literal["PASS", "WARN", "FAIL", "INFO"]
Runner = Callable[[Sequence[str]], tuple[int, str]]
EXTERNAL_EVAL_FLAG = "GLIOMA_EXTERNAL_EVAL_AUTHORIZED"
STORAGE_ROOT = "GLIOMA_STORAGE_ROOT"


@dataclass(frozen=True)
class Check:
    name: str
    status: Status
    message: str
    fix: str | None = None

    def as_dict(self) -> dict[str, str]:
        result = asdict(self)
        if self.fix is None:
            result.pop("fix")
        return result


def _runner_for(repo: Path) -> Runner:
    def run(args: Sequence[str]) -> tuple[int, str]:
        try:
            completed = subprocess.run(
                list(args),
                cwd=repo,
                capture_output=True,
                check=False,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            return 1, ""
        return completed.returncode, completed.stdout.strip()

    return run


def check_python_version(repo: Path, current: tuple[int, int] | None = None) -> Check:
    """Check the running interpreter against project.requires-python."""
    try:
        with (repo / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream).get("project", {})
        requirement = str(project["requires-python"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return Check(
            "python-version",
            "FAIL",
            "could not read project requires-python",
            "restore pyproject.toml",
        )

    match = re.search(r">=\s*(\d+)\.(\d+)", requirement)
    if match is None:
        return Check(
            "python-version",
            "FAIL",
            "could not determine the Python version floor",
            "use a readable requires-python floor",
        )

    floor = (int(match.group(1)), int(match.group(2)))
    running = current or (sys.version_info.major, sys.version_info.minor)
    if running < floor:
        return Check(
            "python-version",
            "FAIL",
            (
                f"Python {running[0]}.{running[1]} is below the project floor "
                f"{floor[0]}.{floor[1]}"
            ),
            f"use Python {floor[0]}.{floor[1]} or newer",
        )
    return Check(
        "python-version",
        "PASS",
        f"Python {running[0]}.{running[1]} meets the {floor[0]}.{floor[1]} floor",
    )


def check_virtualenv(
    prefix: str | None = None, base_prefix: str | None = None
) -> Check:
    current_prefix = prefix if prefix is not None else sys.prefix
    current_base = base_prefix if base_prefix is not None else sys.base_prefix
    if current_prefix == current_base:
        return Check(
            "virtualenv",
            "WARN",
            "running outside a virtual environment",
            "activate the project .venv",
        )
    return Check("virtualenv", "PASS", "running inside a virtual environment")


def check_package_import(
    repo: Path, importer: Callable[[str], object] = importlib.import_module
) -> Check:
    try:
        module = importer("glioma_selective")
    except Exception:
        return Check(
            "package-import",
            "FAIL",
            "could not import glioma_selective",
            "install the project in editable mode",
        )

    module_file = getattr(module, "__file__", None)
    src_root = (repo / "src").resolve()
    if not module_file:
        return Check(
            "package-import",
            "FAIL",
            "glioma_selective has no module file",
            "install the project in editable mode",
        )
    try:
        Path(module_file).resolve().relative_to(src_root)
    except ValueError:
        return Check(
            "package-import",
            "FAIL",
            "glioma_selective is imported from outside this checkout's src directory",
            "reinstall this checkout with pip install -e .",
        )
    return Check(
        "package-import", "PASS", "glioma_selective imports from this checkout"
    )


def check_git(repo: Path, run: Runner) -> Check:
    git_status, _ = run(("git", "--version"))
    if git_status != 0:
        return Check(
            "git",
            "FAIL",
            "git is not available on PATH",
            "install Git and reopen the shell",
        )

    return Check("git", "PASS", "git is available")


def check_git_identity(run: Runner) -> Check:
    missing_identity: list[str] = []
    for field in ("user.name", "user.email"):
        status, value = run(("git", "config", "--get", field))
        if status != 0 or not value.strip():
            missing_identity.append(field)
    if missing_identity:
        return Check(
            "git-identity",
            "WARN",
            f"git identity unset: {', '.join(missing_identity)}",
            "set git config user.name and user.email",
        )
    return Check("git-identity", "PASS", "git identity is configured")


def check_git_hooks(repo: Path, run: Runner) -> Check:
    status, hook_path = run(("git", "rev-parse", "--git-path", "hooks"))
    if status != 0 or not hook_path:
        return Check(
            "git-hooks",
            "WARN",
            "could not determine the repository hooks directory",
            "run pre-commit install",
        )
    hooks = Path(hook_path)
    if not hooks.is_absolute():
        hooks = repo / hooks
    if not (hooks / "pre-commit").is_file():
        return Check(
            "git-hooks",
            "WARN",
            "pre-commit hook is not installed",
            "run pre-commit install",
        )
    return Check("git-hooks", "PASS", "pre-commit hook is installed")


def check_precommit_tool(
    which: Callable[[str], str | None] | None = None,
) -> Check:
    which = shutil.which if which is None else which
    if which("pre-commit") is None:
        return Check(
            "pre-commit-tool",
            "WARN",
            "pre-commit is not available on PATH",
            "activate the project environment or install pre-commit",
        )
    return Check("pre-commit-tool", "PASS", "pre-commit is available on PATH")


def check_gh_auth(
    run: Runner, which: Callable[[str], str | None] | None = None
) -> Check:
    which = shutil.which if which is None else which
    if which("gh") is None:
        return Check(
            "gh-auth",
            "WARN",
            "GitHub CLI is not available on PATH",
            "install gh and run gh auth login",
        )
    status, _ = run(("gh", "auth", "status"))
    if status != 0:
        return Check(
            "gh-auth", "WARN", "GitHub CLI is not authenticated", "run gh auth login"
        )
    return Check("gh-auth", "PASS", "GitHub CLI is authenticated")


def _dotenv_values(path: Path, key: str) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return []
    values: list[str] = []
    for line in lines:
        candidate = line.strip()
        if not candidate or candidate.startswith("#") or "=" not in candidate:
            continue
        name, value = candidate.split("=", 1)
        if name.strip().removeprefix("export ").strip() == key:
            values.append(value.strip().strip("'\""))
    return values


def _dotenv_value(path: Path, key: str) -> str | None:
    values = _dotenv_values(path, key)
    return values[-1] if values else None


def check_env_file(repo: Path, run: Runner) -> Check:
    tracked_status, _ = run(("git", "ls-files", "--error-unmatch", ".env"))
    if tracked_status == 0:
        return Check(
            "env-file",
            "FAIL",
            ".env is tracked by git",
            "remove .env from git and keep it ignored",
        )
    if not (repo / ".env").exists():
        return Check("env-file", "INFO", ".env is absent")
    return Check("env-file", "PASS", ".env exists and is not tracked")


def _flag_state(repo: Path, environ: dict[str, str]) -> str:
    values: list[str] = []
    if EXTERNAL_EVAL_FLAG in environ:
        values.append(environ[EXTERNAL_EVAL_FLAG])
    values.extend(_dotenv_values(repo / ".env", EXTERNAL_EVAL_FLAG))
    if not values:
        return "unset"
    if all(value == "0" for value in values):
        return "0"
    return "NOT ZERO"


def check_external_eval_flag(
    repo: Path, environ: dict[str, str] | None = None
) -> Check:
    state = _flag_state(repo, dict(os.environ) if environ is None else environ)
    if state == "NOT ZERO":
        return Check(
            "external-eval-flag",
            "FAIL",
            "GLIOMA_EXTERNAL_EVAL_AUTHORIZED is NOT ZERO",
            "set GLIOMA_EXTERNAL_EVAL_AUTHORIZED=0 or unset it",
        )
    return Check(
        "external-eval-flag", "PASS", f"GLIOMA_EXTERNAL_EVAL_AUTHORIZED: {state}"
    )


def check_wsl(repo: Path, proc_version: str | None = None) -> Check:
    if proc_version is None:
        try:
            proc_version = Path("/proc/version").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            proc_version = ""
    lowered = proc_version.lower()
    if "microsoft" not in lowered:
        return Check("wsl", "INFO", "not WSL")
    version = "WSL2" if "wsl2" in lowered else "WSL (version not determined)"
    mount_prefix = (os.sep + "mnt" + os.sep).replace("\\", "/")
    if str(repo).replace("\\", "/").startswith(mount_prefix):
        return Check(
            "wsl",
            "WARN",
            f"{version}; repository is under /mnt",
            "keep the checkout in the WSL filesystem",
        )
    return Check("wsl", "INFO", version)


def _git_config(run: Runner, key: str) -> str:
    status, value = run(("git", "config", "--get", key))
    return value if status == 0 and value else "unset"


def _tracked_text_files(run: Runner) -> list[Path]:
    status, output = run(
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
        )
    )
    candidates: list[Path] = []
    if status == 0:
        for name in sorted(item for item in output.split("\0") if item):
            path = Path(name)
            if path.suffix.lower() not in {".md", ".py", ".toml", ".yaml"}:
                continue
            candidates.append(path)
            if len(candidates) == 50:
                break

    return candidates


def _crlf_files(repo: Path, candidates: Sequence[Path]) -> list[str]:
    crlf_files: list[str] = []
    for relative in candidates:
        try:
            if b"\r\n" in (repo / relative).read_bytes():
                crlf_files.append(relative.as_posix())
        except OSError:
            continue
    return crlf_files


def check_line_endings(repo: Path, run: Runner) -> Check:
    autocrlf = _git_config(run, "core.autocrlf")
    eol = _git_config(run, "core.eol")
    crlf_files = _crlf_files(repo, _tracked_text_files(run))
    if crlf_files:
        message = (
            f"core.autocrlf={autocrlf}; core.eol={eol}; "
            f"CRLF found in {', '.join(crlf_files)}"
        )
        return Check(
            "line-endings",
            "WARN",
            message,
            "convert checked text files to LF",
        )
    return Check(
        "line-endings",
        "INFO",
        f"core.autocrlf={autocrlf}; core.eol={eol}; no CRLF found in checked files",
    )


def check_storage_root(repo: Path, environ: dict[str, str] | None = None) -> Check:
    values = dict(os.environ) if environ is None else environ
    value = values.get(STORAGE_ROOT)
    if value is None:
        value = _dotenv_value(repo / ".env", STORAGE_ROOT)
    if not value:
        return Check("storage-root", "INFO", "GLIOMA_STORAGE_ROOT: unset")
    state = "exists" if Path(value).is_dir() else "missing"
    return Check("storage-root", "INFO", f"GLIOMA_STORAGE_ROOT: set, {state}")


def check_branch(run: Runner) -> Check:
    branch_status, branch = run(("git", "branch", "--show-current"))
    if branch_status != 0 or not branch:
        return Check("branch", "INFO", "branch could not be determined")
    status, changes = run(("git", "status", "--porcelain", "--untracked-files=no"))
    if branch == "main" and status == 0 and changes.strip():
        return Check(
            "branch",
            "WARN",
            "main has uncommitted changes",
            "work on a contributor branch",
        )
    return Check("branch", "INFO", f"branch: {branch}")


def collect_checks(repo: Path) -> list[Check]:
    run = _runner_for(repo)
    return [
        check_python_version(repo),
        check_virtualenv(),
        check_package_import(repo),
        check_git(repo, run),
        check_git_identity(run),
        check_git_hooks(repo, run),
        check_precommit_tool(),
        check_gh_auth(run),
        check_env_file(repo, run),
        check_external_eval_flag(repo),
        check_wsl(repo),
        check_line_endings(repo, run),
        check_storage_root(repo),
        check_branch(run),
    ]


def _summary(checks: Sequence[Check]) -> dict[str, int]:
    return {
        status: sum(check.status == status for check in checks)
        for status in ("PASS", "WARN", "FAIL", "INFO")
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="repository to inspect")
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="emit one JSON object"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo = (args.repo or Path(__file__).resolve().parents[1]).resolve()
    if not repo.is_dir():
        print(f"error: repository does not exist: {repo}", file=sys.stderr)
        return 2

    checks = collect_checks(repo)
    counts = _summary(checks)
    if args.as_json:
        print(
            json.dumps(
                {"checks": [check.as_dict() for check in checks], "summary": counts}
            )
        )
    else:
        for check in checks:
            fix = f"  (fix: {check.fix})" if check.fix else ""
            print(f"{check.status}  {check.name}  {check.message}{fix}")
        print(
            "SUMMARY  " + "  ".join(f"{status}={counts[status]}" for status in counts)
        )
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

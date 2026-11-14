#!/usr/bin/env python3
"""T11.7 pre-flight audit: could external results have leaked before Gate E?

Read-only and repeatable.  Prints a JSON report and exits 1 on any finding in a
check marked ``blocking``.  Checks:

1. ``flag``: ``GLIOMA_EXTERNAL_EVAL_AUTHORIZED`` is not "1" in the environment or
   in ``.env``.
2. ``model_code``: no source file under models/training/selective/calibration/
   uncertainty/statistics names an external cohort.
3. ``label_readers``: files that name an external metadata file or call
   ``external_data_dir`` are all on the operational allowlist.
4. ``fixtures``: no test fixture names an external cohort or patient ID pattern.
5. ``artifacts``: no experiment artifact under the given roots holds a number
   under an external-cohort key (JSON) or on a line naming an external cohort,
   a metric and a number (logs, text).
6. ``docs``: lines in Markdown that name an external cohort, a metric and a
   number (review list, not blocking: planned metrics and counts trigger it).
7. ``history``: commit messages on any branch that name an external cohort and a
   metric (review list, not blocking).
8. ``gate_log``: ``GATE_E_LOG.md`` has no authorization entry.

Usage: python scripts/audit_external_leak.py [--artifact-root PATH ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

FLAG = "GLIOMA_EXTERNAL_EVAL_AUTHORIZED"
COHORT = re.compile(r"ucsf|pdgm|\begd\b|egd[-_]", re.IGNORECASE)
PATIENT_ID = re.compile(r"UCSF-PDGM-\d{3,4}|EGD-\d{3,}", re.IGNORECASE)
METRIC = re.compile(
    r"auroc|auc\b|aurc|\bece\b|brier|coverage|accuracy|sensitivity|specificity"
    r"|dice|hd95|risk[-_ ]coverage|auprc",
    re.IGNORECASE,
)
NUMBER = re.compile(r"(?<![\w.])\d+\.\d{2,}")
MODEL_DIRS = (
    "models",
    "training",
    "selective",
    "calibration",
    "uncertainty",
    "statistics",
)
LABEL_READER_ALLOWLIST = (
    "data/metadata.py",
    "data/adapters/",
    "leakage/",
    "preprocessing/",
    "evaluation/firewall.py",
    "utils/paths.py",
)
LABEL_READER_PATTERN = re.compile(
    r"external_data_dir|UCSF-PDGM-metadata|EGD.*(metadata|clinical)", re.IGNORECASE
)
TEXT_SUFFIXES = {".json", ".log", ".txt", ".md", ".csv", ".tsv", ".yaml", ".yml"}


def _finding(check: str, where: str, detail: str, blocking: bool) -> dict[str, Any]:
    return {"check": check, "where": where, "detail": detail, "blocking": blocking}


def check_flag(
    repo: Path, environ: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    env = os.environ if environ is None else environ
    findings = []
    if env.get(FLAG, "0").strip() == "1":
        findings.append(_finding("flag", "environment", f"{FLAG} is 1", True))
    dotenv = repo / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            stripped = line.strip().removeprefix("export ").strip()
            if stripped.startswith(FLAG + "=") and stripped.split("=", 1)[1].strip(
                " \"'"
            ) not in ("0", ""):
                findings.append(_finding("flag", ".env", f"{FLAG} is set", True))
    return findings


def _python_files(src: Path) -> Iterable[Path]:
    return sorted(p for p in src.rglob("*.py") if "egg-info" not in p.parts)


def check_model_code(repo: Path) -> list[dict[str, Any]]:
    findings = []
    base = repo / "src" / "glioma_selective"
    for directory in MODEL_DIRS:
        for path in _python_files(base / directory):
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if COHORT.search(line):
                    findings.append(
                        _finding(
                            "model_code",
                            f"{path.relative_to(repo)}:{number}",
                            line.strip()[:120],
                            True,
                        )
                    )
    return findings


def check_label_readers(repo: Path) -> list[dict[str, Any]]:
    findings = []
    base = repo / "src" / "glioma_selective"
    for path in _python_files(base):
        relative = path.relative_to(base).as_posix()
        if any(relative.startswith(prefix) for prefix in LABEL_READER_ALLOWLIST):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if LABEL_READER_PATTERN.search(line):
                findings.append(
                    _finding(
                        "label_readers",
                        f"src/glioma_selective/{relative}:{number}",
                        line.strip()[:120],
                        True,
                    )
                )
    for path in sorted((repo / "scripts").glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if LABEL_READER_PATTERN.search(line) and "external_data_dir" in line:
                findings.append(
                    _finding(
                        "label_readers",
                        f"scripts/{path.name}:{number}",
                        line.strip()[:120],
                        False,
                    )
                )
    return findings


def check_fixtures(repo: Path) -> list[dict[str, Any]]:
    findings = []
    for path in sorted((repo / "tests" / "fixtures").rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if PATIENT_ID.search(text) or COHORT.search(text):
            findings.append(
                _finding(
                    "fixtures", str(path.relative_to(repo)), "names a cohort", True
                )
            )
    return findings


def _json_leaks(node: Any, path: tuple[str, ...]) -> Iterable[str]:
    """Yield key paths where a numeric value sits under an external-cohort key."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _json_leaks(value, (*path, str(key)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _json_leaks(value, (*path, str(index)))
    elif (
        isinstance(node, int | float)
        and not isinstance(node, bool)
        and any(COHORT.search(part) for part in path)
    ):
        yield "/".join(path)


def _scan_artifact(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".json":
        try:
            return [
                f"numeric value at {leak}" for leak in _json_leaks(json.loads(text), ())
            ]
        except ValueError:
            pass
    return [
        f"{number}: {line.strip()[:100]}"
        for number, line in enumerate(text.splitlines(), 1)
        if COHORT.search(line) and METRIC.search(line) and NUMBER.search(line)
    ]


def check_artifacts(roots: Sequence[Path]) -> list[dict[str, Any]]:
    findings = []
    for root in roots:
        if not root.is_dir():
            findings.append(
                _finding(
                    "artifacts", str(root), "root not readable, not scanned", False
                )
            )
            continue
        for path in sorted(root.rglob("*")):
            if (
                not path.is_file()
                or path.suffix not in TEXT_SUFFIXES
                or path.stat().st_size > 50_000_000
            ):
                continue
            for detail in _scan_artifact(path):
                findings.append(_finding("artifacts", str(path), detail, True))
    return findings


def check_docs(repo: Path) -> list[dict[str, Any]]:
    findings = []
    for path in sorted((repo / "docs").rglob("*.md")) + sorted(
        (repo / "paper").rglob("*.md")
    ):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if COHORT.search(line) and METRIC.search(line) and NUMBER.search(line):
                findings.append(
                    _finding(
                        "docs",
                        f"{path.relative_to(repo)}:{number}",
                        line.strip()[:160],
                        False,
                    )
                )
    return findings


def check_history(repo: Path) -> list[dict[str, Any]]:
    try:
        out = subprocess.run(
            ["git", "log", "--all", "--pretty=%h|%s"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return [_finding("history", "git", "git log failed, not scanned", False)]
    findings = []
    for line in out.splitlines():
        sha, _, subject = line.partition("|")
        if COHORT.search(subject) and METRIC.search(subject):
            findings.append(_finding("history", sha, subject[:120], False))
    return findings


def check_gate_log(repo: Path) -> list[dict[str, Any]]:
    path = repo / "docs" / "research" / "protocols" / "GATE_E_LOG.md"
    if not path.is_file():
        return [_finding("gate_log", str(path), "missing", True)]
    entries = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if re.match(r"^\|\s*20\d\d-\d\d-\d\d", line)
    ]
    return [
        _finding("gate_log", str(path.name), f"{len(entries)} entries", True)
        for _ in range(1 if entries else 0)
    ]


def run_audit(
    repo: Path,
    artifact_roots: Sequence[Path] = (),
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    findings += check_flag(repo, environ)
    findings += check_model_code(repo)
    findings += check_label_readers(repo)
    findings += check_fixtures(repo)
    findings += check_artifacts(artifact_roots)
    findings += check_docs(repo)
    findings += check_history(repo)
    findings += check_gate_log(repo)
    blocking = [f for f in findings if f["blocking"]]
    return {
        "blocking_count": len(blocking),
        "review_count": len(findings) - len(blocking),
        "findings": findings,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--artifact-root", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    report = run_audit(args.repo, args.artifact_root)
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 1 if report["blocking_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check repository invariants that must remain true throughout the project."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path

IMPLEMENTATION_ROOTS = ("src", "scripts", "configs", ".github", "tests")
TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}
ENDPOINT_MGMT_PATTERN = re.compile(
    r"(?:endpoint|target|label|outcome|task|head|metric|primary_endpoint)"
    r"\s*(?::|=)\s*[\"']mgmt[\"']",
    re.IGNORECASE,
)
ABSOLUTE_ROOT_PATTERNS = (
    re.compile(r"/Volumes/"),
    re.compile(r"/mnt/"),
    re.compile(r"(?:^|[^.])\.\./\.\./data(?:/|$)"),
)
VISUALIZATION_IMPORT_PATTERN = re.compile(
    r"(?:from\s+[.\w]*visualization\s+import|"
    r"import\s+glioma_selective\.visualization(?:\.|\s|$))"
)


def _iter_text_files(root: Path) -> Iterable[Path]:
    """Yield implementation files, excluding VCS and generated directories."""

    for directory_name in IMPLEMENTATION_ROOTS:
        directory = root / directory_name
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
                yield path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _location(path: Path, line_number: int, message: str) -> str:
    return f"{path}:{line_number}: {message}"


def _matches(pattern: re.Pattern[str], text: str) -> Iterable[tuple[int, str]]:
    for match in pattern.finditer(text):
        line_number = text.count("\n", 0, match.start()) + 1
        yield line_number, match.group(0)


def check_invariants(root: Path) -> list[str]:
    """Return invariant violations found below *root*.

    The checker intentionally scans implementation and test configuration only;
    planning documents may discuss MGMT and filesystem examples without making
    either one part of the executable research pipeline.
    """

    violations: list[str] = []
    checker_path = Path(__file__).resolve()

    for path in _iter_text_files(root):
        if path.resolve() == checker_path:
            continue
        text = _read(path)

        for line_number, match in _matches(ENDPOINT_MGMT_PATTERN, text):
            violations.append(
                _location(path, line_number, f"MGMT cannot be an endpoint: {match!r}")
            )

        for pattern in ABSOLUTE_ROOT_PATTERNS:
            for line_number, match in _matches(pattern, text):
                violations.append(
                    _location(
                        path,
                        line_number,
                        f"hard-coded filesystem root is forbidden: {match!r}",
                    )
                )

        if "evaluation" in path.parts:
            for line_number, match in _matches(VISUALIZATION_IMPORT_PATTERN, text):
                violations.append(
                    _location(
                        path,
                        line_number,
                        f"evaluation code cannot import visualization: {match!r}",
                    )
                )

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="repository root (defaults to the current directory)",
    )
    args = parser.parse_args(argv)
    violations = check_invariants(args.root.resolve())
    if violations:
        print("Repository invariant check failed:", file=sys.stderr)
        print("\n".join(violations), file=sys.stderr)
        return 1
    print("Repository invariant check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit Phase 04 cached volumes and masks without printing patient IDs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.preprocessing.output_audit import (  # noqa: E402
    OutputAuditError,
    audit_preprocessing_outputs,
)
from glioma_selective.utils import paths  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outputs", type=Path, default=None)
    parser.add_argument(
        "--cohort-manifest",
        type=Path,
        default=REPOSITORY_ROOT
        / "docs/research/manifests/cohort_manifest_post_qc.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT
        / "docs/research/manifests/preprocessing_output_audit.json",
    )
    parser.add_argument("--cache-root", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the audit and return one when any check fails."""

    arguments = _parser().parse_args(argv)
    try:
        report = audit_preprocessing_outputs(
            outputs_path=arguments.outputs,
            cohort_manifest_path=arguments.cohort_manifest,
            output_path=arguments.output,
            cache_root=arguments.cache_root or paths.processed_data_dir(),
        )
    except OutputAuditError as error:
        print(f"audit_preprocessing_outputs.py: audit failed: {error}", file=sys.stderr)
        return 1
    except (OSError, RuntimeError, TypeError, ValueError):
        print("audit_preprocessing_outputs.py: audit failed", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return int(not bool(report["passed"]))


if __name__ == "__main__":
    raise SystemExit(main())

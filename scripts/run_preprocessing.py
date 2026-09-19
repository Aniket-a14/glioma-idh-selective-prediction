#!/usr/bin/env python3
"""Run the resumable Phase 04 preprocessing pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.preprocessing.pipeline import run_pipeline  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", choices=("utsw", "ucsf_pdgm", "all"), default="all")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--cache-root", type=Path, default=None)
    parser.add_argument("--status-path", type=Path, default=None)
    parser.add_argument("--outputs-path", type=Path, default=None)
    parser.add_argument("--n-threads", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline and print aggregate counts only."""

    args = _parser().parse_args(argv)
    try:
        result = run_pipeline(
            args.cohort,
            limit=args.limit,
            cache_root=args.cache_root,
            status_path=args.status_path,
            outputs_path=args.outputs_path,
            n_threads=args.n_threads,
            dry_run=args.dry_run,
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        print("run_preprocessing.py: preprocessing run failed", file=sys.stderr)
        return 1
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())

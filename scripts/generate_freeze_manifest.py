#!/usr/bin/env python3
"""Generate an unsigned Gate E freeze manifest, or seal a hand-signed copy."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path


def main(argv: Sequence[str] | None = None) -> int:
    """Refuse the authorization flag before inspecting arguments or input files."""
    flag = "GLIOMA_EXTERNAL_EVAL_AUTHORIZED"
    if os.environ.get(flag) == "1":
        print(f"{flag}: generation and sealing are blocked", file=sys.stderr)
        return 1

    source_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(source_root / "src"))
    from glioma_selective.evaluation.freeze_manifest import (
        ManifestError,
        build_manifest,
        git_state,
        seal_manifest,
        write_manifest,
    )
    from glioma_selective.utils import paths

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--spec", type=Path)
    mode.add_argument("--seal", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repo", type=Path, default=source_root)
    args = parser.parse_args(argv)
    if args.seal is not None and (args.output is not None or args.repo != source_root):
        parser.error("--output and --repo apply only to --spec")
    try:
        if args.seal is not None:
            print(seal_manifest(args.seal))
            return 0
        commit, clean = git_state(args.repo)
        manifest = build_manifest(
            args.spec,
            roots={
                "repo": args.repo,
                "data": paths.data_root(),
                "artifacts": paths.artifact_root(),
            },
            code_commit_sha=commit,
            created_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            tree_clean=clean,
        )
        output = args.output
        if output is None:
            output = paths.experiments_dir() / "gate_e" / "freeze_manifest.json"
        write_manifest(manifest, output)
        # Read the sidecar without refreshing it: only --seal may rewrite it.
        digest = (
            output.with_name(output.name + ".sha256")
            .read_bytes()
            .split()[0]
            .decode("ascii")
        )
        print(output)
        print(digest)
    except (ManifestError, FileExistsError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

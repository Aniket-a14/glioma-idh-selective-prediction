#!/usr/bin/env python3
"""Compute UTSW patient-level splits or write a caller-selected manifest."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_retained_rosters,
    compute_roster_sha256,
)
from glioma_selective.leakage.id_normalization import (  # noqa: E402
    Cohort,
    normalize_identifier,
)
from glioma_selective.splits import (  # noqa: E402
    SplitConfig,
    SplitLabels,
    load_split_config,
    read_utsw_split_labels,
    sha256_file,
    stratified_patient_split,
    verify_split_manifest,
    write_split_manifest,
)
from glioma_selective.splits.stratified import split_summary  # noqa: E402
from glioma_selective.utils import paths  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--freeze", action="store_true")
    return parser


def _freeze_split_manifest(
    manifest_dir: Path,
    splits: Mapping[str, Sequence[str]],
    labels: Mapping[str, SplitLabels],
    config: SplitConfig,
    exclusion_path: Path,
    roster: Sequence[str],
) -> str:
    """Write and verify the one-time split freeze in a supplied manifest directory."""
    manifest_path = manifest_dir / "splits.json"
    sidecar_path = manifest_dir / "splits.json.sha256"
    if manifest_path.exists() or sidecar_path.exists():
        raise FileExistsError(
            "frozen split manifest or sidecar already exists; a new version needs "
            "a decision-log entry"
        )

    write_split_manifest(
        manifest_path,
        splits,
        labels,
        config,
        exclusion_path,
        roster,
    )
    digest = sha256_file(manifest_path)
    with sidecar_path.open("x", encoding="ascii", newline="\n") as sidecar:
        sidecar.write(f"{digest}  splits.json\n")
    verify_split_manifest(manifest_path, digest)
    print(f"split_manifest_sha256: {digest}")
    return digest


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be a JSON object")
    return cast(Mapping[str, object], value)


def _load_exclusion_document(path: Path) -> Mapping[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return _mapping(document, "post-QC exclusion manifest")


def _utsw_excluded_ids(document: Mapping[str, object]) -> frozenset[str]:
    raw_exclusions = document.get("exclusions")
    if not isinstance(raw_exclusions, list):
        raise ValueError("post-QC exclusion manifest exclusions must be an array")
    excluded: set[str] = set()
    for raw_entry in raw_exclusions:
        entry = _mapping(raw_entry, "exclusion entry")
        if entry.get("cohort") != Cohort.UTSW.value:
            continue
        raw_id = entry.get("patient_id")
        if not isinstance(raw_id, str):
            raise ValueError("UTSW exclusion entry must have a patient ID")
        excluded.add(normalize_identifier(raw_id, Cohort.UTSW))
    return frozenset(excluded)


def _print_summary(
    *,
    roster: Sequence[str],
    summary: Mapping[str, object],
    exclusion_sha256: str,
    roster_sha256: str,
    config_seed: int,
) -> None:
    print(f"population_count: {len(roster)}")
    print(f"seed: {config_seed}")
    print(f"source_exclusion_manifest_sha256: {exclusion_sha256}")
    print(f"roster_sha256: {roster_sha256}")
    for split_name, split_counts in summary.items():
        print(f"{split_name}: {json.dumps(split_counts, sort_keys=True)}")


def main(argv: Sequence[str] | None = None) -> int:
    """Use post-QC UTSW inputs and emit counts only in dry-run mode."""
    args = _parser().parse_args(argv)
    if args.freeze and args.dry_run:
        _parser().error("--freeze cannot be used with --dry-run")
    if args.output is None and not args.freeze:
        _parser().error("--output is required unless --freeze is given")
    exclusion_path = paths.manifests_dir() / "exclusion_manifest_post_qc.json"
    governed_split_path = (paths.manifests_dir() / "splits.json").resolve()
    output_path = (
        args.output.resolve() if args.output is not None else governed_split_path
    )
    if args.freeze and output_path != governed_split_path:
        _parser().error(
            "--output with --freeze must equal the governed splits.json path"
        )
    if not args.freeze and not args.dry_run and output_path == governed_split_path:
        raise ValueError("refusing to create the governed Phase 05 split manifest")

    exclusion_document = _load_exclusion_document(exclusion_path)
    roster_mapping = build_real_retained_rosters(exclusion_document)
    roster = roster_mapping[Cohort.UTSW]
    labels: dict[str, SplitLabels] = read_utsw_split_labels()
    excluded = _utsw_excluded_ids(exclusion_document)
    if set(roster) & excluded:
        raise ValueError("post-QC UTSW roster contains excluded IDs")
    if set(roster) - set(labels):
        raise ValueError("post-QC UTSW roster contains patients without IDH labels")

    config = load_split_config(REPOSITORY_ROOT / "configs/data/splits.yaml")
    splits = stratified_patient_split(roster, labels, config)
    summary = cast(Mapping[str, object], split_summary(splits, labels))
    exclusion_sha256 = sha256_file(exclusion_path)
    roster_sha256 = compute_roster_sha256(roster, Cohort.UTSW)
    _print_summary(
        roster=roster,
        summary=summary,
        exclusion_sha256=exclusion_sha256,
        roster_sha256=roster_sha256,
        config_seed=config.seed,
    )
    if args.freeze:
        _freeze_split_manifest(
            governed_split_path.parent,
            splits,
            labels,
            config,
            exclusion_path,
            roster,
        )
    elif not args.dry_run:
        write_split_manifest(
            output_path,
            splits,
            labels,
            config,
            exclusion_path,
            roster,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

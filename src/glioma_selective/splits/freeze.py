"""Deterministic split-manifest serialization and byte verification."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from glioma_selective.leakage.cohort_manifest import compute_roster_sha256
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.splits.stratified import (
    SplitConfig,
    SplitLabels,
    split_summary,
)

__all__ = ["sha256_file", "verify_split_manifest", "write_split_manifest"]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file's exact bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_split_manifest(path: Path, expected_sha256: str) -> None:
    """Raise when a split manifest's bytes differ from its expected digest."""
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise ValueError("split manifest SHA-256 does not match the expected digest")


def write_split_manifest(
    path: Path,
    splits: Mapping[str, Sequence[str]],
    labels: Mapping[str, SplitLabels],
    config: SplitConfig,
    source_exclusion_manifest_path: Path,
    roster: Sequence[str],
) -> Path:
    """Write a caller-selected split manifest with IDs only in split lists."""
    config.validate()
    expected_names = {"train", "calibration", "internal_test"}
    if set(splits) != expected_names:
        raise ValueError("split mapping must contain exactly the three named splits")
    canonical_roster = tuple(sorted(set(roster)))
    if len(canonical_roster) != len(roster):
        raise ValueError("manifest roster contains duplicate patient IDs")
    split_payload = {
        name: sorted(splits[name]) for name in ("train", "calibration", "internal_test")
    }
    split_sets = [set(values) for values in split_payload.values()]
    if any(
        split_sets[left] & split_sets[right]
        for left in range(len(split_sets))
        for right in range(left + 1, len(split_sets))
    ):
        raise ValueError("split mapping contains a patient in more than one split")
    if set().union(*split_sets) != set(canonical_roster):
        raise ValueError("split mapping does not cover the supplied retained roster")
    summary: dict[str, object] = {
        "population_count": len(canonical_roster),
        "splits": split_summary(split_payload, labels),
    }
    document: dict[str, object] = {
        "manifest_version": 1,
        "seed": config.seed,
        "proportions": config.proportions,
        "stratify_on": config.stratify_on,
        "source_exclusion_manifest_sha256": sha256_file(source_exclusion_manifest_path),
        "roster_sha256": compute_roster_sha256(canonical_roster, Cohort.UTSW),
        "summary": summary,
        "splits": split_payload,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path

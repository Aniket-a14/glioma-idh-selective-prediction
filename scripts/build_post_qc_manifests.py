#!/usr/bin/env python3
"""Build the Phase 04 post-QC exclusion and cohort manifests."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_cohort_manifest,
    build_real_retained_rosters,
    verify_roster_digest,
)
from glioma_selective.leakage.exclusions import (  # noqa: E402
    append_qc_exclusions,
    build_real_exclusion_manifest,
)
from glioma_selective.leakage.id_normalization import (  # noqa: E402
    Cohort,
    IdentifierNormalizationError,
    normalize_identifier,
)
from glioma_selective.preprocessing.qc_exclusions import (  # noqa: E402
    qc_exclusion_records,
)
from glioma_selective.preprocessing.status import (  # noqa: E402
    PreprocessingStatusManifest,
)
from glioma_selective.utils import paths  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-path", type=Path, default=None)
    parser.add_argument("--exclusion-output", type=Path, default=None)
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=REPOSITORY_ROOT
        / "docs/research/manifests/cohort_manifest_post_qc.json",
    )
    return parser


def _atomic_json_write(payload: Mapping[str, object], destination: Path) -> None:
    """Write JSON with a same-directory temporary file and atomic replace."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        temporary_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        with temporary_path.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _resolved_output_paths(
    manifest_output: Path, exclusion_output: Path
) -> tuple[Path, Path]:
    """Resolve outputs and refuse both frozen Phase 03 artifact paths."""

    resolved_manifest = manifest_output.resolve()
    resolved_exclusion = exclusion_output.resolve()
    frozen_paths = {
        (REPOSITORY_ROOT / "docs/research/manifests/cohort_manifest.json").resolve(),
        (paths.manifests_dir() / "exclusion_manifest.json").resolve(),
    }
    if resolved_manifest in frozen_paths or resolved_exclusion in frozen_paths:
        raise ValueError("refusing to overwrite a frozen Phase 03 manifest")
    return resolved_manifest, resolved_exclusion


def _canonical_qc_ids(
    records: Sequence[tuple[str, str, tuple[str, ...]]],
) -> dict[Cohort, set[str]]:
    """Canonicalize QC records and reject duplicate canonical patient IDs."""

    result: dict[Cohort, set[str]] = {}
    for cohort_name, patient_id, _ in records:
        try:
            cohort = Cohort(cohort_name)
            canonical = normalize_identifier(patient_id, cohort)
        except (IdentifierNormalizationError, ValueError, TypeError) as error:
            raise ValueError(
                "QC status manifest contains an invalid patient ID"
            ) from error
        ids = result.setdefault(cohort, set())
        if canonical in ids:
            raise ValueError("QC status manifest contains duplicate canonical patients")
        ids.add(canonical)
    return result


def _retained_by_cohort(
    rosters: Mapping[Cohort, Sequence[str]],
) -> dict[Cohort, tuple[str, ...]]:
    """Normalize the existing roster mapping keys for script comparisons."""

    result: dict[Cohort, tuple[str, ...]] = {}
    for raw_cohort, roster in rosters.items():
        if raw_cohort not in (Cohort.UTSW, Cohort.UCSF_PDGM):
            raise ValueError("retained roster contains an unknown cohort")
        result[raw_cohort] = tuple(roster)
    return result


def _stop_threshold_exceeded(status_manifest: PreprocessingStatusManifest) -> bool:
    summary = status_manifest.summary()
    raw_cohorts = summary.get("cohorts")
    if not isinstance(raw_cohorts, Mapping):
        raise ValueError("preprocessing status summary is malformed")
    return any(
        isinstance(report, Mapping) and report.get("exceeds_stop_threshold") is True
        for report in raw_cohorts.values()
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Build post-QC artifacts and print aggregate counts only."""

    args = _parser().parse_args(argv)
    try:
        status_path = args.status_path or (
            paths.manifests_dir() / "preprocessing_status.json"
        )
        exclusion_output = args.exclusion_output or (
            paths.manifests_dir() / "exclusion_manifest_post_qc.json"
        )
        manifest_output, exclusion_output = _resolved_output_paths(
            args.manifest_output, exclusion_output
        )
        status_manifest = PreprocessingStatusManifest.load(status_path)
        if _stop_threshold_exceeded(status_manifest):
            raise ValueError("one or more cohorts exceed the QC stop threshold")
        records = qc_exclusion_records(status_manifest)
        qc_ids = _canonical_qc_ids(records)

        base = build_real_exclusion_manifest()
        retained_pre = _retained_by_cohort(build_real_retained_rosters(base))
        missing_count = sum(
            len(ids - set(retained_pre.get(cohort, ())))
            for cohort, ids in qc_ids.items()
        )
        if missing_count:
            raise ValueError(
                f"{missing_count} QC exclusions are absent from the pre-QC roster"
            )

        post = append_qc_exclusions(base, records)
        retained_post = _retained_by_cohort(build_real_retained_rosters(post))
        for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
            expected = set(retained_pre[cohort]) - qc_ids.get(cohort, set())
            if set(retained_post.get(cohort, ())) != expected:
                raise ValueError(
                    "post-QC roster does not equal pre-QC roster minus QC exclusions"
                )

        _atomic_json_write(post, exclusion_output)

        cohort_manifest = build_cohort_manifest(post, retained_post)
        for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
            verify_roster_digest(cohort_manifest, cohort, retained_post[cohort])
        note = cohort_manifest.get("note")
        if not isinstance(note, str):
            raise ValueError("cohort manifest note is malformed")
        cohort_manifest["stage"] = "post_qc"
        cohort_manifest["pre_qc_manifest"] = "cohort_manifest.json"
        cohort_manifest["note"] = (
            f"{note} Derived from the Phase 03 manifest by removing the "
            "T04.12 QC exclusions."
        )
        _atomic_json_write(cohort_manifest, manifest_output)

        raw_cohorts = cohort_manifest.get("cohorts")
        if not isinstance(raw_cohorts, Mapping):
            raise ValueError("cohort manifest cohorts are malformed")
        summary: dict[str, object] = {"cohorts": {}, "qc_reason_counts": {}}
        summary_cohorts = cast(dict[str, object], summary["cohorts"])
        reason_counts = Counter(
            reason for _, _, reasons in records for reason in reasons
        )
        summary["qc_reason_counts"] = dict(sorted(reason_counts.items()))
        for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
            entry = raw_cohorts.get(cohort.value)
            if not isinstance(entry, Mapping):
                raise ValueError("cohort manifest entry is malformed")
            summary_cohorts[cohort.value] = {
                "retained_pre_qc": len(retained_pre[cohort]),
                "qc_excluded": len(qc_ids.get(cohort, set())),
                "retained_post_qc": len(retained_post[cohort]),
                "roster_sha256_post_qc": entry.get("roster_sha256"),
            }
    except (OSError, RuntimeError, TypeError, ValueError, KeyError) as error:
        print(f"build_post_qc_manifests.py: error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

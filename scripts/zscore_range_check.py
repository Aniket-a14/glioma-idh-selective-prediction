#!/usr/bin/env python3
"""T04.8: report per-patient z-score ranges against UTSW train behavior."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import nibabel as nib
import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.data.adapters._common import CORE_SEQUENCES  # noqa: E402
from glioma_selective.preprocessing.cache import StageCache  # noqa: E402
from glioma_selective.preprocessing.normalize import (  # noqa: E402
    NormalizationStats,
    load_normalization_stats,
)
from glioma_selective.preprocessing.zscore_check import (  # noqa: E402
    ZSummary,
    flag_summary,
    reference_ranges,
    summarize_volume,
)
from glioma_selective.utils import paths  # noqa: E402

_VOLUME_STAGE = "volume"
_COHORTS = ("utsw", "ucsf_pdgm")
_GROUPS = ("train", "calibration", "internal_test", "ucsf_pdgm")
_QUANTITIES = ("mean", "std", "p99_9", "non_finite")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _mapping(value: object, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{context} must be an object with string keys")
    result: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(key, str):
            result[key] = item
    return result


def _read_json(path: Path, context: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read {context}") from error
    return _mapping(value, context)


def _verified_digest(path: Path) -> str:
    sidecar = path.with_name(path.name + ".sha256")
    try:
        expected = sidecar.read_text(encoding="ascii").split()[0]
    except (OSError, UnicodeError, IndexError) as error:
        raise ValueError("a frozen manifest SHA-256 sidecar is required") from error
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if expected != actual:
        raise ValueError("a manifest does not match its frozen SHA-256")
    return actual


def _train_groups(value: object) -> dict[str, str]:
    root = _mapping(value, "split manifest")
    splits = _mapping(root.get("splits"), "split membership")
    groups: dict[str, str] = {}
    for group in ("train", "calibration", "internal_test"):
        members = splits.get(group)
        if not isinstance(members, list) or any(
            not isinstance(patient_id, str) for patient_id in members
        ):
            raise ValueError("split manifest has invalid UTSW membership")
        for patient_id in members:
            if patient_id in groups:
                raise ValueError("a UTSW patient appears in multiple splits")
            groups[patient_id] = group
    return groups


def _case_outputs(value: object) -> dict[str, dict[str, dict[str, str]]]:
    cohorts = _mapping(value, "preprocessing output index")
    result: dict[str, dict[str, dict[str, str]]] = {}
    for cohort in _COHORTS:
        cases = _mapping(cohorts.get(cohort), f"{cohort} output entries")
        parsed_cases: dict[str, dict[str, str]] = {}
        for patient_id, raw_entry in cases.items():
            entry = _mapping(raw_entry, "patient output entry")
            keys: dict[str, str] = {}
            for sequence in CORE_SEQUENCES:
                key = entry.get(sequence.value)
                if not isinstance(key, str) or not key:
                    raise ValueError("a patient is missing a cached modality key")
                keys[sequence.value] = key
            parsed_cases[patient_id] = keys
        result[cohort] = parsed_cases
    return result


def _volume_files(
    patient_outputs: Mapping[str, str], cache: StageCache
) -> dict[str, str]:
    files: dict[str, str] = {}
    for sequence in CORE_SEQUENCES:
        key = patient_outputs[sequence.value]
        entry = cache.get(_VOLUME_STAGE, key)
        if entry is None:
            raise ValueError("a volume is missing or fails its cache hash")
        files[sequence.value] = str(entry / "volume.nii.gz")
    return files


def _summarize_patient(
    item: tuple[str, str, Mapping[str, str]], stats: NormalizationStats
) -> tuple[str, str, dict[str, ZSummary]]:
    group, patient_id, files = item
    summaries: dict[str, ZSummary] = {}
    for sequence in CORE_SEQUENCES:
        image = nib.load(files[sequence.value])
        if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
            raise ValueError("unsupported NIfTI image type")
        volume = np.asarray(image.dataobj, dtype=np.float32)
        summaries[sequence.value] = summarize_volume(volume, sequence, stats)
    return group, patient_id, summaries


def _json_float(value: float) -> float | None:
    """Keep private JSON standards-compliant when a brain summary is non-finite."""

    return value if np.isfinite(value) else None


def aggregate_group(
    summaries: Mapping[str, Mapping[str, ZSummary]],
    ranges: Mapping[str, Mapping[str, tuple[float, float]]],
) -> dict[str, object]:
    """Build identifier-free patient medians and flag counts for one group."""

    modalities = sorted(ranges)
    modality_report: dict[str, object] = {}
    for modality in modalities:
        patient_summaries = [
            summaries[patient_id][modality] for patient_id in sorted(summaries)
        ]
        flagged = [
            flag_summary(summary, ranges[modality]) for summary in patient_summaries
        ]
        modality_report[modality] = {
            "patient_count": len(patient_summaries),
            "median": {
                quantity: float(
                    np.median(
                        [getattr(summary, quantity) for summary in patient_summaries]
                    )
                )
                for quantity in ("mean", "std", "p99_9", "maximum")
            },
            "flagged_patient_count": {
                quantity: sum(quantity in patient_flags for patient_flags in flagged)
                for quantity in _QUANTITIES
            },
            "patients_with_any_flag": sum(
                bool(patient_flags) for patient_flags in flagged
            ),
        }
    return {
        "patient_count": len(summaries),
        "patients_with_any_flag": sum(
            any(
                flag_summary(patient_summaries[modality], ranges[modality])
                for modality in modalities
            )
            for patient_summaries in summaries.values()
        ),
        "modalities": modality_report,
    }


def render_report(
    summaries_by_group: Mapping[str, Mapping[str, Mapping[str, ZSummary]]],
    ranges: Mapping[str, Mapping[str, tuple[float, float]]],
) -> str:
    """Render deterministic stdout aggregates without patient identifiers."""

    lines = ["EGD: skipped (not downloaded)", "Train reference ranges:"]
    for modality in sorted(ranges):
        for quantity in ("mean", "std", "p99_9"):
            minimum, maximum = ranges[modality][quantity]
            lines.append(f"  {modality} {quantity}: [{minimum:.8g}, {maximum:.8g}]")
    for group in _GROUPS:
        if group not in summaries_by_group:
            continue
        aggregate = aggregate_group(summaries_by_group[group], ranges)
        lines.append(
            f"{group}: patients={aggregate['patient_count']} "
            f"patients_with_any_flag={aggregate['patients_with_any_flag']}"
        )
        for modality in sorted(ranges):
            report_value = aggregate["modalities"]
            if not isinstance(report_value, dict):
                raise ValueError("invalid aggregate report")
            modality_value = report_value[modality]
            if not isinstance(modality_value, dict):
                raise ValueError("invalid modality aggregate")
            medians = modality_value["median"]
            flag_counts = modality_value["flagged_patient_count"]
            if not isinstance(medians, dict) or not isinstance(flag_counts, dict):
                raise ValueError("invalid modality aggregate fields")
            lines.append(
                f"  {modality}: patients={modality_value['patient_count']} "
                f"median_mean={medians['mean']:.8g} "
                f"median_std={medians['std']:.8g} "
                f"median_p99_9={medians['p99_9']:.8g} "
                f"median_maximum={medians['maximum']:.8g} "
                + " ".join(
                    f"flagged_{quantity}={flag_counts[quantity]}"
                    for quantity in _QUANTITIES
                )
            )
    return "\n".join(lines)


def _private_rows(
    summaries_by_group: Mapping[str, Mapping[str, Mapping[str, ZSummary]]],
    ranges: Mapping[str, Mapping[str, tuple[float, float]]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for group in _GROUPS:
        for patient_id in sorted(summaries_by_group.get(group, {})):
            for modality in sorted(ranges):
                summary = summaries_by_group[group][patient_id][modality]
                rows.append(
                    {
                        "group": group,
                        "patient_id": patient_id,
                        "modality": modality,
                        "n": summary.n,
                        "mean": _json_float(summary.mean),
                        "std": _json_float(summary.std),
                        "minimum": _json_float(summary.minimum),
                        "maximum": _json_float(summary.maximum),
                        "p0_1": _json_float(summary.p0_1),
                        "p99_9": _json_float(summary.p99_9),
                        "finite": summary.finite,
                        "flags": flag_summary(summary, ranges[modality]),
                    }
                )
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be at least 1")

    manifests = paths.manifests_dir()
    stats_path = manifests / "normalization_stats.json"
    stats_digest = _verified_digest(stats_path)
    stats = load_normalization_stats(stats_path, expected_sha256=stats_digest)

    split_path = manifests / "splits.json"
    split_digest = _verified_digest(split_path)
    if stats.split_manifest_sha256 != split_digest:
        raise ValueError(
            "normalization statistics reference a different split manifest"
        )
    group_by_patient = _train_groups(_read_json(split_path, "split manifest"))
    outputs_path = manifests / "preprocessing_outputs.json"
    cohort_cases = _case_outputs(_read_json(outputs_path, "preprocessing output index"))
    utsw_cases = cohort_cases["utsw"]
    if set(utsw_cases) != set(group_by_patient):
        raise ValueError("UTSW outputs differ from the frozen split roster")

    cache = StageCache(paths.processed_data_dir())
    work_by_group: dict[str, list[tuple[str, str, dict[str, str]]]] = {
        group: [] for group in _GROUPS
    }
    for cohort in _COHORTS:
        for patient_id in sorted(cohort_cases[cohort]):
            group = group_by_patient[patient_id] if cohort == "utsw" else "ucsf_pdgm"
            work_by_group[group].append(
                (
                    group,
                    patient_id,
                    _volume_files(cohort_cases[cohort][patient_id], cache),
                )
            )

    work = [item for group in _GROUPS for item in sorted(work_by_group[group])]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        patient_results = list(
            pool.map(_summarize_patient, work, [stats] * len(work), chunksize=4)
        )
    summaries: dict[str, dict[str, dict[str, ZSummary]]] = {
        group: {} for group in _GROUPS
    }
    for group, patient_id, patient_summaries in patient_results:
        summaries[group][patient_id] = patient_summaries

    ranges = reference_ranges(summaries["train"])
    report = render_report(summaries, ranges)
    print(report)
    if args.dry_run:
        return 0

    output_path = manifests / "normalization_zscore_check.json"
    if output_path.exists():
        raise FileExistsError("private z-score check output already exists")
    document: dict[str, object] = {
        "version": 1,
        "normalization_stats_sha256": stats_digest,
        "split_manifest_sha256": split_digest,
        "reference_ranges": {
            modality: {
                quantity: list(bounds) for quantity, bounds in modality_ranges.items()
            }
            for modality, modality_ranges in ranges.items()
        },
        "rows": _private_rows(summaries, ranges),
    }
    with output_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"zscore_range_check.py: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1) from error

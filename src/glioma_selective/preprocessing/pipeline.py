"""Resumable Phase 04 per-case preprocessing orchestration.

The pipeline deliberately keeps N4 correction and RAS canonicalization in one
content-addressed ``volume`` entry.  The source file is the direct input to
N4; no intermediate N4 cache entry is created.  Reports contain aggregate
counts and exception-class summaries only.  Canonical identifiers and
exception messages are written only to private output indexes, never to
stdout.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

import nibabel as nib
import numpy as np

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing import discovery, masks, n4, reorient
from glioma_selective.preprocessing.cache import (
    StageCache,
    hash_file,
    stage_cache_key,
)
from glioma_selective.preprocessing.status import PreprocessingStatusManifest
from glioma_selective.utils import paths

__all__ = ["PipelineResult", "run_pipeline"]


_VOLUME_STAGE = "volume"
_VOLUME_STAGE_VERSION = "1"
_MASK_STAGE = "mask"
_MASK_STAGE_VERSION = "1"
_MASK_PARAMS: Final[dict[str, object]] = {
    "label_map": {
        str(label): class_id for label, class_id in masks.BRATS_TO_CLASS.items()
    }
}
_COHORTS: Final[tuple[Cohort, ...]] = (Cohort.UTSW, Cohort.UCSF_PDGM)


@dataclass
class _CohortCounts:
    cases_processed: int = 0
    cases_reused: int = 0
    skipped_excluded: int = 0
    failed: int = 0
    volumes_computed: int = 0
    volumes_reused: int = 0
    masks_computed: int = 0
    masks_reused: int = 0
    failure_reasons: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "cases_processed": self.cases_processed,
            "cases_reused": self.cases_reused,
            "skipped_excluded": self.skipped_excluded,
            "failed": self.failed,
            "volumes_computed": self.volumes_computed,
            "volumes_reused": self.volumes_reused,
            "masks_computed": self.masks_computed,
            "masks_reused": self.masks_reused,
            "failure_reasons": {
                stage: dict(sorted(reasons.items()))
                for stage, reasons in sorted(self.failure_reasons.items())
            },
        }


@dataclass(frozen=True)
class PipelineResult:
    """Aggregate result of one pipeline invocation."""

    cohorts: Mapping[str, Mapping[str, object]]
    wall_clock_seconds: float

    @property
    def exit_code(self) -> int:
        """Return non-zero when any selected case failed."""

        return int(any(counts["failed"] for counts in self.cohorts.values()))

    def to_dict(self) -> dict[str, object]:
        """Return the aggregate-only CLI report."""

        return {
            "cohorts": {
                cohort: dict(counts) for cohort, counts in self.cohorts.items()
            },
            "wall_clock_seconds": round(self.wall_clock_seconds, 3),
        }


@dataclass
class _CaseOutcome:
    volume_keys: dict[str, str] = field(default_factory=dict)
    mask_key: str | None = None
    has_segmentation: bool = False
    volume_failures: int = 0
    mask_failed: bool = False
    volume_computed: int = 0
    volume_reused: int = 0
    mask_computed: int = 0
    mask_reused: int = 0
    failures: list[dict[str, str]] = field(default_factory=list)
    failure_reasons: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        return self.volume_failures > 0 or self.mask_failed

    @property
    def complete(self) -> bool:
        return not self.failed and len(self.volume_keys) == len(CORE_SEQUENCES)

    @property
    def all_reused(self) -> bool:
        return self.complete and self.volume_computed == 0 and self.mask_computed == 0


def _record_failure(
    outcome: _CaseOutcome,
    case: discovery.CaseRecord,
    stage: str,
    error: Exception,
) -> None:
    """Record aggregate diagnostics and private detail for one stage failure."""

    exception_class = type(error).__name__
    reasons = outcome.failure_reasons.setdefault(stage, {})
    reasons[exception_class] = reasons.get(exception_class, 0) + 1
    outcome.failures.append(
        {
            "cohort": case.cohort.value,
            "canonical_id": case.canonical_patient_id,
            "stage": stage,
            "exception_class": exception_class,
            "message": str(error),
        }
    )


def _volume_params(
    n4_params: n4.N4Parameters, reorient_params: reorient.ReorientParameters
) -> dict[str, object]:
    return {
        "n4": n4_params.as_cache_params(),
        "reorient": reorient_params.as_cache_params(),
    }


def _volume_key(
    source: Path,
    params: Mapping[str, object],
) -> str:
    return stage_cache_key(
        _VOLUME_STAGE,
        _VOLUME_STAGE_VERSION,
        params,
        [hash_file(source)],
    )


def _mask_key(case: discovery.CaseRecord) -> str:
    mask_path = masks.select_segmentation_file(case)
    if mask_path is None:
        raise ValueError("case has no selected segmentation target")
    try:
        t1ce_path = case.sequence_files[CanonicalSequence.T1CE]
    except KeyError as error:
        raise ValueError("case has no T1ce volume") from error
    return stage_cache_key(
        _MASK_STAGE,
        _MASK_STAGE_VERSION,
        _MASK_PARAMS,
        [hash_file(mask_path), hash_file(t1ce_path)],
    )


def _valid_volume_entry(cache: StageCache, key: str) -> Path | None:
    entry = cache.get(_VOLUME_STAGE, key)
    if entry is None or not (entry / "volume.nii.gz").is_file():
        return None
    return entry


def _valid_mask_entry(cache: StageCache, key: str) -> Path | None:
    entry = cache.get(_MASK_STAGE, key)
    if entry is None or not (entry / "mask.nii.gz").is_file():
        return None
    return entry


def _composite_key(keys: Mapping[str, str]) -> str | None:
    if not keys:
        return None
    return ",".join(
        keys[sequence.value] for sequence in CORE_SEQUENCES if sequence.value in keys
    )


def _write_volume(
    output_dir: Path,
    source_path: Path,
    n4_params: n4.N4Parameters,
    reorient_params: reorient.ReorientParameters,
    *,
    n_threads: int,
) -> None:
    source = nib.load(source_path)
    if not isinstance(source, nib.Nifti1Image):
        raise TypeError("volume stage inputs must be NIfTI-1 images")

    # The source is passed to N4 unchanged.  In particular, this is not
    # canonicalized before correction; D-026 requires the raw LPS input.
    corrected = n4.correct_bias_nifti(source, n4_params, n_threads=n_threads)
    result = reorient.reorient_volume(corrected, reorient_params)
    if result.resampled:
        raise ValueError("volume was resampled although the cohort grid is 1 mm")
    image = result.image
    if nib.aff2axcodes(image.affine) != ("R", "A", "S"):
        raise ValueError("volume output is not RAS oriented")
    if np.dtype(image.get_data_dtype()) != np.dtype(np.float32):
        raise ValueError("volume output is not float32")

    source_array = np.asarray(source.get_fdata(dtype=np.float32))
    corrected_array = np.asarray(image.dataobj)
    input_orientation = nib.orientations.io_orientation(source.affine)
    output_orientation = nib.orientations.io_orientation(image.affine)
    transform = nib.orientations.ornt_transform(input_orientation, output_orientation)
    source_mask = nib.orientations.apply_orientation(source_array != 0, transform)
    if not np.all(corrected_array[~source_mask] == 0):
        raise ValueError("volume output has non-zero background")

    output_dir.mkdir(parents=True, exist_ok=True)
    nib.save(image, output_dir / "volume.nii.gz")


def _read_has_segmentation(entry: Path) -> bool:
    metadata_path = entry / "meta.json"
    if metadata_path.is_file():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        value = payload.get("has_segmentation") if isinstance(payload, dict) else None
        if isinstance(value, bool):
            return value
    image = nib.load(entry / "mask.nii.gz")
    if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
        raise ValueError("mask cache output is not a supported NIfTI image")
    return bool(np.any(np.asarray(image.dataobj) != 0))


def _run_case(
    cache: StageCache,
    case: discovery.CaseRecord,
    *,
    n4_params: n4.N4Parameters,
    reorient_params: reorient.ReorientParameters,
    n_threads: int,
    dry_run: bool,
) -> _CaseOutcome:
    outcome = _CaseOutcome()
    volume_params = _volume_params(n4_params, reorient_params)
    for sequence in CORE_SEQUENCES:
        try:
            source_path = case.sequence_files[sequence]
            key = _volume_key(source_path, volume_params)
            cached = _valid_volume_entry(cache, key)
            if cached is not None:
                outcome.volume_reused += 1
            elif dry_run:
                outcome.volume_computed += 1
            else:

                def compute(output_dir: Path, source: Path = source_path) -> None:
                    _write_volume(
                        output_dir,
                        source,
                        n4_params,
                        reorient_params,
                        n_threads=n_threads,
                    )

                cache.get_or_compute(
                    _VOLUME_STAGE,
                    key,
                    compute,
                    stage_version=_VOLUME_STAGE_VERSION,
                    params=volume_params,
                    input_keys=[hash_file(source_path)],
                )
                if _valid_volume_entry(cache, key) is None:
                    raise ValueError("volume cache entry did not publish volume.nii.gz")
                outcome.volume_computed += 1
            outcome.volume_keys[sequence.value] = key
        except Exception as error:
            outcome.volume_failures += 1
            _record_failure(outcome, case, f"volume:{sequence.value}", error)

    try:
        key = _mask_key(case)
        cached_mask = _valid_mask_entry(cache, key)
        if cached_mask is not None:
            outcome.mask_reused += 1
            if not dry_run:
                outcome.has_segmentation = _read_has_segmentation(cached_mask)
        elif dry_run:
            outcome.mask_computed += 1
        else:
            mask_path = masks.run_mask_stage(cache, case)
            entry = cache.get(_MASK_STAGE, key)
            if entry is None or not mask_path.is_file():
                raise ValueError("mask cache entry did not publish mask.nii.gz")
            outcome.mask_computed += 1
            outcome.has_segmentation = _read_has_segmentation(entry)
        outcome.mask_key = key
    except Exception as error:
        outcome.mask_failed = True
        _record_failure(outcome, case, "mask", error)
    return outcome


def _load_outputs(path: Path) -> dict[str, dict[str, dict[str, object]]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("preprocessing output index could not be read") from error
    if not isinstance(payload, dict):
        raise ValueError("preprocessing output index must be an object")
    result: dict[str, dict[str, dict[str, object]]] = {}
    for cohort, cases in payload.items():
        if not isinstance(cohort, str) or not isinstance(cases, dict):
            raise ValueError("preprocessing output index has invalid cohort data")
        result[cohort] = {}
        for patient_id, output in cases.items():
            if not isinstance(patient_id, str) or not isinstance(output, dict):
                raise ValueError("preprocessing output index has invalid case data")
            result[cohort][patient_id] = dict(output)
    return result


def _save_outputs(
    path: Path, outputs: Mapping[str, Mapping[str, Mapping[str, object]]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(outputs, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _save_failure_log(path: Path, failures: list[dict[str, str]]) -> None:
    """Atomically replace the private raw-identifier failure log."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(failures, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _selected_cases(
    manifest: PreprocessingStatusManifest,
    cohort: Cohort,
    limit: int | None,
) -> tuple[tuple[discovery.CaseRecord, ...], int]:
    statuses = [case for case in manifest.cases.values() if case.cohort == cohort.value]
    statuses.sort(key=lambda case: case.patient_id)
    excluded = [
        case
        for case in statuses
        if case.verification_status == "failed" or bool(case.qc_reasons)
    ]
    retained = [
        case
        for case in statuses
        if case.verification_status != "failed" and not case.qc_reasons
    ]
    if limit is not None:
        retained = retained[:limit]
    if not retained:
        return (), len(excluded)
    cases = discovery.discover_cases(
        cohort,
        retained_patient_ids=[case.patient_id for case in retained],
    )
    return cases, len(excluded)


def run_pipeline(
    cohort: str = "all",
    *,
    limit: int | None = None,
    cache_root: Path | None = None,
    status_path: Path | None = None,
    outputs_path: Path | None = None,
    n_threads: int = 2,
    dry_run: bool = False,
    n4_params: n4.N4Parameters | None = None,
    reorient_params: reorient.ReorientParameters | None = None,
) -> PipelineResult:
    """Process retained cases in deterministic cohort and patient order."""

    if cohort not in {"utsw", "ucsf_pdgm", "all"}:
        raise ValueError("cohort must be utsw, ucsf_pdgm, or all")
    if limit is not None and (isinstance(limit, bool) or limit < 0):
        raise ValueError("limit must be non-negative")
    if isinstance(n_threads, bool) or n_threads < 1:
        raise ValueError("n_threads must be at least 1")

    selected_cohorts = _COHORTS if cohort == "all" else (Cohort(cohort),)
    selected_status_path = status_path or (
        paths.manifests_dir() / "preprocessing_status.json"
    )
    selected_outputs_path = outputs_path or (
        paths.manifests_dir() / "preprocessing_outputs.json"
    )
    manifest = PreprocessingStatusManifest.load(selected_status_path)
    outputs = {} if dry_run else _load_outputs(selected_outputs_path)
    cache = StageCache(cache_root or paths.processed_data_dir())
    selected_n4 = n4_params or n4.N4Parameters()
    selected_reorient = reorient_params or reorient.ReorientParameters()
    counts = {selected.value: _CohortCounts() for selected in selected_cohorts}
    failure_records: list[dict[str, str]] = []
    start = time.monotonic()

    for selected in selected_cohorts:
        cohort_counts = counts[selected.value]
        cases, excluded_count = _selected_cases(manifest, selected, limit)
        cohort_counts.skipped_excluded = excluded_count
        for case in cases:
            outcome = _run_case(
                cache,
                case,
                n4_params=selected_n4,
                reorient_params=selected_reorient,
                n_threads=n_threads,
                dry_run=dry_run,
            )
            cohort_counts.volumes_computed += outcome.volume_computed
            cohort_counts.volumes_reused += outcome.volume_reused
            cohort_counts.masks_computed += outcome.mask_computed
            cohort_counts.masks_reused += outcome.mask_reused
            for stage, reasons in outcome.failure_reasons.items():
                cohort_reasons = cohort_counts.failure_reasons.setdefault(stage, {})
                for exception_class, count in reasons.items():
                    cohort_reasons[exception_class] = (
                        cohort_reasons.get(exception_class, 0) + count
                    )
            failure_records.extend(outcome.failures)

            if outcome.failed:
                cohort_counts.failed += 1
            elif outcome.all_reused:
                cohort_counts.cases_reused += 1
            else:
                cohort_counts.cases_processed += 1

            if dry_run:
                continue

            composite_key = _composite_key(outcome.volume_keys)
            next_manifest = manifest.update_stage(
                selected,
                case.canonical_patient_id,
                "n4",
                "failed" if outcome.volume_failures else "done",
                composite_key,
            )
            next_manifest = next_manifest.update_stage(
                selected,
                case.canonical_patient_id,
                "reorient",
                "failed" if outcome.volume_failures else "done",
                composite_key,
            )
            next_manifest = next_manifest.update_stage(
                selected,
                case.canonical_patient_id,
                "mask",
                "failed" if outcome.mask_failed else "done",
                outcome.mask_key,
            )
            manifest = next_manifest
            cohort_outputs = outputs.setdefault(selected.value, {})
            if outcome.complete and outcome.mask_key is not None:
                cohort_outputs[case.canonical_patient_id] = {
                    **outcome.volume_keys,
                    "mask": outcome.mask_key,
                    "has_segmentation": outcome.has_segmentation,
                }
            else:
                cohort_outputs.pop(case.canonical_patient_id, None)
            manifest.save(selected_status_path)
            _save_outputs(selected_outputs_path, outputs)

    result_counts = {
        cohort_name: cohort_counts.to_dict()
        for cohort_name, cohort_counts in counts.items()
    }
    if not dry_run:
        _save_failure_log(
            paths.private_data_dir() / "preprocessing_failures.json", failure_records
        )
    return PipelineResult(result_counts, time.monotonic() - start)

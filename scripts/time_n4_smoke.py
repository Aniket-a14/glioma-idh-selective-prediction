#!/usr/bin/env python3
"""Time a small retained UTSW/UCSF-PDGM N4 sample without naming cases."""

from __future__ import annotations

import json
import resource
import statistics
import sys
import time
from pathlib import Path

import nibabel as nib
import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_retained_rosters,
)
from glioma_selective.leakage.id_normalization import Cohort  # noqa: E402
from glioma_selective.preprocessing.cache import StageCache  # noqa: E402
from glioma_selective.preprocessing.discovery import discover_cases  # noqa: E402
from glioma_selective.preprocessing.n4 import (  # noqa: E402
    N4Parameters,
    run_n4_stage,
)
from glioma_selective.utils import paths  # noqa: E402

_VOLUMES_PER_CASE = 4
_PROJECTION_VOLUME_COUNT = 3296
_FIRST_VOLUME_LIMIT_SECONDS = 5 * 60
_COHORTS = (Cohort.UTSW, Cohort.UCSF_PDGM)


def _peak_rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return float(usage) / (1024 * 1024)
    return float(usage) / 1024


def _volume_stats(
    input_path: Path,
    output_path: Path,
) -> tuple[float, float, float]:
    before_image = nib.load(input_path)
    after_image = nib.load(output_path)
    before = np.asarray(before_image.dataobj, dtype=np.float64)
    after = np.asarray(after_image.dataobj, dtype=np.float64)
    mask = before != 0
    if not np.any(mask):
        raise ValueError("N4 timing input has an empty implicit mask")
    before_masked = before[mask]
    after_masked = after[mask]
    if np.any(after_masked == 0):
        raise ValueError("N4 timing output has zero intensity inside the mask")
    applied_field = before_masked / after_masked
    ratio = float(np.mean(after_masked / before_masked))
    return float(np.min(applied_field)), float(np.max(applied_field)), ratio


def _summary(
    timings: dict[Cohort, list[float]],
    field_mins: list[float],
    field_maxes: list[float],
    ratios: dict[Cohort, list[float]],
    *,
    stopped_after_first_volume: bool,
) -> dict[str, object]:
    all_timings = [value for values in timings.values() for value in values]
    all_ratios = [value for values in ratios.values() for value in values]
    by_cohort = {
        cohort.value: {
            "volume_count": len(timings[cohort]),
            "seconds_per_volume": {
                "min": min(timings[cohort]) if timings[cohort] else None,
                "median": statistics.median(timings[cohort])
                if timings[cohort]
                else None,
                "max": max(timings[cohort]) if timings[cohort] else None,
            },
            "mean_intensity_ratio_after_before": statistics.mean(ratios[cohort])
            if ratios[cohort]
            else None,
        }
        for cohort in _COHORTS
    }
    median_seconds = statistics.median(all_timings) if all_timings else None
    return {
        "seconds_per_volume": by_cohort,
        "peak_rss_mb": _peak_rss_mb(),
        "applied_field_range": {
            "aggregate_min": min(field_mins) if field_mins else None,
            "aggregate_max": max(field_maxes) if field_maxes else None,
        },
        "mean_intensity_ratio_after_before": statistics.mean(all_ratios)
        if all_ratios
        else None,
        "projection": {
            "median_seconds_per_volume": median_seconds,
            "volumes": _PROJECTION_VOLUME_COUNT,
            "hours_at_one_process": median_seconds * _PROJECTION_VOLUME_COUNT / 3600
            if median_seconds is not None
            else None,
        },
        "stopped_after_first_volume": stopped_after_first_volume,
    }


def main() -> int:
    """Run the aggregate-only timing smoke test."""

    timings = {cohort: [] for cohort in _COHORTS}
    ratios = {cohort: [] for cohort in _COHORTS}
    field_mins: list[float] = []
    field_maxes: list[float] = []
    first_volume = True
    stopped = False
    params = N4Parameters()
    cache = StageCache(paths.interim_data_dir() / "n4_smoke")

    try:
        retained_rosters = build_real_retained_rosters()
        for cohort in _COHORTS:
            retained_ids = sorted(retained_rosters[cohort])[:3]
            cases = discover_cases(cohort, retained_patient_ids=retained_ids)
            for case in cases:
                for input_path in case.sequence_files.values():
                    started = time.perf_counter()
                    output_dir = run_n4_stage(cache, input_path, params, n_threads=2)
                    elapsed = time.perf_counter() - started
                    field_min, field_max, ratio = _volume_stats(
                        input_path,
                        output_dir / "volume.nii.gz",
                    )
                    timings[cohort].append(elapsed)
                    ratios[cohort].append(ratio)
                    field_mins.append(field_min)
                    field_maxes.append(field_max)
                    if first_volume:
                        first_volume = False
                        if elapsed > _FIRST_VOLUME_LIMIT_SECONDS:
                            stopped = True
                            raise StopIteration
    except StopIteration:
        pass
    except (OSError, RuntimeError, TypeError, ValueError):
        print("time_n4_smoke.py: timing failed", file=sys.stderr)
        return 1

    print(
        json.dumps(
            _summary(
                timings,
                field_mins,
                field_maxes,
                ratios,
                stopped_after_first_volume=stopped,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

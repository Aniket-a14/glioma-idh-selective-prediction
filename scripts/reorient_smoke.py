#!/usr/bin/env python3
"""Run an aggregate-only T04.5 smoke test on six retained real cases."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import nibabel as nib
import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.data.adapters._common import CORE_SEQUENCES  # noqa: E402
from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_retained_rosters,
)
from glioma_selective.leakage.id_normalization import Cohort  # noqa: E402
from glioma_selective.preprocessing.cache import StageCache  # noqa: E402
from glioma_selective.preprocessing.discovery import discover_cases  # noqa: E402
from glioma_selective.preprocessing.reorient import (  # noqa: E402
    ReorientParameters,
    reorient_volume,
    run_reorient_stage,
)
from glioma_selective.utils import paths  # noqa: E402

_COHORTS = (Cohort.UTSW, Cohort.UCSF_PDGM)
_EXPECTED_SHAPE = (240, 240, 155)


def _undo_orientation(output: nib.Nifti1Image, source: nib.Nifti1Image) -> np.ndarray:
    transform = nib.orientations.ornt_transform(
        nib.orientations.io_orientation(output.affine),
        nib.orientations.io_orientation(source.affine),
    )
    return nib.orientations.apply_orientation(np.asarray(output.dataobj), transform)


def main() -> int:
    rosters = build_real_retained_rosters()
    cases = tuple(
        case
        for cohort in _COHORTS
        for case in discover_cases(
            cohort,
            retained_patient_ids=rosters[cohort][:3],
        )
    )
    cache = StageCache(paths.interim_data_dir() / "reorient_smoke")
    params = ReorientParameters()
    counts: Counter[str] = Counter()

    for case in cases:
        for sequence in CORE_SEQUENCES:
            counts["volumes"] += 1
            try:
                source = nib.load(case.sequence_files[sequence])
                source_array = np.asarray(source.dataobj)
                source_dtype = source.get_data_dtype()
                source_spacing = tuple(
                    float(value) for value in source.header.get_zooms()[:3]
                )
                direct_result = reorient_volume(source, params)
                result_dir = run_reorient_stage(
                    cache, case.sequence_files[sequence], params
                )
                output = nib.load(result_dir / "volume.nii.gz")
                spacing_matches = all(
                    abs(current - target) <= params.spacing_tolerance_mm
                    for current, target in zip(
                        source_spacing, params.target_spacing, strict=True
                    )
                )
                passed = (
                    nib.aff2axcodes(output.affine) == ("R", "A", "S")
                    and output.shape == _EXPECTED_SHAPE
                    and output.get_data_dtype() == source_dtype
                    and spacing_matches
                    and direct_result.resampled is False
                    and np.array_equal(_undo_orientation(output, source), source_array)
                )
                counts["passed" if passed else "failed"] += 1
                counts["resampled_false"] += int(direct_result.resampled is False)
            except Exception:
                counts["failed"] += 1

    print(
        "cases="
        f"{len(cases)} volumes={counts['volumes']} passed={counts['passed']} "
        f"failed={counts['failed']} resampled_false={counts['resampled_false']}"
    )
    return int(counts["failed"] != 0)


if __name__ == "__main__":
    raise SystemExit(main())

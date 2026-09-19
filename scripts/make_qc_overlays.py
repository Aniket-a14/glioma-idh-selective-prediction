#!/usr/bin/env python3
"""Generate the Phase 04 T04.9 visual-QC sample and review sheet."""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import matplotlib.pyplot as plt  # noqa: E402

from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_retained_rosters,
)
from glioma_selective.leakage.id_normalization import Cohort  # noqa: E402
from glioma_selective.preprocessing.discovery import discover_cases  # noqa: E402
from glioma_selective.preprocessing.qc_overlays import (  # noqa: E402
    QC_SAMPLE_SEED,
    QCOverlayError,
    QCVerificationSummary,
    load_verification_cases,
    read_utsw_idh_labels,
    render_qc_overlay,
    select_qc_sample,
    write_qc_overlay_index,
    write_qc_review_sheet,
)
from glioma_selective.utils import paths  # noqa: E402


def main() -> int:
    """Run one sequential, aggregate-only-reporting QC overlay generation."""

    started = time.perf_counter()
    try:
        verification_path = (
            paths.private_data_dir() / "preprocessing_verification_cases.json"
        )
        verification = load_verification_cases(verification_path)
        retained = build_real_retained_rosters()
        selections = select_qc_sample(
            retained_patient_ids=retained,
            borderline_cases_path=verification_path,
            label_reader=read_utsw_idh_labels,
            utsw_metadata_path=paths.raw_data_dir() / "UTSW_Glioma_Metadata-2-1.tsv",
            seed=QC_SAMPLE_SEED,
        )
        cases = {}
        for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
            cohort_ids = [
                selection.patient_id
                for selection in selections
                if selection.cohort is cohort
            ]
            cases.update(
                {
                    (cohort, case.patient_id): case
                    for case in discover_cases(cohort, retained_patient_ids=cohort_ids)
                }
            )

        output_directory = paths.figures_dir() / "qc"
        output_directory.mkdir(parents=True, exist_ok=True)
        total_bytes = 0
        for selection in selections:
            case = cases.get((selection.cohort, selection.patient_id))
            if case is None:
                raise QCOverlayError(
                    "selected case is absent from the retained inventory"
                )
            figure = render_qc_overlay(
                case,
                selection,
                verification.get(
                    (selection.cohort, selection.patient_id),
                    QCVerificationSummary(None, None),
                ),
            )
            output_path = output_directory / f"{selection.qc_key}.png"
            try:
                figure.savefig(
                    output_path,
                    dpi=100,
                    format="png",
                    metadata={"Software": "Phase 04 QC"},
                )
            finally:
                plt.close(figure)
            size = output_path.stat().st_size
            if size >= 1_000_000:
                raise QCOverlayError(
                    "QC overlay exceeded the one-megabyte artifact limit"
                )
            total_bytes += size

        write_qc_overlay_index(selections)
        write_qc_review_sheet(selections, verification)
        elapsed = time.perf_counter() - started
        print(
            json.dumps(
                {
                    "selected_cases": len(selections),
                    "cases_by_cohort": dict(
                        sorted(
                            Counter(
                                selection.cohort.value for selection in selections
                            ).items()
                        )
                    ),
                    "cases_by_reason": dict(
                        sorted(
                            Counter(
                                selection.selection_reason for selection in selections
                            ).items()
                        )
                    ),
                    "files_written": len(selections),
                    "total_size_mb": round(total_bytes / (1024 * 1024), 3),
                    "wall_clock_seconds": round(elapsed, 3),
                },
                sort_keys=True,
            )
        )
        return 0
    except (OSError, RuntimeError, TypeError, ValueError, QCOverlayError):
        print("make_qc_overlays.py: QC overlay generation failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

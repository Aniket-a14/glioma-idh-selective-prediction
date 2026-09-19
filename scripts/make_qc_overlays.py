#!/usr/bin/env python3
"""Generate the Phase 04 T04.9 visual-QC sample and review sheet."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import matplotlib.pyplot as plt  # noqa: E402

from glioma_selective.data.adapters._common import CanonicalSequence  # noqa: E402
from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_retained_rosters,
)
from glioma_selective.leakage.id_normalization import Cohort  # noqa: E402
from glioma_selective.preprocessing.discovery import (  # noqa: E402
    CaseRecord,
    discover_cases,
)
from glioma_selective.preprocessing.qc_overlays import (  # noqa: E402
    QC_SAMPLE_SEED,
    QCOverlayError,
    QCSelection,
    QCVerificationSummary,
    append_qc_overlay_index,
    append_qc_review_sheet,
    assign_continuing_qc_keys,
    compute_t1ce_shape_metrics,
    load_qc_overlay_index,
    load_verification_cases,
    load_verification_statuses,
    read_utsw_idh_labels,
    render_qc_overlay,
    review_sheet_has_selection_reason,
    select_new_borderline,
    select_qc_sample,
    select_qc_shape_tail,
    select_qc_tail,
    write_qc_overlay_index,
    write_qc_review_sheet,
)
from glioma_selective.utils import paths  # noqa: E402


def _nonnegative_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise ValueError("tail must not be negative")
    return parsed


def _render_selections(
    selections: Sequence[QCSelection],
    verification: Mapping[tuple[Cohort, str], QCVerificationSummary],
    output_directory: Path,
    cases: Mapping[tuple[Cohort, str], CaseRecord],
) -> int:
    """Render only the supplied selections and refuse to replace a PNG."""

    total_bytes = 0
    for selection in selections:
        case = cases.get((selection.cohort, selection.patient_id))
        if case is None:
            raise QCOverlayError("selected case is absent from the retained inventory")
        output_path = output_directory / f"{selection.qc_key}.png"
        if output_path.exists():
            raise QCOverlayError("QC overlay output already exists")
        figure = render_qc_overlay(
            case,
            selection,
            verification.get(
                (selection.cohort, selection.patient_id),
                QCVerificationSummary(None, None),
            ),
        )
        temporary_path: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{output_path.name}.", suffix=".tmp", dir=output_directory
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            figure.savefig(
                temporary_path,
                dpi=100,
                format="png",
                metadata={"Software": "Phase 04 QC"},
            )
            os.replace(temporary_path, output_path)
            temporary_path = None
        finally:
            plt.close(figure)
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
        size = output_path.stat().st_size
        if size >= 1_000_000:
            raise QCOverlayError("QC overlay exceeded the one-megabyte artifact limit")
        total_bytes += size
    return total_bytes


def _report(
    *,
    selections: Sequence[QCSelection],
    total_bytes: int,
    elapsed: float,
    tail: int | None,
    shape_tail: int | None = None,
    shape_tail_cohort: Cohort | None = None,
    new_borderline: bool = False,
) -> None:
    report: dict[str, object] = {
        "selected_cases": len(selections),
        "cases_by_cohort": dict(
            sorted(Counter(selection.cohort.value for selection in selections).items())
        ),
        "cases_by_reason": dict(
            sorted(
                Counter(selection.selection_reason for selection in selections).items()
            )
        ),
        "files_written": len(selections),
        "tail": tail,
        "total_size_mb": round(total_bytes / (1024 * 1024), 3),
        "wall_clock_seconds": round(elapsed, 3),
    }
    if shape_tail is not None:
        metric_count = shape_tail if selections else 0
        report.update(
            {
                "shape_tail": shape_tail,
                "shape_tail_cohort": (
                    None if shape_tail_cohort is None else shape_tail_cohort.value
                ),
                "solidity_cases": metric_count,
                "closing_gain_cases": metric_count,
                "union_size": len(selections),
            }
        )
    if new_borderline:
        report["new_borderline"] = True
    print(json.dumps(report, sort_keys=True))


def _require_complete_overlay_artifacts(index_path: Path, review_path: Path) -> None:
    if not index_path.exists() or not review_path.exists():
        raise QCOverlayError("QC overlay artifacts are incomplete")


def main(argv: Sequence[str] | None = None) -> int:
    """Run one sequential, aggregate-only-reporting QC overlay generation."""

    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    tail_group = parser.add_mutually_exclusive_group()
    tail_group.add_argument(
        "--tail",
        type=_nonnegative_integer,
        default=None,
        help="append N lowest brain-fraction cases per cohort (default: 0)",
    )
    tail_group.add_argument(
        "--shape-tail",
        type=_nonnegative_integer,
        default=None,
        help="append N lowest-solidity and highest-closing-gain cases (0 disables)",
    )
    tail_group.add_argument(
        "--new-borderline",
        action="store_true",
        help="append currently borderline cases not already in the QC index",
    )
    parser.add_argument(
        "--shape-tail-cohort",
        choices=("utsw", "ucsf_pdgm"),
        default="utsw",
        help="cohort for --shape-tail (default: utsw)",
    )
    try:
        arguments = parser.parse_args(argv)
        if arguments.shape_tail == 0:
            _report(
                selections=(),
                total_bytes=0,
                elapsed=0.0,
                tail=None,
                shape_tail=0,
                shape_tail_cohort=Cohort(arguments.shape_tail_cohort),
            )
            return 0
        if arguments.tail == 0:
            _report(selections=(), total_bytes=0, elapsed=0.0, tail=0)
            return 0
        verification_path = (
            paths.private_data_dir() / "preprocessing_verification_cases.json"
        )
        verification = load_verification_cases(verification_path)
        retained = build_real_retained_rosters()
        output_directory = paths.figures_dir() / "qc"
        index_path = paths.private_data_dir() / "qc_overlay_index.json"
        review_path = output_directory / "qc_review_sheet.csv"

        if arguments.new_borderline:
            _require_complete_overlay_artifacts(index_path, review_path)
            existing_index = load_qc_overlay_index(index_path)
            statuses = load_verification_statuses(verification_path)
            selections = select_new_borderline(
                retained_patient_ids=retained,
                verification_statuses=statuses,
                indexed_cases=existing_index.values(),
            )
            selections = assign_continuing_qc_keys(selections, existing_index)
            if not selections:
                _report(
                    selections=(),
                    total_bytes=0,
                    elapsed=time.perf_counter() - started,
                    tail=None,
                    new_borderline=True,
                )
                return 0
            output_directory.mkdir(parents=True, exist_ok=True)
            cases = {}
            for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
                cohort_ids = [
                    selection.patient_id
                    for selection in selections
                    if selection.cohort is cohort
                ]
                if cohort_ids:
                    cases.update(
                        {
                            (cohort, case.patient_id): case
                            for case in discover_cases(
                                cohort, retained_patient_ids=cohort_ids
                            )
                        }
                    )
            total_bytes = _render_selections(
                selections, verification, output_directory, cases
            )
            append_qc_overlay_index(selections, index_path)
            append_qc_review_sheet(selections, verification, review_path)
            _report(
                selections=selections,
                total_bytes=total_bytes,
                elapsed=time.perf_counter() - started,
                tail=None,
                new_borderline=True,
            )
            return 0

        if arguments.shape_tail is not None:
            output_directory.mkdir(parents=True, exist_ok=True)
            selected_cohort = Cohort(arguments.shape_tail_cohort)
            if index_path.exists() != review_path.exists():
                raise QCOverlayError("QC overlay artifacts are incomplete")
            if review_sheet_has_selection_reason(review_path, "shape_tail"):
                _report(
                    selections=(),
                    total_bytes=0,
                    elapsed=time.perf_counter() - started,
                    tail=None,
                    shape_tail=arguments.shape_tail,
                    shape_tail_cohort=selected_cohort,
                )
                return 0
            existing_index = load_qc_overlay_index(index_path)
            all_cases = discover_cases(
                selected_cohort,
                retained_patient_ids=retained[selected_cohort],
            )
            shape_metrics = {
                (selected_cohort, case.patient_id): compute_t1ce_shape_metrics(
                    case.sequence_files[CanonicalSequence.T1CE]
                )
                for case in all_cases
                if (selected_cohort, case.patient_id) not in existing_index.values()
            }
            selections = select_qc_shape_tail(
                retained_patient_ids=retained,
                shape_metrics=shape_metrics,
                indexed_cases=existing_index.values(),
                cohort=selected_cohort,
                per_metric=arguments.shape_tail,
            )
            selections = assign_continuing_qc_keys(selections, existing_index)
            if not selections:
                _report(
                    selections=(),
                    total_bytes=0,
                    elapsed=time.perf_counter() - started,
                    tail=None,
                    shape_tail=arguments.shape_tail,
                    shape_tail_cohort=selected_cohort,
                )
                return 0
            cases = {
                (selected_cohort, case.patient_id): case
                for case in all_cases
                if (selected_cohort, case.patient_id)
                in {(item.cohort, item.patient_id) for item in selections}
            }
            total_bytes = _render_selections(
                selections, verification, output_directory, cases
            )
            append_qc_overlay_index(selections, index_path)
            append_qc_review_sheet(selections, verification, review_path)
            _report(
                selections=selections,
                total_bytes=total_bytes,
                elapsed=time.perf_counter() - started,
                tail=None,
                shape_tail=arguments.shape_tail,
                shape_tail_cohort=selected_cohort,
            )
            return 0
        if arguments.tail is not None:
            output_directory.mkdir(parents=True, exist_ok=True)
            existing_index = load_qc_overlay_index(index_path)
            selections = select_qc_tail(
                retained_patient_ids=retained,
                verification=verification,
                indexed_cases=existing_index.values(),
                per_cohort=arguments.tail,
                seed=QC_SAMPLE_SEED,
            )
            selections = assign_continuing_qc_keys(selections, existing_index)
            if not selections:
                _report(
                    selections=(),
                    total_bytes=0,
                    elapsed=time.perf_counter() - started,
                    tail=arguments.tail,
                )
                return 0
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
                        for case in discover_cases(
                            cohort, retained_patient_ids=cohort_ids
                        )
                    }
                )
            total_bytes = _render_selections(
                selections, verification, output_directory, cases
            )
            append_qc_overlay_index(selections, index_path)
            append_qc_review_sheet(selections, verification, review_path)
        else:
            output_directory.mkdir(parents=True, exist_ok=True)
            # A completed base sample is never regenerated: doing so would
            # overwrite human verdicts on a rerun without --tail.
            if index_path.exists() or review_path.exists():
                if not index_path.exists() or not review_path.exists():
                    raise QCOverlayError("QC overlay artifacts are incomplete")
                _report(
                    selections=(),
                    total_bytes=0,
                    elapsed=time.perf_counter() - started,
                    tail=None,
                )
                return 0
            selections = select_qc_sample(
                retained_patient_ids=retained,
                borderline_cases_path=verification_path,
                label_reader=read_utsw_idh_labels,
                utsw_metadata_path=paths.raw_data_dir()
                / "UTSW_Glioma_Metadata-2-1.tsv",
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
                        for case in discover_cases(
                            cohort, retained_patient_ids=cohort_ids
                        )
                    }
                )
            total_bytes = _render_selections(
                selections, verification, output_directory, cases
            )
            write_qc_overlay_index(selections, index_path)
            write_qc_review_sheet(selections, verification, review_path)
        elapsed = time.perf_counter() - started
        _report(
            selections=selections,
            total_bytes=total_bytes,
            elapsed=elapsed,
            tail=arguments.tail,
        )
        return 0
    except (OSError, RuntimeError, TypeError, ValueError, QCOverlayError):
        print("make_qc_overlays.py: QC overlay generation failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

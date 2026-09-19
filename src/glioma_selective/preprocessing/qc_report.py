"""Build the roster-free Phase 04 automated and visual QC report."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from scipy.stats import beta  # type: ignore[import-untyped]

from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.qc_overlays import load_qc_overlay_index
from glioma_selective.preprocessing.status import PreprocessingStatusManifest
from glioma_selective.preprocessing.verification import VerificationThresholds

__all__ = ["QCReportError", "build_qc_report"]


_ORIGINAL_LOWER_BOUND: Final[float] = 0.08
_CURRENT_LOWER_BOUND: Final[float] = (
    VerificationThresholds().borderline_min_brain_fraction
)
_BOUNDS: Final[tuple[float, ...]] = (
    0.05,
    _ORIGINAL_LOWER_BOUND,
    0.10,
    0.11,
    0.12,
    0.15,
)
_REVIEW_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "qc_key",
        "cohort",
        "selection_reason",
        "brain_voxel_fraction",
        "min_cross_sequence_dice",
        "reviewer_verdict",
        "failure_category",
        "notes",
    }
)
_VALID_SELECTION_REASONS: Final[frozenset[str]] = frozenset(
    {
        "borderline",
        "stratified",
        "random",
        "tail",
        "shape_tail",
        "residual_sample",
    }
)


class QCReportError(ValueError):
    """Raised when a QC report input is malformed or inconsistent."""


@dataclass(frozen=True)
class _VerificationCase:
    cohort: Cohort
    patient_id: str
    status: str
    brain_voxel_fraction: float | None
    failure_categories: tuple[str, ...]


@dataclass(frozen=True)
class _ReviewRow:
    qc_key: str
    cohort: Cohort
    selection_reason: str
    brain_voxel_fraction: float | None
    verdict: str
    failure_category: str


def _read_json(path: Path, message: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QCReportError(message) from error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as error:
        raise QCReportError("QC report input could not be hashed") from error
    return digest.hexdigest()


def _atomic_json_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _float(value: object, *, allow_blank: bool) -> float | None:
    if value is None or (allow_blank and value == ""):
        return None
    if not isinstance(value, str | int | float):
        raise QCReportError("QC report contains a non-numeric metric")
    try:
        converted = float(value)
    except (TypeError, ValueError) as error:
        raise QCReportError("QC report contains a non-numeric metric") from error
    if not math.isfinite(converted):
        raise QCReportError("QC report contains a non-finite metric")
    return converted


def _cohort(value: object) -> Cohort:
    if not isinstance(value, str):
        raise QCReportError("QC report contains an invalid cohort")
    try:
        selected = Cohort(value)
    except ValueError as error:
        raise QCReportError("QC report contains an unsupported cohort") from error
    if selected not in {Cohort.UTSW, Cohort.UCSF_PDGM}:
        raise QCReportError("QC report supports only the Phase 04 cohorts")
    return selected


def _verification_case(raw_case: object) -> _VerificationCase:
    if not isinstance(raw_case, dict):
        raise QCReportError("preprocessing verification case is invalid")
    cohort = _cohort(raw_case.get("cohort"))
    patient_id = raw_case.get("patient_id")
    status = raw_case.get("status")
    if not isinstance(patient_id, str) or not patient_id:
        raise QCReportError("preprocessing verification case has invalid identity")
    if not isinstance(status, str):
        raise QCReportError("preprocessing verification case has invalid status")
    categories = raw_case.get("failure_categories", [])
    if not isinstance(categories, list) or not all(
        isinstance(category, str) for category in categories
    ):
        raise QCReportError("preprocessing verification failure categories are invalid")
    return _VerificationCase(
        cohort=cohort,
        patient_id=patient_id,
        status=status,
        brain_voxel_fraction=_float(
            raw_case.get("brain_voxel_fraction"), allow_blank=True
        ),
        failure_categories=tuple(categories),
    )


def _load_verification(path: Path) -> dict[tuple[Cohort, str], _VerificationCase]:
    payload = _read_json(path, "preprocessing verification cases could not be read")
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        raise QCReportError(
            "preprocessing verification cases must use schema version 2"
        )
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise QCReportError("preprocessing verification cases are missing cases")
    result: dict[tuple[Cohort, str], _VerificationCase] = {}
    for raw_case in raw_cases:
        case = _verification_case(raw_case)
        key = (case.cohort, case.patient_id)
        if key in result:
            raise QCReportError("preprocessing verification cases contain a duplicate")
        result[key] = case
    return result


def _load_review(path: Path) -> tuple[list[_ReviewRow], int]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if frozenset(reader.fieldnames or ()) != _REVIEW_COLUMNS:
                raise QCReportError("QC review sheet has an invalid header")
            rows: list[_ReviewRow] = []
            without_verdict = 0
            seen: set[str] = set()
            for raw_row in reader:
                key = raw_row.get("qc_key", "")
                if not key or key in seen:
                    raise QCReportError(
                        "QC review sheet has a missing or duplicate key"
                    )
                seen.add(key)
                verdict = raw_row.get("reviewer_verdict", "").strip().casefold()
                if not verdict:
                    without_verdict += 1
                elif verdict not in {"pass", "fail"}:
                    raise QCReportError("QC review sheet has an invalid verdict")
                selection_reason = raw_row.get("selection_reason", "")
                if selection_reason not in _VALID_SELECTION_REASONS:
                    raise QCReportError(
                        "QC review sheet has an invalid selection reason"
                    )
                rows.append(
                    _ReviewRow(
                        qc_key=key,
                        cohort=_cohort(raw_row.get("cohort")),
                        selection_reason=selection_reason,
                        brain_voxel_fraction=_float(
                            raw_row.get("brain_voxel_fraction"), allow_blank=True
                        ),
                        verdict=verdict,
                        failure_category=raw_row.get("failure_category", ""),
                    )
                )
    except OSError as error:
        raise QCReportError("QC review sheet could not be read") from error
    return rows, without_verdict


def _status_section(
    status_manifest: PreprocessingStatusManifest,
) -> dict[str, object]:
    summary = status_manifest.summary()
    raw_cohorts = summary.get("cohorts")
    if not isinstance(raw_cohorts, dict):
        raise QCReportError("status summary is malformed")
    result: dict[str, object] = {}
    for cohort_name, raw_summary in raw_cohorts.items():
        if not isinstance(raw_summary, dict):
            raise QCReportError("status summary has invalid cohort data")
        reasons: Counter[str] = Counter()
        for case in status_manifest.cases.values():
            if case.cohort == cohort_name:
                reasons.update(case.qc_reasons)
        section = dict(raw_summary)
        section["exclusions_by_qc_reason"] = dict(sorted(reasons.items()))
        result[cohort_name] = section
    return result


def _reviewed_counts(rows: list[_ReviewRow]) -> dict[str, object]:
    grouped: dict[str, Counter[tuple[str, str]]] = defaultdict(Counter)
    for row in rows:
        grouped[row.cohort.value][(row.selection_reason, row.verdict)] += 1
    result: dict[str, object] = {}
    for cohort in sorted(grouped):
        counts = grouped[cohort]
        result[cohort] = {
            "by_selection_reason_and_verdict": {
                reason: {
                    verdict: counts[(reason, verdict)]
                    for verdict in ("pass", "fail")
                    if counts[(reason, verdict)]
                }
                for reason in sorted({key[0] for key in counts})
            },
            "total": sum(counts.values()),
        }
    return result


def _agreement(
    rows: list[_ReviewRow],
    index: dict[str, tuple[Cohort, str]],
    verification: dict[tuple[Cohort, str], _VerificationCase],
) -> dict[str, object]:
    tables: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "automated_flagged__human_pass": 0,
            "automated_flagged__human_fail": 0,
            "automated_clear__human_pass": 0,
            "automated_clear__human_fail": 0,
        }
    )
    failures: dict[str, list[dict[str, object]]] = defaultdict(list)
    failures_flagged_at_original_bound: Counter[str] = Counter()
    joinable = 0
    for row in rows:
        indexed = index.get(row.qc_key)
        if indexed is None:
            continue
        indexed_cohort, patient_id = indexed
        case = verification.get((indexed_cohort, patient_id))
        if case is None:
            continue
        joinable += 1
        automated_flag = case.status in {"verified-borderline", "failed"}
        key = (
            ("automated_flagged" if automated_flag else "automated_clear")
            + "__human_"
            + row.verdict
        )
        tables[row.cohort.value][key] += 1
        if row.verdict == "fail":
            flagged_at_original_bound = (
                case.brain_voxel_fraction is not None
                and case.brain_voxel_fraction < _ORIGINAL_LOWER_BOUND
            )
            failures_flagged_at_original_bound[row.cohort.value] += int(
                flagged_at_original_bound
            )
            failures[row.cohort.value].append(
                {
                    "qc_key": row.qc_key,
                    "failure_category": row.failure_category,
                    "brain_voxel_fraction": case.brain_voxel_fraction,
                    "automated_flagged": automated_flag,
                    "flagged_at_original_bound": flagged_at_original_bound,
                }
            )
    return {
        "interpretation": (
            "The automated statuses shown are from the recalibrated D-031 screen "
            "and are therefore in-sample for the human failure that motivated "
            "recalibration. The reviewed sample was selected on the tails; these "
            "are counts, not sensitivity or specificity estimates."
        ),
        "joinable_reviewed_case_count": joinable,
        "by_cohort": {
            cohort: {
                "automated_flag_vs_human_verdict": dict(table),
                "human_failures": failures.get(cohort, []),
                "human_failures_flagged_at_original_bound": (
                    failures_flagged_at_original_bound.get(cohort, 0)
                ),
            }
            for cohort, table in sorted(tables.items())
        },
    }


def _sensitivity(
    verification: dict[tuple[Cohort, str], _VerificationCase], rows: list[_ReviewRow]
) -> dict[str, object]:
    all_by_cohort: dict[str, list[float]] = defaultdict(list)
    for case in verification.values():
        if case.brain_voxel_fraction is not None:
            all_by_cohort[case.cohort.value].append(case.brain_voxel_fraction)
    result: dict[str, object] = {}
    for bound in _BOUNDS:
        label = f"{bound:.2f}"
        result[label] = {
            "all_cases_below_by_cohort": {
                cohort: _below(values, bound)
                for cohort, values in sorted(all_by_cohort.items())
            },
            "reviewed_cases_below": {
                "pass": _reviewed_below(rows, bound, "pass"),
                "fail": _reviewed_below(rows, bound, "fail"),
            },
        }
    return {
        "candidate_lower_brain_fraction_bounds": result,
        "reviewed_case_count": len(rows),
    }


def _below(values: list[float], bound: float) -> int:
    return sum(value < bound for value in values)


def _reviewed_below(rows: list[_ReviewRow], bound: float, verdict: str) -> int:
    return sum(
        row.verdict == verdict
        and row.brain_voxel_fraction is not None
        and row.brain_voxel_fraction < bound
        for row in rows
    )


def _clopper_pearson_upper(failures: int, n: int) -> float | None:
    """Return the exact one-sided 95% binomial upper confidence bound."""

    if n < 0 or failures < 0 or failures > n:
        raise QCReportError("invalid binomial failure count")
    if n == 0:
        return None
    if failures == n:
        return 1.0
    if failures == 0:
        return 1.0 - math.pow(0.05, 1.0 / n)
    raw_upper = beta.ppf(0.95, failures + 1, n - failures)
    if isinstance(raw_upper, bool) or not isinstance(raw_upper, int | float):
        raise QCReportError("could not compute the binomial upper bound")
    upper = float(raw_upper)
    if not math.isfinite(upper):
        raise QCReportError("could not compute the binomial upper bound")
    return upper


def _residual_failure_rate(rows: list[_ReviewRow]) -> dict[str, object]:
    bound = _CURRENT_LOWER_BOUND
    residual_rows = [row for row in rows if row.selection_reason == "residual_sample"]
    all_random_rows = [
        row
        for row in rows
        if row.cohort is Cohort.UTSW
        and row.selection_reason in {"stratified", "random", "residual_sample"}
        and row.brain_voxel_fraction is not None
        and row.brain_voxel_fraction >= bound
    ]

    def counts(selected: list[_ReviewRow]) -> dict[str, object]:
        failures = sum(row.verdict == "fail" for row in selected)
        return {
            "n": len(selected),
            "failures": failures,
            "upper_95": _clopper_pearson_upper(failures, len(selected)),
        }

    return {
        "bound": bound,
        "residual_sample": counts(residual_rows),
        "all_random_above_bound": {
            "cohort_filter": "utsw",
            **counts(all_random_rows),
        },
        "interpretation": (
            "These are residual-risk estimates for Limitations, not thresholds. "
            "The all-random-above-bound group mixes designs (IDH-stratified "
            "random and residual random)."
        ),
    }


def _crosscheck_review(
    rows: list[_ReviewRow],
    index: dict[str, tuple[Cohort, str]],
    verification: dict[tuple[Cohort, str], _VerificationCase],
) -> int:
    mismatch_count = 0
    for row in rows:
        indexed = index.get(row.qc_key)
        if indexed is None:
            continue
        indexed_cohort, patient_id = indexed
        case = verification.get((indexed_cohort, patient_id))
        if case is None:
            continue
        fraction_matches = (
            row.brain_voxel_fraction is None and case.brain_voxel_fraction is None
        ) or (
            row.brain_voxel_fraction is not None
            and case.brain_voxel_fraction is not None
            and math.isclose(
                row.brain_voxel_fraction,
                case.brain_voxel_fraction,
                rel_tol=0,
                abs_tol=5e-8,
            )
        )
        mismatch_count += int(row.cohort is not indexed_cohort or not fraction_matches)
    return mismatch_count


def build_qc_report(
    *,
    status_path: Path,
    verification_path: Path,
    review_path: Path,
    overlay_index_path: Path,
    output_path: Path,
) -> dict[str, object]:
    """Build and atomically write the roster-free QC report."""

    status_manifest = PreprocessingStatusManifest.load(status_path)
    verification = _load_verification(verification_path)
    rows, without_verdict = _load_review(review_path)
    if without_verdict:
        raise QCReportError(
            f"QC review sheet contains {without_verdict} rows without a verdict"
        )
    try:
        loaded_index = load_qc_overlay_index(overlay_index_path)
    except ValueError as error:
        raise QCReportError("QC overlay index could not be read") from error
    index = dict(loaded_index)

    mismatch_count = _crosscheck_review(rows, index, verification)
    if mismatch_count:
        raise QCReportError(
            "QC review and verification cohort/fraction mismatch count: "
            f"{mismatch_count}"
        )

    status_section = _status_section(status_manifest)
    report: dict[str, object] = {
        "schema_version": 1,
        "cohorts": status_section,
        "reviewed_sample": _reviewed_counts(rows),
        "automated_vs_human_agreement": _agreement(rows, index, verification),
        "screen_bounds": {
            "original_lower_bound": _ORIGINAL_LOWER_BOUND,
            "current_lower_bound": _CURRENT_LOWER_BOUND,
            "provisional": True,
        },
        "threshold_sensitivity": _sensitivity(verification, rows),
        "residual_failure_rate": _residual_failure_rate(rows),
        "provenance": {
            "input_sha256": {
                "preprocessing_status": _sha256(status_path),
                "preprocessing_verification_cases": _sha256(verification_path),
                "qc_review_sheet": _sha256(review_path),
            },
            "reviewed_rows_without_verdict": without_verdict,
        },
    }
    _atomic_json_write(output_path, report)
    return report

"""Resumable per-case status tracking for the Phase 04 pipeline.

The manifest is an operational, raw-identifier-tier artifact.  It is written
to the configured private/manifests storage by the Phase 04 status script and
is never printed with patient-level detail.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, cast

from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.verification import CaseVerification

__all__ = [
    "CaseStatus",
    "PreprocessingStatusManifest",
    "StageRecord",
    "qc_reason",
]


StatusValue = Literal[
    "verified-passthrough",
    "verified-borderline",
    "failed",
    "not-run",
]
StageState = Literal["pending", "done", "failed"]
VisualQCState = Literal["not-required", "pending", "passed", "failed"]
CaseKey = tuple[str, str]

_SCHEMA_VERSION: Final[int] = 1
_STAGES: Final[tuple[str, ...]] = ("verify", "reorient", "n4")
_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    {"verified-passthrough", "verified-borderline", "failed", "not-run"}
)
_STAGE_STATES: Final[frozenset[str]] = frozenset({"pending", "done", "failed"})
_VISUAL_QC_STATES: Final[frozenset[str]] = frozenset(
    {"not-required", "pending", "passed", "failed"}
)
_QC_CATEGORIES: Final[tuple[str, ...]] = (
    "registration-failed",
    "skullstrip-over",
    "skullstrip-under",
    "n4-artifact",
    "orientation-wrong",
    "corrupt",
    "modality-mislabelled",
)
_QC_CATEGORY_SET: Final[frozenset[str]] = frozenset(_QC_CATEGORIES)
_COHORT_VALUES: Final[frozenset[str]] = frozenset(item.value for item in Cohort)


def qc_reason(category: str) -> str:
    """Return the D-028 exclusion reason for one Phase 04 category."""

    if not isinstance(category, str) or category not in _QC_CATEGORY_SET:
        raise ValueError(
            "unknown Phase 04 QC category; expected one of: "
            + ", ".join(_QC_CATEGORIES)
        )
    return f"qc:{category}"


def _validate_cohort(cohort: str) -> str:
    if not isinstance(cohort, str) or cohort not in _COHORT_VALUES:
        raise ValueError("unknown cohort")
    return cohort


def _validate_patient_id(patient_id: str) -> str:
    if not isinstance(patient_id, str) or not patient_id:
        raise ValueError("patient_id must be a non-empty string")
    return patient_id


def _validate_categories(categories: Iterable[str], *, field: str) -> tuple[str, ...]:
    values = tuple(categories)
    if any(not isinstance(category, str) for category in values):
        raise ValueError(f"{field} must contain only strings")
    unknown = sorted(set(values) - _QC_CATEGORY_SET)
    if unknown:
        raise ValueError(f"unknown {field} category")
    if len(set(values)) != len(values):
        raise ValueError(f"{field} must not contain duplicates")
    return values


def _validate_stage_name(stage: str) -> str:
    if stage not in _STAGES:
        raise ValueError(
            "unknown preprocessing stage; expected verify, reorient, or n4"
        )
    return stage


@dataclass(frozen=True)
class StageRecord:
    """The resumable state of one preprocessing stage."""

    state: StageState
    cache_key: str | None = None

    def __post_init__(self) -> None:
        if self.state not in _STAGE_STATES:
            raise ValueError("unknown preprocessing stage state")
        if self.cache_key is not None and (
            not isinstance(self.cache_key, str) or not self.cache_key
        ):
            raise ValueError("cache_key must be a non-empty string or None")

    def to_dict(self) -> dict[str, str | None]:
        """Return the JSON-compatible representation."""

        return {"cache_key": self.cache_key, "state": self.state}


@dataclass(frozen=True)
class CaseStatus:
    """Status for one canonical patient in one cohort."""

    cohort: str
    patient_id: str
    verification_status: StatusValue
    failure_categories: tuple[str, ...]
    borderline_checks: tuple[str, ...]
    stages: Mapping[str, StageRecord]
    visual_qc: VisualQCState
    qc_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_cohort(self.cohort)
        _validate_patient_id(self.patient_id)
        if self.verification_status not in _STATUS_VALUES:
            raise ValueError("unknown verification status")
        _validate_categories(self.failure_categories, field="failure")
        if any(
            not isinstance(check, str) or not check for check in self.borderline_checks
        ):
            raise ValueError("borderline_checks must contain non-empty strings")
        if self.visual_qc not in _VISUAL_QC_STATES:
            raise ValueError("unknown visual-QC state")
        reasons = tuple(self.qc_reasons)
        valid_reasons = {qc_reason(category) for category in _QC_CATEGORIES}
        if any(reason not in valid_reasons for reason in reasons):
            raise ValueError("qc_reasons must use Phase 04 qc:* reason codes")
        if len(set(reasons)) != len(reasons):
            raise ValueError("qc_reasons must not contain duplicates")
        if self.visual_qc != "failed" and reasons:
            raise ValueError(
                "qc_reasons require a failed visual-QC or exclusion decision"
            )
        normalized_stages = dict(self.stages)
        if set(normalized_stages) != set(_STAGES):
            raise ValueError("stages must contain exactly verify, reorient, and n4")
        for stage, record in normalized_stages.items():
            _validate_stage_name(stage)
            if not isinstance(record, StageRecord):
                raise ValueError("stages must contain StageRecord values")
        object.__setattr__(self, "failure_categories", tuple(self.failure_categories))
        object.__setattr__(self, "borderline_checks", tuple(self.borderline_checks))
        object.__setattr__(self, "stages", normalized_stages)
        object.__setattr__(self, "qc_reasons", reasons)

    @property
    def key(self) -> CaseKey:
        """Return the manifest lookup key."""

        return (self.cohort, self.patient_id)

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic JSON-compatible case record."""

        return {
            "borderline_checks": list(self.borderline_checks),
            "cohort": self.cohort,
            "failure_categories": list(self.failure_categories),
            "patient_id": self.patient_id,
            "qc_reasons": list(self.qc_reasons),
            "stages": {stage: self.stages[stage].to_dict() for stage in _STAGES},
            "verification_status": self.verification_status,
            "visual_qc": self.visual_qc,
        }


def _cohort_value(cohort: Cohort | str) -> str:
    value = cohort.value if isinstance(cohort, Cohort) else cohort
    return _validate_cohort(value)


def _case_from_verification(result: CaseVerification) -> CaseStatus:
    status = result.status
    if status not in _STATUS_VALUES:
        raise ValueError("verification result has an unknown status")
    if status == "verified-borderline" or status == "failed":
        visual_qc: VisualQCState = "pending"
    else:
        visual_qc = "not-required"
    stages = {
        "verify": StageRecord("done"),
        "reorient": StageRecord("pending"),
        "n4": StageRecord("pending"),
    }
    return CaseStatus(
        cohort=_cohort_value(result.cohort),
        patient_id=result.patient_id,
        verification_status=cast(StatusValue, status),
        failure_categories=tuple(result.failure_categories),
        borderline_checks=tuple(result.borderline_checks),
        stages=stages,
        visual_qc=visual_qc,
        qc_reasons=(),
    )


def _categories_argument(category: str | Sequence[str] | None) -> tuple[str, ...]:
    if category is None:
        values: tuple[str, ...] = ()
    elif isinstance(category, str):
        values = (category,)
    else:
        values = tuple(category)
    return _validate_categories(values, field="QC")


@dataclass(frozen=True)
class PreprocessingStatusManifest:
    """Immutable in-memory representation of the Phase 04 status manifest."""

    cases: Mapping[CaseKey, CaseStatus]

    def __post_init__(self) -> None:
        normalized: dict[CaseKey, CaseStatus] = {}
        for key, case in self.cases.items():
            if not isinstance(key, tuple) or len(key) != 2:
                raise ValueError("case keys must be (cohort, patient_id) tuples")
            if not isinstance(case, CaseStatus) or case.key != key:
                raise ValueError("case key does not match CaseStatus")
            normalized[key] = case
        object.__setattr__(self, "cases", normalized)

    @classmethod
    def from_verification(
        cls, results: Sequence[CaseVerification]
    ) -> PreprocessingStatusManifest:
        """Build a manifest from one verification run."""

        cases: dict[CaseKey, CaseStatus] = {}
        for result in results:
            case = _case_from_verification(result)
            if case.key in cases:
                raise ValueError("verification results contain a duplicate case")
            cases[case.key] = case
        return cls(cases)

    def _with_case(self, case: CaseStatus) -> PreprocessingStatusManifest:
        updated = dict(self.cases)
        if case.key not in updated:
            raise KeyError("case is not present in the status manifest")
        updated[case.key] = case
        return type(self)(updated)

    def _case(self, cohort: Cohort | str, patient_id: str) -> CaseStatus:
        key = (_cohort_value(cohort), _validate_patient_id(patient_id))
        try:
            return self.cases[key]
        except KeyError as error:
            raise KeyError("case is not present in the status manifest") from error

    def update_stage(
        self,
        cohort: Cohort | str,
        patient_id: str,
        stage: str,
        state: StageState,
        cache_key: str | None = None,
    ) -> PreprocessingStatusManifest:
        """Return a copy with one stage record updated."""

        _validate_stage_name(stage)
        case = self._case(cohort, patient_id)
        stages = dict(case.stages)
        stages[stage] = StageRecord(state, cache_key)
        return self._with_case(
            CaseStatus(
                cohort=case.cohort,
                patient_id=case.patient_id,
                verification_status=case.verification_status,
                failure_categories=case.failure_categories,
                borderline_checks=case.borderline_checks,
                stages=stages,
                visual_qc=case.visual_qc,
                qc_reasons=case.qc_reasons,
            )
        )

    def pending_cases(self, stage: str) -> tuple[CaseStatus, ...]:
        """Return cases whose stage is not complete, in deterministic order."""

        _validate_stage_name(stage)
        return tuple(
            case
            for _, case in sorted(self.cases.items())
            if case.stages[stage].state != "done"
        )

    def merge_verification(
        self, results: Sequence[CaseVerification]
    ) -> PreprocessingStatusManifest:
        """Refresh verification fields while retaining valid stage records.

        Human QC decisions are tied to the verification outcome they judged.
        If verification status, failure categories, and borderline checks are
        all unchanged, the previous visual-QC verdict and reasons survive an
        idempotent refresh.  If any of those fields changes, the previous
        verdict no longer describes the refreshed result, so visual QC is
        reset to the state computed for that result and its reasons are
        cleared.  Stage records always survive because their cache keys cover
        the stages' own invalidation.
        """

        updated = dict(self.cases)
        seen: set[CaseKey] = set()
        for result in results:
            refreshed = _case_from_verification(result)
            if refreshed.key in seen:
                raise ValueError("verification results contain a duplicate case")
            seen.add(refreshed.key)
            previous = updated.get(refreshed.key)
            if previous is None:
                updated[refreshed.key] = refreshed
                continue
            verification_unchanged = (
                previous.verification_status == refreshed.verification_status
                and previous.failure_categories == refreshed.failure_categories
                and previous.borderline_checks == refreshed.borderline_checks
            )
            updated[refreshed.key] = CaseStatus(
                cohort=refreshed.cohort,
                patient_id=refreshed.patient_id,
                verification_status=refreshed.verification_status,
                failure_categories=refreshed.failure_categories,
                borderline_checks=refreshed.borderline_checks,
                stages=previous.stages,
                visual_qc=(
                    previous.visual_qc
                    if verification_unchanged
                    else refreshed.visual_qc
                ),
                qc_reasons=(previous.qc_reasons if verification_unchanged else ()),
            )
        return type(self)(updated)

    def record_visual_qc_verdict(
        self,
        cohort: Cohort | str,
        patient_id: str,
        verdict: Literal["passed", "failed"],
        category: str | Sequence[str] | None = None,
    ) -> PreprocessingStatusManifest:
        """Record a human QC verdict; failed verdicts require categories."""

        categories = _categories_argument(category)
        if verdict not in {"passed", "failed"}:
            raise ValueError("visual-QC verdict must be passed or failed")
        if verdict == "passed" and categories:
            raise ValueError("a passed visual-QC verdict cannot have QC categories")
        if verdict == "failed" and not categories:
            raise ValueError("a failed visual-QC verdict requires a QC category")
        case = self._case(cohort, patient_id)
        reasons = tuple(qc_reason(item) for item in categories)
        return self._with_case(
            CaseStatus(
                cohort=case.cohort,
                patient_id=case.patient_id,
                verification_status=case.verification_status,
                failure_categories=case.failure_categories,
                borderline_checks=case.borderline_checks,
                stages=case.stages,
                visual_qc=verdict,
                qc_reasons=reasons,
            )
        )

    def record_exclusion(
        self,
        cohort: Cohort | str,
        patient_id: str,
        category: str | Sequence[str],
    ) -> PreprocessingStatusManifest:
        """Record an explicit individual exclusion with one or more QC reasons."""

        categories = _categories_argument(category)
        if not categories:
            raise ValueError("an exclusion requires a QC category")
        case = self._case(cohort, patient_id)
        return self._with_case(
            CaseStatus(
                cohort=case.cohort,
                patient_id=case.patient_id,
                verification_status=case.verification_status,
                failure_categories=case.failure_categories,
                borderline_checks=case.borderline_checks,
                stages=case.stages,
                visual_qc="failed",
                qc_reasons=tuple(qc_reason(item) for item in categories),
            )
        )

    def summary(self) -> dict[str, object]:
        """Return aggregate-only counts and the Phase 04 stop flag."""

        grouped: dict[str, list[CaseStatus]] = {}
        for case in self.cases.values():
            grouped.setdefault(case.cohort, []).append(case)
        cohort_summaries: dict[str, object] = {}
        for cohort in sorted(grouped):
            cases = grouped[cohort]
            total = len(cases)
            verification_counts = {
                status: sum(case.verification_status == status for case in cases)
                for status in sorted(_STATUS_VALUES)
            }
            failure_counts = {
                category: sum(category in case.failure_categories for case in cases)
                for category in _QC_CATEGORIES
            }
            visual_counts = {
                state: sum(case.visual_qc == state for case in cases)
                for state in sorted(_VISUAL_QC_STATES)
            }
            automated_failures = verification_counts["failed"]
            exclusions = sum(bool(case.qc_reasons) for case in cases)
            automated_rate = automated_failures / total if total else 0.0
            exclusion_rate = exclusions / total if total else 0.0
            cohort_summaries[cohort] = {
                "automated_failure_rate": automated_rate,
                "borderline_count": verification_counts["verified-borderline"],
                "exceeds_stop_threshold": automated_rate > 0.10
                or exclusion_rate > 0.10,
                "failure_counts_by_category": failure_counts,
                "post_decision_exclusion_rate": exclusion_rate,
                "total": total,
                "verification_status_counts": verification_counts,
                "visual_qc_counts": visual_counts,
            }
        return {"cohorts": cohort_summaries}

    def _serialized(self) -> dict[str, object]:
        return {
            "cases": [
                case.to_dict()
                for _, case in sorted(self.cases.items(), key=lambda item: item[0])
            ],
            "schema_version": _SCHEMA_VERSION,
        }

    def save(self, path: Path) -> None:
        """Atomically save the manifest beside the destination file."""

        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                json.dump(
                    self._serialized(),
                    handle,
                    ensure_ascii=True,
                    indent=2,
                    sort_keys=True,
                )
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_path, destination)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass

    @classmethod
    def load(cls, path: Path) -> PreprocessingStatusManifest:
        """Load and validate a saved manifest without exposing its path in errors."""

        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(
                "preprocessing status manifest could not be read"
            ) from error
        if not isinstance(payload, dict):
            raise ValueError("preprocessing status manifest must be a JSON object")
        if payload.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("unsupported preprocessing status schema version")
        raw_cases = payload.get("cases")
        if not isinstance(raw_cases, list):
            raise ValueError("preprocessing status cases must be an array")
        cases: dict[CaseKey, CaseStatus] = {}
        for raw_case in raw_cases:
            if not isinstance(raw_case, dict):
                raise ValueError("preprocessing status case must be an object")
            try:
                cohort = raw_case["cohort"]
                patient_id = raw_case["patient_id"]
                raw_stages = raw_case["stages"]
                if not isinstance(raw_stages, dict):
                    raise ValueError("stages must be an object")
                if set(raw_stages) != set(_STAGES):
                    raise ValueError(
                        "stages must contain exactly verify, reorient, and n4"
                    )
                stages: dict[str, StageRecord] = {}
                for stage in _STAGES:
                    raw_stage = raw_stages[stage]
                    if not isinstance(raw_stage, dict):
                        raise ValueError("stage record must be an object")
                    stages[stage] = StageRecord(
                        state=raw_stage["state"],
                        cache_key=raw_stage.get("cache_key"),
                    )
                case = CaseStatus(
                    cohort=cohort,
                    patient_id=patient_id,
                    verification_status=raw_case["verification_status"],
                    failure_categories=tuple(raw_case["failure_categories"]),
                    borderline_checks=tuple(raw_case["borderline_checks"]),
                    stages=stages,
                    visual_qc=raw_case["visual_qc"],
                    qc_reasons=tuple(raw_case["qc_reasons"]),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"invalid preprocessing status case: {error}"
                ) from error
            if case.key in cases:
                raise ValueError("preprocessing status contains a duplicate case")
            cases[case.key] = case
        return cls(cases)

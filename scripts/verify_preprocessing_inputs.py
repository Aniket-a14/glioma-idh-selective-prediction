#!/usr/bin/env python3
"""Verify retained Phase 04 preprocessing inputs and write two reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.cohort_manifest import (  # noqa: E402
    build_real_retained_rosters,
)
from glioma_selective.preprocessing.discovery import (  # noqa: E402
    discover_cases,
)
from glioma_selective.preprocessing.verification import (  # noqa: E402
    CaseVerification,
    ExpectedGrid,
    SegmentationFinding,
    VerificationCheck,
    VerificationThresholds,
    build_verification_report,
    verify_case,
)
from glioma_selective.utils import paths  # noqa: E402


def _serialize_check(check: VerificationCheck) -> dict[str, object]:
    """Serialize a check without adding paths or exception details."""

    return {
        "passed": check.passed,
        "measured": check.measured,
        "failure_category": check.failure_category,
        "borderline": check.borderline,
    }


def _serialize_segmentation_finding(
    finding: SegmentationFinding,
) -> dict[str, object]:
    """Serialize one segmentation finding without paths or exceptions."""

    return {
        "readable": finding.readable,
        "empty": finding.empty,
        "grid_matches_t1ce": finding.grid_matches_t1ce,
        "inside_brain_fraction": finding.inside_brain_fraction,
        "dice_self": finding.dice_self,
    }


def _serialize_case(result: CaseVerification) -> dict[str, object]:
    """Serialize raw-identifier-tier case output for private storage."""

    return {
        "cohort": result.cohort.value,
        "patient_id": result.patient_id,
        "status": result.status,
        "failure_categories": list(result.failure_categories),
        "borderline_checks": list(result.borderline_checks),
        "brain_voxel_fraction": result.brain_voxel_fraction,
        "cross_sequence_dice": dict(result.cross_sequence_dice),
        "segmentation_findings": {
            role: _serialize_segmentation_finding(finding)
            for role, finding in sorted(result.segmentation_findings.items())
        },
        "checks": {
            name: _serialize_check(check)
            for name, check in sorted(result.checks.items())
        },
    }


def _json_default(value: object) -> object:
    """Convert NumPy scalar values without permitting arbitrary objects."""

    item = getattr(value, "item", None)
    if callable(item):
        return item()
    raise TypeError(f"unsupported report value type: {type(value).__name__}")


def main() -> int:
    """Verify retained UTSW and UCSF-PDGM cases in deterministic order."""

    try:
        retained_rosters = build_real_retained_rosters()
        cases = tuple(
            case
            for cohort in sorted(retained_rosters, key=lambda item: item.value)
            for case in discover_cases(
                cohort,
                retained_patient_ids=retained_rosters[cohort],
            )
        )
        cases = tuple(
            sorted(cases, key=lambda case: (case.cohort.value, case.patient_id))
        )
        expected = ExpectedGrid()
        thresholds = VerificationThresholds()
        results: list[CaseVerification] = []
        total = len(cases)
        for index, case in enumerate(cases, start=1):
            results.append(verify_case(case, expected, thresholds))
            if index == total or index % 25 == 0:
                print(f"verified {index}/{total} cases", flush=True)

        aggregate_report = build_verification_report(results)
        private_report = {
            "schema_version": aggregate_report["schema_version"],
            "cases": [_serialize_case(result) for result in results],
        }
        aggregate_path = (
            paths.manifests_dir() / "preprocessing_verification_report.json"
        )
        private_path = (
            paths.private_data_dir() / "preprocessing_verification_cases.json"
        )
        aggregate_path.parent.mkdir(parents=True, exist_ok=True)
        private_path.parent.mkdir(parents=True, exist_ok=True)
        aggregate_path.write_text(
            json.dumps(
                aggregate_report,
                indent=2,
                sort_keys=True,
                default=_json_default,
            )
            + "\n",
            encoding="utf-8",
        )
        private_path.write_text(
            json.dumps(
                private_report,
                indent=2,
                sort_keys=True,
                default=_json_default,
            )
            + "\n",
            encoding="utf-8",
        )
    except (OSError, RuntimeError, ValueError, TypeError):
        print("verify_preprocessing_inputs.py: verification failed", file=sys.stderr)
        return 1

    print(json.dumps(aggregate_report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

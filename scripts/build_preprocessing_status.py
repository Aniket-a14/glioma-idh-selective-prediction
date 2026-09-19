#!/usr/bin/env python3
"""Build the resumable Phase 04 per-case status manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.id_normalization import Cohort  # noqa: E402
from glioma_selective.preprocessing.status import (  # noqa: E402
    PreprocessingStatusManifest,
)
from glioma_selective.preprocessing.verification import (  # noqa: E402
    CaseVerification,
    FailureCategory,
)
from glioma_selective.utils import paths  # noqa: E402


def _read_verification_results(source: Path) -> tuple[CaseVerification, ...]:
    """Read schema-2 private verification cases without printing their IDs."""

    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("verification input could not be read") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 2:
        raise ValueError("verification input must use schema version 2")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("verification input cases must be an array")

    results: list[CaseVerification] = []
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise ValueError("verification input case must be an object")
        cohort_value = raw_case.get("cohort")
        patient_id = raw_case.get("patient_id")
        status = raw_case.get("status")
        failure_categories = raw_case.get("failure_categories")
        borderline_checks = raw_case.get("borderline_checks")
        if not isinstance(cohort_value, str) or not isinstance(patient_id, str):
            raise ValueError("verification input case has invalid identity fields")
        if not isinstance(status, str):
            raise ValueError("verification input case has an invalid status")
        if not isinstance(failure_categories, list) or not all(
            isinstance(category, str) for category in failure_categories
        ):
            raise ValueError("verification input case has invalid failure categories")
        if not isinstance(borderline_checks, list) or not all(
            isinstance(check, str) for check in borderline_checks
        ):
            raise ValueError("verification input case has invalid borderline checks")
        try:
            cohort = Cohort(cohort_value)
        except ValueError as error:
            raise ValueError("verification input case has an unknown cohort") from error
        results.append(
            CaseVerification(
                cohort=cohort,
                patient_id=patient_id,
                status=status,
                checks={},
                failure_categories=cast(
                    tuple[FailureCategory, ...], tuple(failure_categories)
                ),
                borderline_checks=tuple(borderline_checks),
                brain_voxel_fraction=None,
                cross_sequence_dice={},
                segmentation_findings={},
            )
        )
    return tuple(results)


def main() -> int:
    """Build or merge the status artifact and print only aggregate counts."""

    try:
        source = paths.private_data_dir() / "preprocessing_verification_cases.json"
        destination = paths.manifests_dir() / "preprocessing_status.json"
        results = _read_verification_results(source)
        if destination.exists():
            manifest = PreprocessingStatusManifest.load(destination).merge_verification(
                results
            )
        else:
            manifest = PreprocessingStatusManifest.from_verification(results)
        manifest.save(destination)
        print(json.dumps(manifest.summary(), indent=2, sort_keys=True))
    except (OSError, RuntimeError, TypeError, ValueError):
        print(
            "build_preprocessing_status.py: status manifest build failed",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Phase 04 preprocessing: input discovery, verification, and the stage cache.

``registration``, ``resample`` and ``skullstrip`` (which pull in SimpleITK and
wrap HD-BET) are imported as submodules where needed, not re-exported here.
"""

from glioma_selective.preprocessing.cache import StageCache, hash_file, stage_cache_key
from glioma_selective.preprocessing.discovery import (
    CaseRecord,
    VolumeGeometry,
    build_geometry_report,
    discover_cases,
    inspect_volume_geometry,
)
from glioma_selective.preprocessing.verification import (
    CaseVerification,
    ExpectedGrid,
    SegmentationFinding,
    VerificationCheck,
    VerificationThresholds,
    build_verification_report,
    verify_case,
)

__all__ = [
    "CaseRecord",
    "CaseVerification",
    "ExpectedGrid",
    "SegmentationFinding",
    "StageCache",
    "VerificationCheck",
    "VerificationThresholds",
    "VolumeGeometry",
    "build_geometry_report",
    "build_verification_report",
    "discover_cases",
    "hash_file",
    "inspect_volume_geometry",
    "stage_cache_key",
    "verify_case",
]

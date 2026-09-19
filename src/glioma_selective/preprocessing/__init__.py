"""Phase 04 preprocessing: input discovery, verification, and the stage cache.

``registration``, ``resample``, ``reorient``, ``n4`` and ``skullstrip`` (SimpleITK /
HD-BET) and ``qc_overlays`` (matplotlib) are imported as submodules where needed,
not re-exported here.
"""

from glioma_selective.preprocessing.cache import StageCache, hash_file, stage_cache_key
from glioma_selective.preprocessing.discovery import (
    CaseRecord,
    VolumeGeometry,
    build_geometry_report,
    discover_cases,
    inspect_volume_geometry,
)
from glioma_selective.preprocessing.masks import (
    BRATS_TO_CLASS,
    SegmentationTarget,
    build_mask_report,
    inspect_segmentation_target,
    remap_labels,
    run_mask_stage,
    select_segmentation_file,
)
from glioma_selective.preprocessing.status import (
    CaseStatus,
    PreprocessingStatusManifest,
    StageRecord,
    qc_reason,
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
    "BRATS_TO_CLASS",
    "CaseRecord",
    "CaseStatus",
    "CaseVerification",
    "ExpectedGrid",
    "PreprocessingStatusManifest",
    "SegmentationFinding",
    "SegmentationTarget",
    "StageCache",
    "StageRecord",
    "VerificationCheck",
    "VerificationThresholds",
    "VolumeGeometry",
    "build_geometry_report",
    "build_mask_report",
    "build_verification_report",
    "discover_cases",
    "hash_file",
    "inspect_segmentation_target",
    "inspect_volume_geometry",
    "qc_reason",
    "remap_labels",
    "run_mask_stage",
    "select_segmentation_file",
    "stage_cache_key",
    "verify_case",
]

"""Preprocessing input discovery and header-only volume inspection."""

from glioma_selective.preprocessing.discovery import (
    CaseRecord,
    VolumeGeometry,
    build_geometry_report,
    discover_cases,
    inspect_volume_geometry,
)

__all__ = [
    "CaseRecord",
    "VolumeGeometry",
    "build_geometry_report",
    "discover_cases",
    "inspect_volume_geometry",
]

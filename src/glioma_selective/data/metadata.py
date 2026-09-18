"""Count literal clinical-metadata values without interpreting labels.

The report produced here is an aggregate verification artifact.  It keeps
empty fields and textual missing-value markers as distinct categories, so a
later task can decide how (or whether) those values should be harmonized.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from glioma_selective.utils import paths

__all__ = [
    "MetadataFileSpec",
    "build_label_count_report",
    "count_metadata_file",
    "default_metadata_specs",
    "write_label_count_report",
]


_UNLABELED_MARKERS = frozenset({"", "na", "n/a"})


@dataclass(frozen=True)
class MetadataFileSpec:
    """Describe one cohort metadata file and its literal marker columns."""

    cohort: str
    path: Path
    delimiter: str
    identifier_column: str
    marker_columns: Mapping[str, str]
    notes: tuple[str, ...] = ()


def default_metadata_specs() -> tuple[MetadataFileSpec, ...]:
    """Return the UTSW-Glioma and UCSF-PDGM specs via the path abstraction."""
    return (
        MetadataFileSpec(
            cohort="UTSW-Glioma",
            path=paths.raw_data_dir() / "UTSW_Glioma_Metadata-2-1.tsv",
            delimiter="\t",
            identifier_column="Subject ID",
            marker_columns={
                "IDH": "IDH",
                "1p/19q": "1p19Q CODEL",
                "MGMT": "MGMT",
            },
        ),
        MetadataFileSpec(
            cohort="UCSF-PDGM",
            path=paths.external_data_dir() / "UCSF-PDGM-metadata_v2.csv",
            delimiter=",",
            identifier_column="ID",
            marker_columns={
                "IDH": "IDH",
                "1p/19q": "1p/19q",
                "MGMT": "MGMT status",
            },
            notes=(
                "Raw metadata IDs use three-digit padding while imaging folders "
                "use four-digit padding; ID reconciliation is deferred to T03.1 "
                "and T03.3.",
            ),
        ),
    )


def _is_unlabeled(value: str) -> bool:
    """Identify only blank/explicit-NA cells for row-level reporting."""
    return value.strip().casefold() in _UNLABELED_MARKERS


def count_metadata_file(
    spec: MetadataFileSpec,
) -> dict[str, object]:
    """Count every literal marker value in one metadata file.

    ``source_row`` values are one-based physical file rows, including the
    header as row 1.  They are recorded only for blank/explicit-NA cells and
    never paired with patient identifiers.

    Raises:
        FileNotFoundError: if the configured metadata file is absent.
        ValueError: if the delimiter is invalid or a required column is
            missing, or if a required marker cell is structurally absent.
    """
    if len(spec.delimiter) != 1:
        raise ValueError("Metadata delimiters must be one character")

    counts: dict[str, Counter[str]] = {
        marker: Counter() for marker in spec.marker_columns
    }
    unlabeled_rows: dict[str, list[int]] = {
        marker: [] for marker in spec.marker_columns
    }

    with spec.path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=spec.delimiter)
        fieldnames = reader.fieldnames or []
        required_columns = (spec.identifier_column, *spec.marker_columns.values())
        missing_columns = [
            column for column in required_columns if column not in fieldnames
        ]
        if missing_columns:
            raise ValueError(
                f"{spec.path.name} is missing required columns: "
                f"{', '.join(missing_columns)}"
            )

        row_count = 0
        for row in reader:
            row_count += 1
            source_row = reader.line_num
            for marker, column in spec.marker_columns.items():
                value = row[column]
                if value is None:
                    raise ValueError(
                        f"{spec.path.name} has no cell for {column!r} "
                        f"at source row {source_row}"
                    )
                counts[marker][value] += 1
                if marker == "IDH" and _is_unlabeled(value):
                    unlabeled_rows[marker].append(source_row)

    marker_reports: dict[str, dict[str, object]] = {
        marker: {
            "source_column": column,
            "category_counts": dict(sorted(counts[marker].items())),
        }
        for marker, column in spec.marker_columns.items()
    }
    if "IDH" in marker_reports:
        marker_reports["IDH"]["unlabeled_source_rows"] = unlabeled_rows["IDH"]
    report: dict[str, object] = {
        "cohort": spec.cohort,
        "source_file": spec.path.name,
        "row_count": row_count,
        "markers": marker_reports,
    }
    if spec.notes:
        report["notes"] = list(spec.notes)
    return report


def build_label_count_report(
    specs: Sequence[MetadataFileSpec] | None = None,
) -> dict[str, object]:
    """Build the aggregate per-cohort, per-marker verification report."""
    selected_specs = tuple(specs) if specs is not None else default_metadata_specs()
    return {
        "report_version": 1,
        "cohorts": [count_metadata_file(spec) for spec in selected_specs],
    }


def write_label_count_report(
    output_path: Path | None = None,
    specs: Sequence[MetadataFileSpec] | None = None,
) -> Path:
    """Write the JSON report, defaulting to ``paths.manifests_dir()``."""
    destination = (
        output_path
        if output_path is not None
        else paths.manifests_dir() / "label_verification.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(build_label_count_report(specs), handle, indent=2)
        handle.write("\n")
    return destination


def main() -> None:
    """Generate the default report under the configured manifests directory."""
    print(write_label_count_report())


if __name__ == "__main__":
    main()

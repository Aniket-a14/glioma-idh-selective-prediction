"""Synthetic tests for literal clinical-metadata counting."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from glioma_selective.data.metadata import (
    MetadataFileSpec,
    count_metadata_file,
    write_label_count_report,
)

UTSW_COLUMNS = [
    "Subject ID",
    "Sex at birth",
    "Age at Imaging",
    "Race",
    "Ethnicity",
    "Tumor Type",
    "Pathology Information",
    "Tumor Grade",
    "IDH",
    "IDH_Testing Method",
    "1p19Q CODEL",
    "MGMT",
    "Operation Status",
    "T1",
    "T1GD",
    "T2",
    "T2FLAIR",
    "Scanner Make",
    "Scanner Model",
    "Scanner Strength",
    "Manually Refined Segmentation",
]

UCSF_COLUMNS = [
    "ID",
    "Sex",
    "Age at MRI",
    "WHO CNS Grade",
    "Final pathologic diagnosis (WHO 2021)",
    "MGMT status",
    "MGMT index",
    "1p/19q",
    "IDH",
    "1-dead 0-alive",
    "OS",
    "EOR",
    "Biopsy prior to imaging",
    "BraTS21 ID",
    "BraTS21 Segmentation Cohort",
    "BraTS21 MGMT Cohort",
]


def _write_delimited(
    path: Path, columns: list[str], rows: list[dict[str, str]], delimiter: str
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def test_utsw_counts_keep_blank_and_na_as_literal_categories(tmp_path: Path) -> None:
    metadata_path = tmp_path / "utsw.tsv"
    rows = [
        {
            "Subject ID": "fixture-a",
            "IDH": "mutated",
            "1p19Q CODEL": "co-deleted",
            "MGMT": "methylated",
        },
        {
            "Subject ID": "fixture-b",
            "IDH": "NA",
            "1p19Q CODEL": "NA",
            "MGMT": "",
        },
        {
            "Subject ID": "fixture-c",
            "IDH": "",
            "1p19Q CODEL": "non co-deleted",
            "MGMT": "unmethylated",
        },
    ]
    _write_delimited(metadata_path, UTSW_COLUMNS, rows, "\t")

    report = count_metadata_file(
        MetadataFileSpec(
            cohort="synthetic-UTSW",
            path=metadata_path,
            delimiter="\t",
            identifier_column="Subject ID",
            marker_columns={
                "IDH": "IDH",
                "1p/19q": "1p19Q CODEL",
                "MGMT": "MGMT",
            },
        )
    )

    assert report["row_count"] == 3
    markers = report["markers"]
    assert markers["IDH"]["category_counts"] == {"": 1, "NA": 1, "mutated": 1}
    assert markers["IDH"]["unlabeled_source_rows"] == [3, 4]
    assert markers["1p/19q"]["category_counts"] == {
        "NA": 1,
        "co-deleted": 1,
        "non co-deleted": 1,
    }
    assert markers["MGMT"]["category_counts"] == {
        "": 1,
        "methylated": 1,
        "unmethylated": 1,
    }


def test_ucsf_csv_counts_keep_distinct_idh_assay_values(tmp_path: Path) -> None:
    metadata_path = tmp_path / "ucsf.csv"
    rows = [
        {
            "ID": "fixture-a",
            "IDH": "wildtype",
            "1p/19q": "intact",
            "MGMT status": "negative",
        },
        {
            "ID": "fixture-b",
            "IDH": "mutated (NOS)",
            "1p/19q": "",
            "MGMT status": "positive",
        },
        {
            "ID": "fixture-c",
            "IDH": "IDH1 p.R132H",
            "1p/19q": "intact",
            "MGMT status": "indeterminate",
        },
    ]
    _write_delimited(metadata_path, UCSF_COLUMNS, rows, ",")

    report = count_metadata_file(
        MetadataFileSpec(
            cohort="synthetic-UCSF-PDGM",
            path=metadata_path,
            delimiter=",",
            identifier_column="ID",
            marker_columns={
                "IDH": "IDH",
                "1p/19q": "1p/19q",
                "MGMT": "MGMT status",
            },
        )
    )

    markers = report["markers"]
    assert markers["IDH"]["category_counts"] == {
        "IDH1 p.R132H": 1,
        "mutated (NOS)": 1,
        "wildtype": 1,
    }
    assert markers["1p/19q"]["category_counts"] == {"": 1, "intact": 2}
    assert markers["MGMT"]["category_counts"] == {
        "indeterminate": 1,
        "negative": 1,
        "positive": 1,
    }


def test_missing_required_column_is_rejected(tmp_path: Path) -> None:
    metadata_path = tmp_path / "missing.tsv"
    _write_delimited(
        metadata_path,
        ["Subject ID", "IDH"],
        [{"Subject ID": "fixture-a", "IDH": "NA"}],
        "\t",
    )

    with pytest.raises(ValueError, match="missing required columns"):
        count_metadata_file(
            MetadataFileSpec(
                cohort="synthetic",
                path=metadata_path,
                delimiter="\t",
                identifier_column="Subject ID",
                marker_columns={"IDH": "IDH", "MGMT": "MGMT"},
            )
        )


def test_report_defaults_to_the_manifests_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GLIOMA_DATA_ROOT", str(tmp_path / "data"))
    metadata_path = tmp_path / "synthetic.tsv"
    _write_delimited(
        metadata_path,
        ["Subject ID", "IDH"],
        [{"Subject ID": "fixture-a", "IDH": "mutated"}],
        "\t",
    )

    destination = write_label_count_report(
        specs=[
            MetadataFileSpec(
                cohort="synthetic",
                path=metadata_path,
                delimiter="\t",
                identifier_column="Subject ID",
                marker_columns={"IDH": "IDH"},
            )
        ]
    )

    assert destination == tmp_path / "data" / "manifests" / "label_verification.json"
    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["cohorts"][0]["markers"]["IDH"]["category_counts"] == {"mutated": 1}

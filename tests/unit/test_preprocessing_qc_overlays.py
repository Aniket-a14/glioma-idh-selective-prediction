"""Synthetic tests for the Phase 04 visual-QC sampler and overlays."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort
from glioma_selective.preprocessing.discovery import CaseRecord
from glioma_selective.preprocessing.qc_overlays import (
    QCOverlayError,
    QCSelection,
    QCVerificationSummary,
    append_qc_overlay_index,
    append_qc_review_sheet,
    assign_continuing_qc_keys,
    load_qc_overlay_index,
    load_verification_cases,
    render_qc_overlay,
    review_sheet_has_tail,
    select_qc_sample,
    select_qc_tail,
    write_qc_overlay_index,
    write_qc_review_sheet,
)


def _write_volume(path: Path, values: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(values.astype(np.float32), np.eye(4)), path)


def _case(tmp_path: Path, *, empty_segmentation: bool = False) -> CaseRecord:
    shape = (16, 16, 16)
    brain = np.zeros(shape, dtype=np.float32)
    brain[3:13, 3:13, 3:13] = 1
    sequence_files: dict[CanonicalSequence, Path] = {}
    for offset, sequence in enumerate(CORE_SEQUENCES, start=1):
        values = brain * float(offset)
        path = tmp_path / f"{sequence.value}.nii.gz"
        _write_volume(path, values)
        sequence_files[sequence] = path
    segmentation = np.zeros(shape, dtype=np.float32)
    if not empty_segmentation:
        segmentation[7:10, 7:10, 7:10] = 1
        segmentation[8:10, 8:10, 8:10] = 2
        segmentation[9:11, 9:11, 9:11] = 4
    segmentation_path = tmp_path / "tumorseg_FeTS.nii.gz"
    _write_volume(segmentation_path, segmentation)
    return CaseRecord(
        cohort=Cohort.UTSW,
        patient_id="UTSW-BT0001",
        source_directory=tmp_path,
        sequence_files=sequence_files,
        geometries={},
        segmentation_files={"tumorseg_FeTS": segmentation_path},
    )


def _rosters() -> tuple[dict[Cohort, tuple[str, ...]], dict[str, str]]:
    utsw = tuple(f"UTSW-BT{index:04d}" for index in range(1, 31))
    ucsf = tuple(f"UCSF-PDGM-{index:04d}" for index in range(1, 31))
    labels = {
        patient_id: ("Mutated" if index <= 15 else "Wild type")
        for index, patient_id in enumerate(utsw, start=1)
    }
    return {Cohort.UTSW: utsw, Cohort.UCSF_PDGM: ucsf}, labels


def test_sample_is_deterministic_stratified_and_deduplicated() -> None:
    rosters, labels = _rosters()
    reader_calls: list[Cohort] = []

    def reader(cohort: Cohort, _metadata_path: Path) -> dict[str, str]:
        reader_calls.append(cohort)
        if cohort is Cohort.UCSF_PDGM:
            raise AssertionError("UCSF labels must not be requested")
        return labels

    borderline = QCSelection(
        cohort=Cohort.UTSW,
        patient_id="UTSW-BT0001",
        selection_reason="borderline",
    )
    first = select_qc_sample(
        retained_patient_ids=rosters,
        borderline_cases=(borderline,),
        label_reader=reader,
        utsw_metadata_path=Path("synthetic.tsv"),
    )
    second = select_qc_sample(
        retained_patient_ids=rosters,
        borderline_cases=(borderline,),
        label_reader=reader,
        utsw_metadata_path=Path("synthetic.tsv"),
    )

    assert first == second
    assert len(first) == 36  # The borderline case overlaps one stratified draw.
    assert len({(item.cohort, item.patient_id) for item in first}) == len(first)
    assert sum(item.cohort is Cohort.UCSF_PDGM for item in first) == 12
    assert sum("stratified" in item.selection_reasons for item in first) == 24
    assert sum(item.selection_reason == "borderline" for item in first) == 1
    assert reader_calls == [Cohort.UTSW, Cohort.UTSW]
    assert (
        next(
            item for item in first if item.patient_id == "UTSW-BT0001"
        ).selection_reason
        == "borderline"
    )


def test_borderline_private_records_are_loaded_and_schema_is_checked(
    tmp_path: Path,
) -> None:
    verification_path = tmp_path / "verification.json"
    verification_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "cases": [
                    {
                        "cohort": "utsw",
                        "patient_id": "UTSW-BT0001",
                        "status": "verified-borderline",
                        "brain_voxel_fraction": 0.2,
                        "cross_sequence_dice": {"T1": 0.99, "T2": 1.0},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    records = load_verification_cases(verification_path)
    assert records[(Cohort.UTSW, "UTSW-BT0001")] == QCVerificationSummary(0.2, 0.99)

    rosters, labels = _rosters()
    sample = select_qc_sample(
        retained_patient_ids=rosters,
        borderline_cases_path=verification_path,
        utsw_idh_labels=labels,
    )
    selected = next(item for item in sample if item.patient_id == "UTSW-BT0001")
    assert selected.selection_reason == "borderline"
    assert selected.selection_reasons == (
        "borderline",
        "stratified",
    ) or selected.selection_reasons == ("borderline",)


def test_overlay_renders_png_and_empty_segmentation_uses_brain_centroid(
    tmp_path: Path,
) -> None:
    case = _case(tmp_path / "nonempty")
    selection = QCSelection(Cohort.UTSW, "UTSW-BT0001", "stratified", qc_key="qc_0001")
    figure = render_qc_overlay(case, selection, QCVerificationSummary(0.244, 1.0))
    output = tmp_path / "qc_0001.png"
    try:
        figure.savefig(output, dpi=100, format="png")
    finally:
        import matplotlib.pyplot as plt

        plt.close(figure)
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert output.stat().st_size > 0

    empty_case = _case(tmp_path / "empty", empty_segmentation=True)
    empty_figure = render_qc_overlay(empty_case, selection)
    import matplotlib.pyplot as plt

    plt.close(empty_figure)


def test_missing_core_volume_error_contains_no_path(tmp_path: Path) -> None:
    case = _case(tmp_path)
    missing_path = case.sequence_files[CanonicalSequence.T2]
    missing_path.unlink()
    selection = QCSelection(Cohort.UTSW, "UTSW-BT0001", "random", qc_key="qc_0001")
    with pytest.raises(QCOverlayError, match="missing the T2 volume") as error:
        render_qc_overlay(case, selection)
    assert str(tmp_path) not in str(error.value)
    assert str(missing_path) not in str(error.value)


def test_output_names_and_review_sheet_do_not_contain_patient_id(
    tmp_path: Path,
) -> None:
    patient_id = "UTSW-BT0001"
    selection = QCSelection(Cohort.UTSW, patient_id, "borderline", qc_key="qc_0042")
    verification = {(Cohort.UTSW, patient_id): QCVerificationSummary(0.2, 0.98)}
    index_path = tmp_path / "private" / "qc_overlay_index.json"
    review_path = tmp_path / "figures" / "qc_review_sheet.csv"
    write_qc_overlay_index((selection,), index_path)
    write_qc_review_sheet((selection,), verification, review_path)

    assert index_path.read_text(encoding="utf-8").find(patient_id) >= 0
    assert patient_id not in review_path.read_text(encoding="utf-8")
    assert review_path.name == "qc_review_sheet.csv"
    with review_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["qc_key"] == "qc_0042"
    assert rows[0]["reviewer_verdict"] == ""
    assert rows[0]["failure_category"] == ""
    assert rows[0]["notes"] == ""


def _tail_fixture() -> tuple[
    dict[Cohort, tuple[str, ...]], dict[tuple[Cohort, str], QCVerificationSummary]
]:
    rosters = {
        Cohort.UTSW: tuple(f"UTSW-BT{index:04d}" for index in range(1, 5)),
        Cohort.UCSF_PDGM: tuple(f"UCSF-PDGM-{index:04d}" for index in range(1, 5)),
    }
    fractions = {
        Cohort.UTSW: (0.40, 0.10, 0.20, 0.30),
        Cohort.UCSF_PDGM: (0.35, 0.05, 0.25, 0.15),
    }
    verification = {
        (cohort, patient_id): QCVerificationSummary(fractions[cohort][index], 1.0)
        for cohort, patient_ids in rosters.items()
        for index, patient_id in enumerate(patient_ids)
    }
    return rosters, verification


def test_tail_selects_lowest_per_cohort_and_excludes_indexed_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rosters, verification = _tail_fixture()
    label_reader_calls: list[Cohort] = []

    def forbidden_label_reader(cohort: Cohort, _metadata_path: Path) -> dict[str, str]:
        label_reader_calls.append(cohort)
        raise AssertionError("tail sampling must not read labels")

    monkeypatch.setattr(
        "glioma_selective.preprocessing.qc_overlays.read_utsw_idh_labels",
        forbidden_label_reader,
    )
    selected = select_qc_tail(
        retained_patient_ids=rosters,
        verification=verification,
        indexed_cases=(
            (Cohort.UTSW, "UTSW-BT0002"),
            (Cohort.UCSF_PDGM, "UCSF-PDGM-0004"),
        ),
        per_cohort=2,
        seed=17,
    )
    assert {(item.cohort, item.patient_id) for item in selected} == {
        (Cohort.UTSW, "UTSW-BT0003"),
        (Cohort.UTSW, "UTSW-BT0004"),
        (Cohort.UCSF_PDGM, "UCSF-PDGM-0002"),
        (Cohort.UCSF_PDGM, "UCSF-PDGM-0003"),
    }
    assert all(item.selection_reason == "tail" for item in selected)
    assert label_reader_calls == []


def test_tail_append_preserves_review_bytes_index_values_and_existing_png(
    tmp_path: Path,
) -> None:
    rosters, verification = _tail_fixture()
    index_path = tmp_path / "private" / "qc_overlay_index.json"
    review_path = tmp_path / "figures" / "qc_review_sheet.csv"
    existing = (
        QCSelection(Cohort.UTSW, "UTSW-BT0001", "stratified", qc_key="qc_0001"),
        QCSelection(
            Cohort.UCSF_PDGM,
            "UCSF-PDGM-0001",
            "random",
            qc_key="qc_0002",
        ),
    )
    write_qc_overlay_index(existing, index_path)
    write_qc_review_sheet(existing, verification, review_path)
    review_path.write_bytes(
        review_path.read_bytes().replace(
            b",,,\r\n", b",pass,brain-retained,reviewed\r\n", 1
        )
    )
    existing_review_bytes = review_path.read_bytes()
    existing_index = load_qc_overlay_index(index_path)

    png_path = tmp_path / "figures" / "qc_0001.png"
    png_path.write_bytes(b"existing-png")
    png_before = (png_path.stat().st_mtime_ns, png_path.read_bytes())

    selected = select_qc_tail(
        retained_patient_ids=rosters,
        verification=verification,
        indexed_cases=existing_index.values(),
        per_cohort=1,
        seed=17,
    )
    assigned = assign_continuing_qc_keys(selected, existing_index)
    assert {item.qc_key for item in assigned} == {"qc_0003", "qc_0004"}
    append_qc_overlay_index(assigned, index_path)
    append_qc_review_sheet(assigned, verification, review_path)

    assert review_path.read_bytes().startswith(existing_review_bytes)
    merged_index = load_qc_overlay_index(index_path)
    assert all(merged_index[key] == value for key, value in existing_index.items())
    assert png_path.stat().st_mtime_ns == png_before[0]
    assert png_path.read_bytes() == png_before[1]

    assert review_sheet_has_tail(review_path)


def test_tail_zero_cli_is_a_noop(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    marker.write_bytes(b"unchanged")
    result = subprocess.run(
        [sys.executable, "scripts/make_qc_overlays.py", "--tail", "0"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert marker.read_bytes() == b"unchanged"

"""Unit tests for Phase 03 Task T03.1 identifier normalization."""

from __future__ import annotations

import pytest

from glioma_selective.leakage.id_normalization import (
    Cohort,
    IdentifierNormalizationError,
    normalize_brats2021_id,
    normalize_egd_id,
    normalize_identifier,
    normalize_tcga_gbm_id,
    normalize_tcga_lgg_id,
    normalize_ucsf_pdgm_id,
    normalize_utsw_id,
)


@pytest.mark.parametrize(
    ("raw_id", "expected"),
    [
        ("BT0001", "UTSW-BT0001"),
        ("bt-0001", "UTSW-BT0001"),
        ("UTSW_BT_0001", "UTSW-BT0001"),
        ("BT0002", "UTSW-BT0002"),
    ],
)
def test_utsw_case_padding_and_prefix_variants(raw_id: str, expected: str) -> None:
    assert normalize_utsw_id(raw_id) == expected


def test_ucsf_real_metadata_and_directory_padding_discrepancy() -> None:
    metadata_id = "UCSF-PDGM-004"
    directory_id = "UCSF-PDGM-0004_nifti"

    assert normalize_ucsf_pdgm_id(metadata_id) == "UCSF-PDGM-0004"
    assert normalize_ucsf_pdgm_id(directory_id) == "UCSF-PDGM-0004"


@pytest.mark.parametrize(
    ("raw_id", "expected"),
    [
        ("brats2021_00001", "BraTS2021_00001"),
        ("BRATS21-00001", "BraTS2021_00001"),
        ("BraTS-2021 00002", "BraTS2021_00002"),
    ],
)
def test_brats_case_prefix_and_separator_variants(raw_id: str, expected: str) -> None:
    assert normalize_brats2021_id(raw_id) == expected


@pytest.mark.parametrize(
    ("normalizer", "raw_id"),
    [
        (normalize_utsw_id, "BT0007"),
        (normalize_ucsf_pdgm_id, "UCSF-PDGM-007"),
        (normalize_brats2021_id, "BraTS21_00007"),
        (normalize_egd_id, "SYNTHETIC-EGD-0007"),
        (normalize_tcga_gbm_id, "SYNTHETIC-TCGA-GBM-0007"),
        (normalize_tcga_lgg_id, "SYNTHETIC-TCGA-LGG-0007"),
    ],
)
def test_normalization_is_idempotent(normalizer, raw_id: str) -> None:
    normalized = normalizer(raw_id)
    assert normalizer(normalized) == normalized


def test_different_known_patients_do_not_collide() -> None:
    for normalizer, raw_ids in (
        (normalize_utsw_id, ("BT0001", "BT0002")),
        (normalize_ucsf_pdgm_id, ("UCSF-PDGM-004", "UCSF-PDGM-005")),
        (normalize_brats2021_id, ("BraTS2021_00001", "BraTS2021_00002")),
    ):
        assert len({normalizer(raw_id) for raw_id in raw_ids}) == 2


def test_generic_unseen_cohort_normalization_does_not_pad_or_guess() -> None:
    assert normalize_egd_id("synthetic_egd_7") == "EGD-SYNTHETIC-EGD-7"
    assert normalize_tcga_gbm_id("synthetic tcga gbm 7") == (
        "TCGA-GBM-SYNTHETIC-TCGA-GBM-7"
    )
    assert normalize_tcga_lgg_id("synthetic_tcga_lgg_7") == (
        "TCGA-LGG-SYNTHETIC-TCGA-LGG-7"
    )


def test_dispatch_accepts_documented_cohort_aliases() -> None:
    assert normalize_identifier("bt-0001", "UTSW-Glioma") == "UTSW-BT0001"
    assert normalize_identifier("UCSF_PDGM_004", Cohort.UCSF_PDGM) == ("UCSF-PDGM-0004")


@pytest.mark.parametrize(
    ("normalizer", "raw_id"),
    [
        (normalize_utsw_id, "BT001"),
        (normalize_ucsf_pdgm_id, "UCSF-PDGM-04"),
        (normalize_brats2021_id, "BraTS2021_0001"),
        (normalize_egd_id, "SYNTHETIC/EGD/0001"),
    ],
)
def test_ambiguous_or_malformed_ids_fail_closed(normalizer, raw_id: str) -> None:
    with pytest.raises(IdentifierNormalizationError):
        normalizer(raw_id)

"""Normalize cohort identifiers before any overlap comparison.

The return values remain raw-identifier-tier values. They are canonical
spellings for matching within the audit, not private internal IDs and not
public pseudonyms. The raw spelling must be retained by the caller when an
overlap decision is recorded.

Only the UTSW-Glioma, UCSF-PDGM, and BraTS-2021 formats have been checked
against files currently available on this machine. EGD, TCGA-GBM, and
TCGA-LGG use a deliberately conservative generic normalizer until their real
inventories arrive; it changes case and separators only and does not guess a
padding or prefix rule.
"""

from __future__ import annotations

import re
from enum import StrEnum

__all__ = [
    "Cohort",
    "IdentifierNormalizationError",
    "normalize_brats2021_id",
    "normalize_egd_id",
    "normalize_identifier",
    "normalize_tcga_gbm_id",
    "normalize_tcga_lgg_id",
    "normalize_ucsf_pdgm_id",
    "normalize_utsw_id",
]


class Cohort(StrEnum):
    """Cohorts supported by the Phase 03 identifier audit."""

    UTSW = "utsw"
    UCSF_PDGM = "ucsf_pdgm"
    BRATS_2021 = "brats2021"
    EGD = "egd"
    TCGA_GBM = "tcga_gbm"
    TCGA_LGG = "tcga_lgg"


class IdentifierNormalizationError(ValueError):
    """Raised when an identifier is malformed or ambiguous for its cohort."""


_COHORT_ALIASES: dict[str, Cohort] = {
    "brats-2021": Cohort.BRATS_2021,
    "brats2021": Cohort.BRATS_2021,
    "egd": Cohort.EGD,
    "tcga-gbm": Cohort.TCGA_GBM,
    "tcga_gbm": Cohort.TCGA_GBM,
    "tcga-lgg": Cohort.TCGA_LGG,
    "tcga_lgg": Cohort.TCGA_LGG,
    "ucsf-pdgm": Cohort.UCSF_PDGM,
    "ucsf_pdgm": Cohort.UCSF_PDGM,
    "utsw": Cohort.UTSW,
    "utsw-glioma": Cohort.UTSW,
    "utsw_glioma": Cohort.UTSW,
}

_SEPARATOR_RE = re.compile(r"[-_\s]+")
_GENERIC_ID_RE = re.compile(r"[A-Z0-9]+(?:-[A-Z0-9]+)*")


def _coerce_cohort(cohort: Cohort | str) -> Cohort:
    if isinstance(cohort, Cohort):
        return cohort
    key = cohort.strip().lower()
    try:
        return _COHORT_ALIASES[key]
    except KeyError as error:
        raise IdentifierNormalizationError(
            f"unsupported cohort identifier: {cohort!r}"
        ) from error


def _normalized_separators(raw_id: str) -> str:
    if not isinstance(raw_id, str):
        raise IdentifierNormalizationError("raw identifier must be a string")
    value = raw_id.strip().upper()
    if not value:
        raise IdentifierNormalizationError("raw identifier must not be empty")
    return _SEPARATOR_RE.sub("-", value)


def normalize_utsw_id(raw_id: str) -> str:
    """Return the canonical UTSW form ``UTSW-BTNNNN``.

    UTSW-Glioma supplies a ``BT`` prefix and a fixed four-digit suffix. The
    optional ``UTSW`` cohort prefix and separator variations are formatting
    differences; a suffix with another width is rejected rather than padded,
    because the observed UTSW format is fixed-width.
    """
    value = _normalized_separators(raw_id)
    match = re.fullmatch(r"(?:UTSW-)?BT-?(\d{4})", value)
    if match is None:
        raise IdentifierNormalizationError(
            "UTSW identifiers must use BT plus a four-digit numeric suffix"
        )
    return f"UTSW-BT{match.group(1)}"


def normalize_ucsf_pdgm_id(raw_id: str) -> str:
    """Return the canonical UCSF-PDGM form ``UCSF-PDGM-NNNN``.

    The downloaded metadata uses three digits while patient directory names
    use four digits. Both widths are accepted and zero-padded to four digits;
    a directory suffix such as ``_nifti`` is also removed. Other widths are
    rejected so an unknown identifier cannot be silently merged.
    """
    value = raw_id.strip()
    value = re.sub(r"(?i)(?:-|_)nifti$", "", value)
    value = _normalized_separators(value)
    match = re.fullmatch(r"UCSF-PDGM-(\d{3}|\d{4})", value)
    if match is None:
        raise IdentifierNormalizationError(
            "UCSF-PDGM identifiers must use a three- or four-digit suffix"
        )
    return f"UCSF-PDGM-{match.group(1).zfill(4)}"


def normalize_brats2021_id(raw_id: str) -> str:
    """Return the canonical BraTS-2021 form ``BraTS2021_NNNNN``.

    ``BraTS21`` and separator/case variants are accepted. The observed
    mapping column uses a fixed five-digit suffix, so other widths are
    rejected instead of guessed.
    """
    value = _normalized_separators(raw_id)
    match = re.fullmatch(r"BRATS-?(?:2021|21)-(\d{5})", value)
    if match is None:
        raise IdentifierNormalizationError(
            "BraTS-2021 identifiers must use a five-digit numeric suffix"
        )
    return f"BraTS2021_{match.group(1)}"


def _normalize_unseen_cohort_id(raw_id: str, prefix: str) -> str:
    """Normalize only unambiguous formatting for an unseen cohort.

    No numeric padding, prefix alias, or suffix stripping is applied here.
    This is intentional until real EGD/TCGA filenames are available.
    """
    value = _normalized_separators(raw_id)
    if _GENERIC_ID_RE.fullmatch(value) is None:
        raise IdentifierNormalizationError(
            "unseen-cohort identifiers may contain only letters, digits, and separators"
        )
    if value == prefix or value.startswith(f"{prefix}-"):
        return value
    if prefix.startswith("TCGA-") and value.startswith("TCGA-"):
        return value
    return f"{prefix}-{value}"


def normalize_egd_id(raw_id: str) -> str:
    """Normalize EGD formatting conservatively until its inventory arrives."""
    return _normalize_unseen_cohort_id(raw_id, "EGD")


def normalize_tcga_gbm_id(raw_id: str) -> str:
    """Normalize TCGA-GBM formatting conservatively until its inventory arrives."""
    return _normalize_unseen_cohort_id(raw_id, "TCGA-GBM")


def normalize_tcga_lgg_id(raw_id: str) -> str:
    """Normalize TCGA-LGG formatting conservatively until its inventory arrives."""
    return _normalize_unseen_cohort_id(raw_id, "TCGA-LGG")


def normalize_identifier(raw_id: str, cohort: Cohort | str) -> str:
    """Normalize ``raw_id`` using the rules for ``cohort``.

    Cohort aliases include the names used in the research documents, such as
    ``"UTSW-Glioma"`` and ``"UCSF-PDGM"``. Unknown cohort names and malformed
    identifiers fail closed instead of applying a broad lossy transformation.
    """
    selected = _coerce_cohort(cohort)
    normalizers = {
        Cohort.UTSW: normalize_utsw_id,
        Cohort.UCSF_PDGM: normalize_ucsf_pdgm_id,
        Cohort.BRATS_2021: normalize_brats2021_id,
        Cohort.EGD: normalize_egd_id,
        Cohort.TCGA_GBM: normalize_tcga_gbm_id,
        Cohort.TCGA_LGG: normalize_tcga_lgg_id,
    }
    return normalizers[selected](raw_id)

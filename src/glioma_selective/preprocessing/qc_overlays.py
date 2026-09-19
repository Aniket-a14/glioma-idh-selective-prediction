"""Deterministic Phase 04 visual-QC sampling and overlay figures.

The sampler deliberately treats UTSW and UCSF-PDGM differently.  UTSW is the
development cohort and may be stratified using its IDH metadata.  UCSF-PDGM
is an external cohort before Gate E, so its sample is uniform and does not
touch any label reader.  Patient identifiers are accepted in memory and are
written only to the private QC index; neither figure names nor the review
sheet contains them.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import random
import re
import tempfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, Literal

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from scipy.ndimage import (  # type: ignore[import-untyped]
    binary_closing,
    generate_binary_structure,
    label,
)
from scipy.spatial import ConvexHull, QhullError  # type: ignore[import-untyped]

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.id_normalization import Cohort, normalize_identifier
from glioma_selective.preprocessing.discovery import CaseRecord
from glioma_selective.utils import paths

__all__ = [
    "QC_SAMPLE_SEED",
    "QCOverlayError",
    "QCSelection",
    "QCShapeMetrics",
    "QCVerificationSummary",
    "compute_t1ce_shape_metrics",
    "load_verification_cases",
    "load_verification_statuses",
    "load_qc_overlay_index",
    "mask_closing_gain",
    "mask_solidity",
    "read_utsw_idh_labels",
    "render_qc_overlay",
    "review_sheet_has_selection_reason",
    "select_qc_tail",
    "select_qc_sample",
    "select_new_borderline",
    "assign_continuing_qc_keys",
    "append_qc_overlay_index",
    "append_qc_review_sheet",
    "review_sheet_has_tail",
    "write_qc_overlay_index",
    "write_qc_review_sheet",
]


QC_SAMPLE_SEED: Final[int] = 20260919
_VERIFICATION_SCHEMA_VERSION: Final[int] = 2
_REVIEW_COLUMNS: Final[tuple[str, ...]] = (
    "qc_key",
    "cohort",
    "selection_reason",
    "brain_voxel_fraction",
    "min_cross_sequence_dice",
    "reviewer_verdict",
    "failure_category",
    "notes",
)
_SELECTION_REASONS: tuple[str, ...] = (
    "borderline",
    "stratified",
    "random",
    "tail",
    "shape_tail",
)
SelectionReason = Literal["borderline", "stratified", "random", "tail", "shape_tail"]
IDHLabelReader = Callable[[Cohort, Path], Mapping[str, str]]
OverlayIndex = dict[str, tuple[Cohort, str]]


class QCOverlayError(ValueError):
    """Raised when a QC sample or selected case cannot be rendered safely."""


@dataclass(frozen=True)
class QCShapeMetrics:
    """Image-only T1ce shape metrics used for shape-tail sampling."""

    solidity: float
    closing_gain: float

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value) for value in (self.solidity, self.closing_gain)
        ):
            raise ValueError("QC shape metrics must be finite")


@dataclass(frozen=True)
class QCSelection:
    """One selected case, with a non-identifying QC key assigned for output."""

    cohort: Cohort
    patient_id: str
    selection_reason: SelectionReason
    selection_reasons: tuple[SelectionReason, ...] = ()
    qc_key: str = ""
    shape_metrics: QCShapeMetrics | None = None

    def __post_init__(self) -> None:
        if not self.patient_id.strip():
            raise ValueError("QC selection patient ID must not be empty")
        reasons = self.selection_reasons or (self.selection_reason,)
        if self.selection_reason not in reasons:
            raise ValueError("primary QC selection reason must be listed")
        if any(reason not in _SELECTION_REASONS for reason in reasons):
            raise ValueError("unsupported QC selection reason")
        object.__setattr__(self, "selection_reasons", tuple(reasons))


@dataclass(frozen=True)
class QCVerificationSummary:
    """Automated values displayed in a QC figure and review row."""

    brain_voxel_fraction: float | None
    min_cross_sequence_dice: float | None


def _downsampled_largest_component(mask: np.ndarray) -> np.ndarray:
    """Keep the largest 26-connected component and downsample it by two."""

    array = np.asarray(mask)
    if array.ndim != 3:
        raise QCOverlayError("shape metric masks must be three-dimensional")
    binary = np.asarray(array != 0, dtype=bool)
    raw_labels, raw_component_count = label(binary, structure=np.ones((3, 3, 3)))
    labels = np.asarray(raw_labels, dtype=np.int32)
    component_count = int(raw_component_count)
    if component_count == 0:
        raise QCOverlayError("shape metrics require a non-empty mask")
    component_sizes = np.bincount(labels.ravel())
    largest_label = int(np.argmax(component_sizes[1:])) + 1
    downsampled: np.ndarray = np.asarray(labels == largest_label, dtype=bool)
    downsampled = np.asarray(downsampled[::2, ::2, ::2], dtype=bool)
    if not np.any(downsampled):
        raise QCOverlayError("shape metrics have no voxels after downsampling")
    return downsampled


def _shape_metrics_from_reduced(reduced: np.ndarray) -> QCShapeMetrics:
    points = np.argwhere(reduced)
    try:
        hull_volume = float(ConvexHull(points).volume)
    except QhullError as error:
        raise QCOverlayError(
            "shape metric mask is too degenerate for a hull"
        ) from error
    if not math.isfinite(hull_volume) or hull_volume <= 0:
        raise QCOverlayError("shape metric hull volume is not positive")
    original_count = int(reduced.sum())
    closed = binary_closing(
        reduced,
        structure=generate_binary_structure(3, 2),
        iterations=3,
    )
    return QCShapeMetrics(
        solidity=float(points.shape[0]) / hull_volume,
        closing_gain=float(int(closed.sum()) - original_count) / original_count,
    )


def mask_solidity(mask: np.ndarray) -> float:
    """Return mask solidity after the specified Phase 04 shape reduction.

    The mask is reduced to its largest 26-connected component using
    ``scipy.ndimage.label`` with ``np.ones((3, 3, 3))``, downsampled by two on
    every axis, and converted to ``pts = np.argwhere(mm)``.  Solidity is
    ``pts.shape[0] / scipy.spatial.ConvexHull(pts).volume``.
    """

    return _shape_metrics_from_reduced(_downsampled_largest_component(mask)).solidity


def mask_closing_gain(mask: np.ndarray) -> float:
    """Return the morphological-closing gain for a reduced binary mask.

    The mask is reduced to its largest 26-connected component using
    ``scipy.ndimage.label`` with ``np.ones((3, 3, 3))``, downsampled by two on
    every axis, and closed with ``binary_closing(mm,
    structure=generate_binary_structure(3, 2), iterations=3)``.  The result
    is ``(closed.sum() - mm.sum()) / mm.sum()``.  A high gain is the suspicious
    direction because closing fills more missing shape.
    """

    return _shape_metrics_from_reduced(
        _downsampled_largest_component(mask)
    ).closing_gain


def compute_t1ce_shape_metrics(t1ce_path: Path) -> QCShapeMetrics:
    """Compute solidity and closing gain from a T1ce NIfTI path.

    The T1ce mask is ``T1ce != 0``.  Each metric then uses the largest
    26-connected component, twofold downsampling on every axis, and the exact
    definitions in :func:`mask_solidity` and :func:`mask_closing_gain`.
    """

    try:
        image = nib.load(t1ce_path)
        if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
            raise ValueError
        if len(image.shape) != 3:
            raise ValueError
        array = np.asarray(image.get_fdata(dtype=np.float32))
    except (OSError, ValueError, TypeError):
        raise QCOverlayError("cannot read T1ce volume for shape metrics") from None
    if not np.all(np.isfinite(array)):
        raise QCOverlayError("T1ce volume for shape metrics is not finite")
    return _shape_metrics_from_reduced(_downsampled_largest_component(array != 0))


def _cohort(value: Cohort | str) -> Cohort:
    if isinstance(value, Cohort):
        return value
    try:
        return Cohort(value)
    except ValueError as error:
        raise QCOverlayError("verification record has an unsupported cohort") from error


def _finite_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise QCOverlayError("verification metric is not numeric")
    converted = float(value)
    if not math.isfinite(converted):
        raise QCOverlayError("verification metric is not finite")
    return converted


def load_verification_cases(
    verification_path: Path,
) -> dict[tuple[Cohort, str], QCVerificationSummary]:
    """Load schema-v2 per-case verification values from private storage.

    The returned mapping contains no filesystem paths.  Errors intentionally
    omit the input path so a malformed private record cannot leak it to logs.
    """

    try:
        payload = json.loads(verification_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QCOverlayError("cannot read preprocessing verification cases") from error
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != _VERIFICATION_SCHEMA_VERSION
    ):
        raise QCOverlayError(
            "preprocessing verification cases must use schema version 2"
        )
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise QCOverlayError(
            "preprocessing verification cases are missing their case list"
        )
    result: dict[tuple[Cohort, str], QCVerificationSummary] = {}
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise QCOverlayError("preprocessing verification case is not an object")
        raw_cohort = raw_case.get("cohort")
        patient_id = raw_case.get("patient_id")
        if not isinstance(raw_cohort, str) or not isinstance(patient_id, str):
            raise QCOverlayError(
                "preprocessing verification case identity is malformed"
            )
        key = (_cohort(raw_cohort), patient_id)
        if key in result:
            raise QCOverlayError("preprocessing verification cases contain a duplicate")
        raw_dice = raw_case.get("cross_sequence_dice")
        if not isinstance(raw_dice, dict):
            raise QCOverlayError("preprocessing verification case is missing mask Dice")
        dice_values = [_finite_float(value) for value in raw_dice.values()]
        finite_dice = [value for value in dice_values if value is not None]
        result[key] = QCVerificationSummary(
            brain_voxel_fraction=_finite_float(raw_case.get("brain_voxel_fraction")),
            min_cross_sequence_dice=min(finite_dice) if finite_dice else None,
        )
    return result


def load_verification_statuses(
    verification_path: Path,
) -> dict[tuple[Cohort, str], str]:
    """Load current per-case statuses from the private verification report."""

    try:
        payload = json.loads(verification_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QCOverlayError("cannot read preprocessing verification cases") from error
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != _VERIFICATION_SCHEMA_VERSION
    ):
        raise QCOverlayError(
            "preprocessing verification cases must use schema version 2"
        )
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise QCOverlayError(
            "preprocessing verification cases are missing their case list"
        )
    result: dict[tuple[Cohort, str], str] = {}
    for raw_case in raw_cases:
        if not isinstance(raw_case, dict):
            raise QCOverlayError("preprocessing verification case is not an object")
        raw_cohort = raw_case.get("cohort")
        patient_id = raw_case.get("patient_id")
        status = raw_case.get("status")
        if (
            not isinstance(raw_cohort, str)
            or not isinstance(patient_id, str)
            or not isinstance(status, str)
        ):
            raise QCOverlayError("preprocessing verification case status is malformed")
        key = (_cohort(raw_cohort), patient_id)
        if key in result:
            raise QCOverlayError("preprocessing verification cases contain a duplicate")
        result[key] = status
    return result


def _borderline_from_verification(
    verification_path: Path,
) -> tuple[QCSelection, ...]:
    """Read every visual-QC borderline record from the private report."""
    statuses = load_verification_statuses(verification_path)
    return tuple(
        QCSelection(cohort, patient_id, "borderline")
        for (cohort, patient_id), status in statuses.items()
        if status == "verified-borderline"
    )


def _idh_class(value: str) -> Literal["mutant", "wildtype"]:
    normalized = "".join(
        character for character in value.casefold() if character.isalnum()
    )
    if normalized in {"mutated", "mutant", "idhmutated", "idhmutant"}:
        return "mutant"
    if normalized in {"wildtype", "idhwildtype", "wt"}:
        return "wildtype"
    raise QCOverlayError("UTSW metadata contains an unsupported IDH category")


def read_utsw_idh_labels(cohort: Cohort, metadata_path: Path) -> Mapping[str, str]:
    """Read UTSW ``Subject ID``/``IDH`` values for the injected-reader API."""

    if cohort is not Cohort.UTSW:
        raise QCOverlayError("IDH metadata is permitted only for UTSW sampling")
    try:
        with metadata_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if not reader.fieldnames or not {"Subject ID", "IDH"}.issubset(
                reader.fieldnames
            ):
                raise QCOverlayError(
                    "UTSW metadata is missing Subject ID or IDH columns"
                )
            labels: dict[str, str] = {}
            for row in reader:
                raw_id = row.get("Subject ID")
                raw_label = row.get("IDH")
                if not raw_id or raw_label is None:
                    raise QCOverlayError("UTSW metadata contains an incomplete IDH row")
                if raw_label.strip().casefold() in {"", "na", "n/a"}:
                    # These rows are excluded from the retained UTSW roster
                    # by the Phase 03 exclusion manifest.
                    continue
                try:
                    canonical_id = normalize_identifier(raw_id, Cohort.UTSW)
                except ValueError as error:
                    raise QCOverlayError(
                        "UTSW metadata contains an invalid Subject ID"
                    ) from error
                if canonical_id in labels:
                    raise QCOverlayError(
                        "UTSW metadata contains a duplicate Subject ID"
                    )
                labels[canonical_id] = _idh_class(raw_label)
            return labels
    except OSError as error:
        raise QCOverlayError("cannot read UTSW IDH metadata") from error


def _retained_ids(
    retained_patient_ids: Mapping[Cohort, Iterable[str]] | Mapping[str, Iterable[str]],
) -> dict[Cohort, tuple[str, ...]]:
    result: dict[Cohort, tuple[str, ...]] = {}
    for raw_cohort, raw_ids in retained_patient_ids.items():
        selected = _cohort(raw_cohort)
        if selected not in {Cohort.UTSW, Cohort.UCSF_PDGM}:
            raise QCOverlayError("QC sampling supports UTSW and UCSF-PDGM only")
        values = tuple(dict.fromkeys(patient_id.strip() for patient_id in raw_ids))
        if any(not patient_id for patient_id in values):
            raise QCOverlayError("retained QC roster contains an empty patient ID")
        if selected in result:
            raise QCOverlayError("retained QC roster repeats a cohort")
        result[selected] = values
    missing = {Cohort.UTSW, Cohort.UCSF_PDGM} - set(result)
    if missing:
        raise QCOverlayError("retained QC roster is missing a required cohort")
    return result


def _add_reason(
    reasons: dict[tuple[Cohort, str], set[SelectionReason]],
    selection: QCSelection,
) -> None:
    key = (selection.cohort, selection.patient_id)
    reasons.setdefault(key, set()).update(selection.selection_reasons)


def _primary_reason(reasons: set[SelectionReason]) -> SelectionReason:
    return next(reason for reason in _SELECTION_REASONS if reason in reasons)


def select_qc_sample(
    *,
    retained_patient_ids: Mapping[Cohort, Iterable[str]] | Mapping[str, Iterable[str]],
    borderline_cases: Iterable[QCSelection | Mapping[str, object]] = (),
    borderline_cases_path: Path | None = None,
    label_reader: IDHLabelReader | None = None,
    utsw_metadata_path: Path | None = None,
    utsw_idh_labels: Mapping[str, str] | None = None,
    per_utsw_stratum: int = 12,
    ucsf_count: int = 12,
    seed: int = QC_SAMPLE_SEED,
) -> tuple[QCSelection, ...]:
    """Select the D-028 sample and assign deterministic non-identifying keys.

    ``label_reader`` is called exactly once, for UTSW, when
    ``utsw_idh_labels`` is not supplied.  It is never called for UCSF-PDGM.
    Borderline cases have primary reason ``borderline`` when they also occur
    in a random draw; ``selection_reasons`` retains all reasons.
    """

    if per_utsw_stratum < 1 or ucsf_count < 1:
        raise QCOverlayError("QC sample sizes must be positive")
    retained = _retained_ids(retained_patient_ids)
    reasons: dict[tuple[Cohort, str], set[SelectionReason]] = {}

    borderline_entries = list(borderline_cases)
    if borderline_cases_path is not None:
        borderline_entries.extend(_borderline_from_verification(borderline_cases_path))
    for entry in borderline_entries:
        if isinstance(entry, QCSelection):
            selection = entry
        elif isinstance(entry, Mapping):
            raw_cohort = entry.get("cohort")
            patient_id = entry.get("patient_id")
            status = entry.get("status")
            if status is not None and status != "verified-borderline":
                continue
            if not isinstance(raw_cohort, str) or not isinstance(patient_id, str):
                raise QCOverlayError("borderline selection identity is malformed")
            selection = QCSelection(
                cohort=_cohort(raw_cohort),
                patient_id=patient_id,
                selection_reason="borderline",
            )
        else:
            raise QCOverlayError("borderline selection is not an object")
        _add_reason(reasons, selection)

    if utsw_idh_labels is None:
        reader = label_reader or read_utsw_idh_labels
        if utsw_metadata_path is None:
            raise QCOverlayError(
                "UTSW IDH metadata is required for stratified sampling"
            )
        # This is intentionally the sole label-reader call.  The UCSF branch
        # below samples identifiers without consulting any external labels.
        utsw_idh_labels = reader(Cohort.UTSW, utsw_metadata_path)
    normalized_labels: dict[str, str] = {}
    for patient_id, raw_label in utsw_idh_labels.items():
        normalized_labels[patient_id] = _idh_class(raw_label)
    strata: dict[str, list[str]] = {"mutant": [], "wildtype": []}
    for patient_id in retained[Cohort.UTSW]:
        try:
            strata[normalized_labels[patient_id]].append(patient_id)
        except KeyError as error:
            raise QCOverlayError(
                "UTSW retained roster is missing an IDH label"
            ) from error

    draw_rng = random.Random(seed)
    for category in ("mutant", "wildtype"):
        available = sorted(strata[category])
        if len(available) < per_utsw_stratum:
            raise QCOverlayError("UTSW IDH stratum is smaller than the QC sample")
        for patient_id in draw_rng.sample(available, per_utsw_stratum):
            _add_reason(
                reasons,
                QCSelection(
                    cohort=Cohort.UTSW,
                    patient_id=patient_id,
                    selection_reason="stratified",
                ),
            )

    available_ucsf = sorted(retained[Cohort.UCSF_PDGM])
    if len(available_ucsf) < ucsf_count:
        raise QCOverlayError("UCSF-PDGM retained roster is smaller than the QC sample")
    for patient_id in draw_rng.sample(available_ucsf, ucsf_count):
        _add_reason(
            reasons,
            QCSelection(
                cohort=Cohort.UCSF_PDGM,
                patient_id=patient_id,
                selection_reason="random",
            ),
        )

    selections = [
        QCSelection(
            cohort=cohort,
            patient_id=patient_id,
            selection_reason=_primary_reason(case_reasons),
            selection_reasons=tuple(
                reason for reason in _SELECTION_REASONS if reason in case_reasons
            ),
        )
        for (cohort, patient_id), case_reasons in reasons.items()
    ]
    key_rng = random.Random(seed)
    key_rng.shuffle(selections)
    return tuple(
        replace(selection, qc_key=f"qc_{index:04d}")
        for index, selection in enumerate(selections, start=1)
    )


def select_new_borderline(
    *,
    retained_patient_ids: Mapping[Cohort, Iterable[str]] | Mapping[str, Iterable[str]],
    verification_statuses: Mapping[tuple[Cohort, str], str],
    indexed_cases: Iterable[tuple[Cohort, str]] = (),
) -> tuple[QCSelection, ...]:
    """Select retained, newly borderline cases in deterministic order.

    Selection is based only on the current verification status, the retained
    roster, and the existing ``(cohort, patient_id)`` index.  QC keys are
    assigned separately so this pure selector remains idempotent.
    """

    retained = _retained_ids(retained_patient_ids)
    retained_cases = {
        (cohort, patient_id)
        for cohort, patient_ids in retained.items()
        for patient_id in patient_ids
    }
    indexed = set(indexed_cases)
    return tuple(
        QCSelection(cohort, patient_id, "borderline")
        for cohort, patient_id in sorted(
            verification_statuses, key=lambda item: (item[0].value, item[1])
        )
        if verification_statuses[(cohort, patient_id)] == "verified-borderline"
        and (cohort, patient_id) in retained_cases
        and (cohort, patient_id) not in indexed
    )


def select_qc_tail(
    *,
    retained_patient_ids: Mapping[Cohort, Iterable[str]] | Mapping[str, Iterable[str]],
    verification: Mapping[tuple[Cohort, str], QCVerificationSummary],
    indexed_cases: Iterable[tuple[Cohort, str]] = (),
    per_cohort: int = 0,
    seed: int = QC_SAMPLE_SEED,
) -> tuple[QCSelection, ...]:
    """Select the lowest-brain-fraction cases not already in the QC index.

    Ranking uses the image-derived ``brain_voxel_fraction`` only.  A seeded
    shuffle is applied before sorting so equal fractions have deterministic,
    reproducible tie-breaking.  This function does not accept or invoke a
    label reader; in particular, UCSF-PDGM tail selection is label-free.
    """

    if per_cohort < 0:
        raise QCOverlayError("QC tail size must not be negative")
    if per_cohort == 0:
        return ()
    retained = _retained_ids(retained_patient_ids)
    indexed = set(indexed_cases)
    selected: list[QCSelection] = []
    for cohort in (Cohort.UTSW, Cohort.UCSF_PDGM):
        candidates = [
            (patient_id, verification.get((cohort, patient_id)))
            for patient_id in retained[cohort]
            if (cohort, patient_id) not in indexed
        ]
        ranked = [
            (patient_id, summary.brain_voxel_fraction)
            for patient_id, summary in candidates
            if summary is not None and summary.brain_voxel_fraction is not None
        ]
        if len(ranked) < per_cohort:
            raise QCOverlayError("QC tail has fewer ranked cases than requested")
        random.Random(seed + (0 if cohort is Cohort.UTSW else 1)).shuffle(ranked)
        ranked.sort(key=lambda item: item[1])
        selected.extend(
            QCSelection(cohort, patient_id, "tail")
            for patient_id, _fraction in ranked[:per_cohort]
        )
    random.Random(seed).shuffle(selected)
    return tuple(selected)


def select_qc_shape_tail(
    *,
    retained_patient_ids: Mapping[Cohort, Iterable[str]] | Mapping[str, Iterable[str]],
    shape_metrics: Mapping[tuple[Cohort, str], QCShapeMetrics],
    indexed_cases: Iterable[tuple[Cohort, str]] = (),
    cohort: Cohort = Cohort.UTSW,
    per_metric: int = 0,
) -> tuple[QCSelection, ...]:
    """Select the union of the lowest-solidity and highest-gain shape tails.

    For the chosen cohort, candidates are restricted to retained cases that
    are not already in the private QC overlay index.  The selected set is the
    union of the ``per_metric`` lowest-solidity cases and the ``per_metric``
    highest-closing-gain cases.  Both rankings use patient ID as a stable
    tie-breaker.  Closing gain is suspicious in the high direction because a
    larger morphological fill-in indicates more missing shape.  No labels are
    read for either cohort.
    """

    if per_metric < 0:
        raise QCOverlayError("QC shape-tail size must not be negative")
    if cohort not in {Cohort.UTSW, Cohort.UCSF_PDGM}:
        raise QCOverlayError("QC shape-tail supports UTSW and UCSF-PDGM only")
    if per_metric == 0:
        return ()
    retained = _retained_ids(retained_patient_ids)
    indexed = set(indexed_cases)
    candidates = [
        patient_id
        for patient_id in retained[cohort]
        if (cohort, patient_id) not in indexed
    ]
    ranked: list[tuple[str, QCShapeMetrics]] = []
    for patient_id in candidates:
        metrics = shape_metrics.get((cohort, patient_id))
        if metrics is None:
            raise QCOverlayError("QC shape-tail is missing a ranked case")
        ranked.append((patient_id, metrics))
    if not ranked:
        return ()
    if len(ranked) < per_metric:
        raise QCOverlayError("QC shape-tail has fewer ranked cases than requested")

    lowest_solidity = sorted(ranked, key=lambda item: (item[1].solidity, item[0]))[
        :per_metric
    ]
    highest_closing_gain = sorted(
        ranked, key=lambda item: (-item[1].closing_gain, item[0])
    )[:per_metric]
    union_ids = {
        patient_id for patient_id, _metrics in (*lowest_solidity, *highest_closing_gain)
    }
    return tuple(
        QCSelection(
            cohort=cohort,
            patient_id=patient_id,
            selection_reason="shape_tail",
            shape_metrics=next(
                metrics
                for candidate_id, metrics in ranked
                if candidate_id == patient_id
            ),
        )
        for patient_id in sorted(union_ids)
    )


_QC_KEY_RE = re.compile(r"qc_(\d+)")


def assign_continuing_qc_keys(
    selections: Sequence[QCSelection], existing_index: Mapping[str, tuple[Cohort, str]]
) -> tuple[QCSelection, ...]:
    """Assign the next unused numeric QC keys without changing old keys."""

    used_keys = set(existing_index)
    used_cases = set(existing_index.values())
    next_number = 1
    for key in used_keys:
        match = _QC_KEY_RE.fullmatch(key)
        if match is not None:
            next_number = max(next_number, int(match.group(1)) + 1)
    assigned: list[QCSelection] = []
    for selection in selections:
        case_key = (selection.cohort, selection.patient_id)
        if case_key in used_cases:
            raise QCOverlayError("QC tail selection is already indexed")
        while f"qc_{next_number:04d}" in used_keys:
            next_number += 1
        qc_key = f"qc_{next_number:04d}"
        assigned.append(replace(selection, qc_key=qc_key))
        used_keys.add(qc_key)
        used_cases.add(case_key)
        next_number += 1
    return tuple(assigned)


def _load_case_volume(case: CaseRecord, sequence: CanonicalSequence) -> np.ndarray:
    volume_path = case.sequence_files.get(sequence)
    if volume_path is None:
        raise QCOverlayError(f"selected case is missing the {sequence.value} volume")
    if not volume_path.is_file():
        raise QCOverlayError(f"selected case is missing the {sequence.value} volume")
    try:
        image = nib.load(volume_path)
        if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
            raise ValueError
        if len(image.shape) != 3:
            raise ValueError
        array = np.asarray(image.get_fdata(dtype=np.float32))
    except (OSError, ValueError, TypeError):
        raise QCOverlayError(
            f"selected case has an unreadable {sequence.value} volume"
        ) from None
    if not np.all(np.isfinite(array)):
        raise QCOverlayError(f"selected case has an invalid {sequence.value} volume")
    return array


def _load_segmentation(case: CaseRecord, shape: tuple[int, ...]) -> np.ndarray | None:
    for role in ("tumorseg_FeTS", "tumor_segmentation"):
        segmentation_path = case.segmentation_files.get(role)
        if segmentation_path is None:
            continue
        if not segmentation_path.is_file():
            return None
        try:
            image = nib.load(segmentation_path)
            if not isinstance(image, nib.Nifti1Image | nib.Nifti2Image):
                return None
            if len(image.shape) != 3:
                return None
            array = np.asarray(image.get_fdata(dtype=np.float32))
        except (OSError, ValueError, TypeError):
            return None
        if array.shape != shape or not np.all(np.isfinite(array)):
            return None
        return array
    return None


def _dice(left: np.ndarray, right: np.ndarray) -> float:
    left_count = int(np.count_nonzero(left))
    right_count = int(np.count_nonzero(right))
    if left_count + right_count == 0:
        return 1.0
    return 2.0 * float(np.count_nonzero(left & right)) / (left_count + right_count)


def _plane(array: np.ndarray, plane: str, index: int) -> tuple[np.ndarray, int, int]:
    axes = {"axial": (2, 0, 1), "coronal": (1, 0, 2), "sagittal": (0, 1, 2)}
    slice_axis, x_axis, y_axis = axes[plane]
    return np.take(array, index, axis=slice_axis), x_axis, y_axis


def _slice_centroid(mask: np.ndarray) -> tuple[int, int, int]:
    coordinates = np.argwhere(mask)
    if coordinates.size == 0:
        raise QCOverlayError("selected case has an empty T1CE brain mask")
    centroid = np.rint(coordinates.mean(axis=0)).astype(int)
    return (
        int(max(0, min(int(centroid[0]), mask.shape[0] - 1))),
        int(max(0, min(int(centroid[1]), mask.shape[1] - 1))),
        int(max(0, min(int(centroid[2]), mask.shape[2] - 1))),
    )


def _display_limits(array: np.ndarray) -> tuple[float, float]:
    nonzero = array[np.isfinite(array) & (array != 0)]
    values = nonzero if nonzero.size else array[np.isfinite(array)]
    if values.size == 0:
        return 0.0, 1.0
    low, high = np.percentile(values, (1, 99))
    if not math.isfinite(float(low)) or not math.isfinite(float(high)) or low == high:
        low, high = float(values.min()), float(values.max())
    if low == high:
        high = low + 1.0
    return float(low), float(high)


def _edge_mask(image: np.ndarray, fallback_mask: np.ndarray) -> np.ndarray:
    gradients = np.gradient(image.astype(np.float32, copy=False))
    magnitude = np.hypot(gradients[0], gradients[1])
    positive = magnitude[np.isfinite(magnitude) & (magnitude > 0)]
    if positive.size:
        threshold = float(np.percentile(positive, 92))
        return np.asarray(magnitude >= threshold, dtype=bool)
    return fallback_mask


def _label_axes(axis: Axes, orientation: str, x_axis: int, y_axis: int) -> None:
    typed_axis = axis
    typed_axis.set_xlabel(f"array axis {x_axis} ({orientation[x_axis]})")
    typed_axis.set_ylabel(f"array axis {y_axis} ({orientation[y_axis]})")


def _draw_image(
    axis: Axes,
    image: np.ndarray,
    title: str,
    orientation: str,
    x_axis: int,
    y_axis: int,
) -> None:
    typed_axis = axis
    low, high = _display_limits(image)
    typed_axis.imshow(image.T, cmap="gray", vmin=low, vmax=high, origin="lower")
    typed_axis.set_title(title)
    _label_axes(typed_axis, orientation, x_axis, y_axis)
    typed_axis.set_xticks([])
    typed_axis.set_yticks([])


def _draw_contour(axis: Axes, mask: np.ndarray, color: str, label: str) -> None:
    typed_axis = axis
    if np.any(mask):
        typed_axis.contour(
            mask.T.astype(float), levels=[0.5], colors=[color], linewidths=0.8
        )
    if label:
        typed_axis.plot([], [], color=color, label=label)


def render_qc_overlay(
    case: CaseRecord,
    selection: QCSelection,
    verification: QCVerificationSummary | None = None,
) -> Figure:
    """Render one selected case and return an unclosed matplotlib figure.

    The caller owns the returned figure and must close it after saving.  The
    figure has three modality/T1CE panels, three brain-boundary panels, and
    three FeTS-over-FLAIR panels (axial, coronal, sagittal).
    """

    volumes = {
        sequence: _load_case_volume(case, sequence) for sequence in CORE_SEQUENCES
    }
    t1ce = volumes[CanonicalSequence.T1CE]
    if not np.any(t1ce != 0):
        raise QCOverlayError("selected case has an empty T1CE brain mask")
    brain_mask = t1ce != 0
    segmentation = _load_segmentation(case, t1ce.shape)
    fets_mask = (
        (segmentation == 1) | (segmentation == 2) | (segmentation == 4)
        if segmentation is not None
        else np.zeros_like(brain_mask)
    )
    slice_point = (
        _slice_centroid(fets_mask) if np.any(fets_mask) else _slice_centroid(brain_mask)
    )
    image_orientation = "RAS"
    try:
        t1ce_image = nib.load(case.sequence_files[CanonicalSequence.T1CE])
        if not isinstance(t1ce_image, nib.Nifti1Image | nib.Nifti2Image):
            raise ValueError
        image_orientation = "".join(
            code or "?" for code in nib.aff2axcodes(t1ce_image.affine)
        )
    except (OSError, ValueError, TypeError, KeyError):
        pass

    brain_fraction = float(np.count_nonzero(brain_mask) / brain_mask.size)
    dice_values = [
        _dice(brain_mask, volumes[sequence] != 0) for sequence in CORE_SEQUENCES
    ]
    computed_verification = QCVerificationSummary(brain_fraction, min(dice_values))
    summary = verification or computed_verification
    figure, axes = plt.subplots(3, 3, figsize=(11, 9), dpi=100, constrained_layout=True)
    planes = ("axial", "coronal", "sagittal")
    for column, sequence in enumerate(
        (CanonicalSequence.T1, CanonicalSequence.T2, CanonicalSequence.FLAIR)
    ):
        plane, x_axis, y_axis = _plane(volumes[sequence], "axial", slice_point[2])
        _draw_image(
            axes[0, column],
            plane,
            f"{sequence.value} + T1CE edges",
            image_orientation,
            x_axis,
            y_axis,
        )
        t1ce_plane, _, _ = _plane(t1ce, "axial", slice_point[2])
        edge = _edge_mask(t1ce_plane, _plane(brain_mask, "axial", slice_point[2])[0])
        _draw_contour(axes[0, column], edge, "cyan", "T1CE edge")
        axes[0, column].legend(loc="upper right", fontsize=6)

    for column, plane_name in enumerate(planes):
        slice_axis = {"axial": 2, "coronal": 1, "sagittal": 0}[plane_name]
        plane, x_axis, y_axis = _plane(t1ce, plane_name, slice_point[slice_axis])
        _draw_image(
            axes[1, column],
            plane,
            f"T1CE brain boundary ({plane_name})",
            image_orientation,
            x_axis,
            y_axis,
        )
        _draw_contour(
            axes[1, column],
            _plane(brain_mask, plane_name, slice_point[slice_axis])[0],
            "yellow",
            "brain mask",
        )
        axes[1, column].legend(loc="upper right", fontsize=6)

    for column, plane_name in enumerate(planes):
        slice_axis = {"axial": 2, "coronal": 1, "sagittal": 0}[plane_name]
        plane, x_axis, y_axis = _plane(
            volumes[CanonicalSequence.FLAIR], plane_name, slice_point[slice_axis]
        )
        _draw_image(
            axes[2, column],
            plane,
            f"FeTS contours over FLAIR ({plane_name})",
            image_orientation,
            x_axis,
            y_axis,
        )
        if segmentation is None:
            axes[2, column].text(
                0.5,
                0.5,
                "FeTS unavailable",
                transform=axes[2, column].transAxes,
                ha="center",
                va="center",
                color="white",
            )
        else:
            for label, color in ((1, "lime"), (2, "magenta"), (4, "red")):
                _draw_contour(
                    axes[2, column],
                    _plane(segmentation == label, plane_name, slice_point[slice_axis])[
                        0
                    ],
                    color,
                    f"FeTS {label}",
                )
            axes[2, column].legend(loc="upper right", fontsize=6)

    brain_text = (
        "n/a"
        if summary.brain_voxel_fraction is None
        else f"{summary.brain_voxel_fraction:.4f}"
    )
    dice_text = (
        "n/a"
        if summary.min_cross_sequence_dice is None
        else f"{summary.min_cross_sequence_dice:.4f}"
    )
    title = (
        "Phase 04 visual QC | "
        f"{selection.selection_reason} | brain fraction {brain_text} | "
        f"min cross-sequence Dice {dice_text}"
    )
    if selection.selection_reason == "shape_tail":
        if selection.shape_metrics is None:
            raise QCOverlayError("shape-tail overlay is missing its shape metrics")
        title += (
            f" | solidity {selection.shape_metrics.solidity:.3f}"
            f" | closing gain {selection.shape_metrics.closing_gain:.3f}"
        )
    figure.suptitle(title, fontsize=11)
    return figure


def _atomic_write(destination: Path, content: str | bytes) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        temporary_path = Path(temporary_name)
        if isinstance(content, bytes):
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _index_payload(entries: Mapping[str, tuple[Cohort, str]]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "qc_keys": {
            key: {"cohort": cohort.value, "patient_id": patient_id}
            for key, (cohort, patient_id) in entries.items()
        },
    }


def _validate_index_payload(payload: object) -> OverlayIndex:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise QCOverlayError("QC overlay index has an unsupported schema")
    raw_entries = payload.get("qc_keys")
    if not isinstance(raw_entries, dict):
        raise QCOverlayError("QC overlay index is missing its key map")
    entries: OverlayIndex = {}
    cases: set[tuple[Cohort, str]] = set()
    for raw_key, raw_entry in raw_entries.items():
        if not isinstance(raw_key, str) or _QC_KEY_RE.fullmatch(raw_key) is None:
            raise QCOverlayError("QC overlay index contains an invalid QC key")
        if not isinstance(raw_entry, dict):
            raise QCOverlayError("QC overlay index contains an invalid entry")
        raw_cohort = raw_entry.get("cohort")
        patient_id = raw_entry.get("patient_id")
        if not isinstance(raw_cohort, str) or not isinstance(patient_id, str):
            raise QCOverlayError("QC overlay index contains an invalid case identity")
        case = (_cohort(raw_cohort), patient_id)
        if case in cases:
            raise QCOverlayError("QC overlay index contains a duplicate case")
        entries[raw_key] = case
        cases.add(case)
    return entries


def load_qc_overlay_index(index_path: Path) -> OverlayIndex:
    """Load the private QC index without exposing its identifiers in errors."""

    if not index_path.exists():
        return {}
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QCOverlayError("cannot read QC overlay index") from error
    return _validate_index_payload(payload)


def write_qc_overlay_index(
    selections: Sequence[QCSelection], output_path: Path | None = None
) -> Path:
    """Atomically write a new private QC-key to canonical-ID map."""

    destination = output_path or paths.private_data_dir() / "qc_overlay_index.json"
    entries: OverlayIndex = {}
    for selection in selections:
        if selection.qc_key in entries:
            raise QCOverlayError("QC selections contain a duplicate QC key")
        entries[selection.qc_key] = (selection.cohort, selection.patient_id)
    content = json.dumps(_index_payload(entries), indent=2, sort_keys=True) + "\n"
    _atomic_write(destination, content)
    return destination


def append_qc_overlay_index(
    selections: Sequence[QCSelection], output_path: Path | None = None
) -> Path:
    """Atomically merge new entries while preserving all existing values."""

    destination = output_path or paths.private_data_dir() / "qc_overlay_index.json"
    existing = load_qc_overlay_index(destination)
    merged = dict(existing)
    existing_cases = set(existing.values())
    for selection in selections:
        case = (selection.cohort, selection.patient_id)
        if selection.qc_key in merged or case in existing_cases:
            raise QCOverlayError("QC overlay append would replace an existing entry")
        merged[selection.qc_key] = case
        existing_cases.add(case)
    if selections:
        content = json.dumps(_index_payload(merged), indent=2, sort_keys=True) + "\n"
        _atomic_write(destination, content)
    return destination


def _review_csv_text(
    selections: Sequence[QCSelection],
    verification: Mapping[tuple[Cohort, str], QCVerificationSummary],
    *,
    include_header: bool,
) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=_REVIEW_COLUMNS, lineterminator="\r\n")
    if include_header:
        writer.writeheader()
    for selection in selections:
        summary = verification.get(
            (selection.cohort, selection.patient_id),
            QCVerificationSummary(None, None),
        )
        writer.writerow(
            {
                "qc_key": selection.qc_key,
                "cohort": selection.cohort.value,
                "selection_reason": selection.selection_reason,
                "brain_voxel_fraction": ""
                if summary.brain_voxel_fraction is None
                else f"{summary.brain_voxel_fraction:.8f}",
                "min_cross_sequence_dice": ""
                if summary.min_cross_sequence_dice is None
                else f"{summary.min_cross_sequence_dice:.8f}",
                "reviewer_verdict": "",
                "failure_category": "",
                "notes": "",
            }
        )
    return buffer.getvalue()


def _review_keys(raw_content: bytes) -> set[str]:
    try:
        text = raw_content.decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text, newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise QCOverlayError("QC review sheet is not valid UTF-8 CSV") from error
    if not rows and text.splitlines()[:1] != [",".join(_REVIEW_COLUMNS)]:
        raise QCOverlayError("QC review sheet has an invalid header")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if tuple(reader.fieldnames or ()) != _REVIEW_COLUMNS:
        raise QCOverlayError("QC review sheet has an invalid header")
    keys: set[str] = set()
    for row in rows:
        key = row.get("qc_key")
        if not isinstance(key, str) or _QC_KEY_RE.fullmatch(key) is None:
            raise QCOverlayError("QC review sheet contains an invalid QC key")
        if key in keys:
            raise QCOverlayError("QC review sheet contains a duplicate QC key")
        keys.add(key)
    return keys


def review_sheet_has_selection_reason(
    review_path: Path, selection_reason: SelectionReason
) -> bool:
    """Return whether a review sheet already contains a selection reason."""

    if not review_path.exists():
        return False
    try:
        text = review_path.read_text(encoding="utf-8")
        _review_keys(text.encode("utf-8"))
        rows = csv.DictReader(io.StringIO(text, newline=""))
        return any(row.get("selection_reason") == selection_reason for row in rows)
    except (OSError, UnicodeError, csv.Error) as error:
        raise QCOverlayError("cannot read QC review sheet") from error


def review_sheet_has_tail(review_path: Path) -> bool:
    """Return whether a review sheet already contains an appended tail row."""

    return review_sheet_has_selection_reason(review_path, "tail")


def write_qc_review_sheet(
    selections: Sequence[QCSelection],
    verification: Mapping[tuple[Cohort, str], QCVerificationSummary],
    output_path: Path | None = None,
) -> Path:
    """Atomically write the identifier-free human review sheet."""

    destination = output_path or paths.figures_dir() / "qc" / "qc_review_sheet.csv"
    _atomic_write(
        destination,
        _review_csv_text(selections, verification, include_header=True),
    )
    return destination


def append_qc_review_sheet(
    selections: Sequence[QCSelection],
    verification: Mapping[tuple[Cohort, str], QCVerificationSummary],
    output_path: Path | None = None,
) -> Path:
    """Atomically append blank-verdict rows without rewriting old CSV bytes."""

    destination = output_path or paths.figures_dir() / "qc" / "qc_review_sheet.csv"
    if not selections:
        return destination
    if destination.exists():
        existing = destination.read_bytes()
        existing_keys = _review_keys(existing)
    else:
        existing = _review_csv_text((), {}, include_header=True).encode("utf-8")
        existing_keys = set()
    new_keys = [selection.qc_key for selection in selections]
    if len(set(new_keys)) != len(new_keys) or set(new_keys) & existing_keys:
        raise QCOverlayError("QC review append would replace an existing row")
    addition = _review_csv_text(selections, verification, include_header=False).encode(
        "utf-8"
    )
    if existing and not existing.endswith((b"\n", b"\r")):
        existing += b"\r\n"
    _atomic_write(destination, existing + addition)
    return destination

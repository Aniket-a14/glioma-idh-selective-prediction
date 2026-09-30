"""Per-modality z-score statistics from the frozen UTSW training split only.

T04.6 is a leakage control (D-023, D-036). Raw intensity units differ by up to
several hundred times between patients, so each volume is first divided by its own
brain-voxel median (a per-patient step that uses no other patient's data). The
statistics are then pooled over the rescaled brain (non-zero) voxels of every
training patient, one mean and one population standard deviation per modality, and
applied unchanged to every cohort and split. Applying never recomputes anything,
and there is no clipping.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
from monai.transforms import NormalizeIntensity

from glioma_selective.data.adapters._common import CORE_SEQUENCES, CanonicalSequence
from glioma_selective.leakage.cohort_manifest import compute_roster_sha256
from glioma_selective.leakage.id_normalization import Cohort

__all__ = [
    "NormalizationStats",
    "ModalityStats",
    "PatientMoments",
    "combine_moments",
    "fit_normalization_stats",
    "load_normalization_stats",
    "normalize_volume",
    "patient_moments",
    "write_normalization_stats",
]

STATS_VERSION = 1
FIT_SPLIT = "train"
PATIENT_SCALE = "brain-voxel median"
_SEQUENCE_NAMES = tuple(sequence.value for sequence in CORE_SEQUENCES)


@dataclass(frozen=True)
class PatientMoments:
    """Count, mean and sum of squared deviations of one patient's brain voxels."""

    n: int
    mean: float
    m2: float


@dataclass(frozen=True)
class ModalityStats:
    """Pooled brain-voxel mean and population standard deviation of a modality."""

    mean: float
    std: float
    voxel_count: int


@dataclass(frozen=True)
class NormalizationStats:
    """Frozen statistics and the provenance that proves what they were fitted on."""

    fit_cohort: str
    fit_split: str
    patient_count: int
    train_roster_sha256: str
    split_manifest_sha256: str
    modalities: Mapping[str, ModalityStats]


def _brain_voxels(volume: np.ndarray) -> np.ndarray:
    array = np.asarray(volume)
    brain: np.ndarray = np.asarray(array[array != 0], dtype=np.float64)
    if brain.size == 0:
        raise ValueError("volume has no non-zero brain voxels")
    if not np.all(np.isfinite(brain)):
        raise ValueError("volume contains non-finite values")
    return brain


def _patient_scale(brain: np.ndarray) -> float:
    scale = float(np.median(brain))
    if not scale > 0:
        raise ValueError("brain-voxel median must be positive to rescale a volume")
    return scale


def patient_moments(volume: np.ndarray) -> PatientMoments:
    """Moments of one patient's brain voxels after dividing by their own median."""
    brain = _brain_voxels(volume)
    brain = brain / _patient_scale(brain)
    mean = float(brain.mean())
    return PatientMoments(
        n=int(brain.size), mean=mean, m2=float(np.sum((brain - mean) ** 2))
    )


def combine_moments(items: Sequence[PatientMoments]) -> PatientMoments:
    """Pool moments left to right (Chan et al.); the order is part of the result."""
    if not items:
        raise ValueError("cannot combine an empty list of moments")
    total = items[0]
    for item in items[1:]:
        count = total.n + item.n
        delta = item.mean - total.mean
        total = PatientMoments(
            n=count,
            mean=total.mean + delta * item.n / count,
            m2=total.m2 + item.m2 + delta * delta * total.n * item.n / count,
        )
    return total


def _sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frozen_train_roster(split_manifest_path: Path) -> tuple[str, ...]:
    sidecar = split_manifest_path.with_name(split_manifest_path.name + ".sha256")
    actual = _sha256_bytes(split_manifest_path)
    if not sidecar.is_file():
        raise ValueError("split manifest has no .sha256 sidecar; it is not frozen")
    if sidecar.read_text(encoding="ascii").split()[0] != actual:
        raise ValueError("split manifest does not match its frozen SHA-256")
    document = json.loads(split_manifest_path.read_text(encoding="utf-8"))
    train = document["splits"][FIT_SPLIT]
    return tuple(sorted(str(patient_id) for patient_id in train))


def fit_normalization_stats(
    moments_by_patient: Mapping[str, Mapping[str, PatientMoments]],
    *,
    cohort: Cohort,
    split_name: str,
    split_manifest_path: Path,
) -> NormalizationStats:
    """Fit on exactly the frozen UTSW training roster; refuse anything else."""
    if cohort is not Cohort.UTSW or split_name != FIT_SPLIT:
        raise ValueError("statistics may only be fitted on the UTSW training split")
    train_roster = _frozen_train_roster(split_manifest_path)
    if tuple(sorted(moments_by_patient)) != train_roster:
        raise ValueError("fitting patients differ from the frozen UTSW training roster")
    modalities: dict[str, ModalityStats] = {}
    for name in _SEQUENCE_NAMES:
        pooled = combine_moments(
            [moments_by_patient[pid][name] for pid in train_roster]
        )
        std = math.sqrt(pooled.m2 / pooled.n)
        if not (std > 0 and math.isfinite(std) and math.isfinite(pooled.mean)):
            raise ValueError(f"degenerate statistics for modality {name}")
        modalities[name] = ModalityStats(
            mean=pooled.mean, std=std, voxel_count=pooled.n
        )
    return NormalizationStats(
        fit_cohort=Cohort.UTSW.value,
        fit_split=FIT_SPLIT,
        patient_count=len(train_roster),
        train_roster_sha256=compute_roster_sha256(train_roster, Cohort.UTSW),
        split_manifest_sha256=_sha256_bytes(split_manifest_path),
        modalities=modalities,
    )


def _to_document(stats: NormalizationStats) -> dict[str, object]:
    return {
        "stats_version": STATS_VERSION,
        "fit_cohort": stats.fit_cohort,
        "fit_split": stats.fit_split,
        "patient_count": stats.patient_count,
        "train_roster_sha256": stats.train_roster_sha256,
        "split_manifest_sha256": stats.split_manifest_sha256,
        "patient_scale": PATIENT_SCALE,
        "statistic": (
            "pooled mean and population std (ddof=0) of brain voxels (!= 0) "
            "after dividing each volume by its own brain-voxel median"
        ),
        "modalities": {
            name: {"mean": m.mean, "std": m.std, "voxel_count": m.voxel_count}
            for name, m in stats.modalities.items()
        },
    }


def write_normalization_stats(path: Path, stats: NormalizationStats) -> Path:
    """Write the statistics once, atomically; an existing file is never replaced."""
    if path.exists():
        raise FileExistsError(f"normalization statistics already exist: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_to_document(stats), indent=2, sort_keys=True) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path


def load_normalization_stats(
    path: Path, *, expected_sha256: str | None = None
) -> NormalizationStats:
    """Read frozen statistics; when a digest is given, the bytes must match it."""
    if expected_sha256 is not None and _sha256_bytes(path) != expected_sha256:
        raise ValueError("normalization statistics do not match the expected SHA-256")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("stats_version") != STATS_VERSION:
        raise ValueError("unsupported normalization statistics version")
    if document.get("patient_scale") != PATIENT_SCALE:
        raise ValueError("statistics were fitted with a different patient scale")
    if (
        document["fit_cohort"] != Cohort.UTSW.value
        or document["fit_split"] != FIT_SPLIT
    ):
        raise ValueError("statistics were not fitted on the UTSW training split")
    raw = cast(Mapping[str, Mapping[str, float]], document["modalities"])
    if set(raw) != set(_SEQUENCE_NAMES):
        raise ValueError("statistics must cover exactly the four modalities")
    return NormalizationStats(
        fit_cohort=str(document["fit_cohort"]),
        fit_split=str(document["fit_split"]),
        patient_count=int(document["patient_count"]),
        train_roster_sha256=str(document["train_roster_sha256"]),
        split_manifest_sha256=str(document["split_manifest_sha256"]),
        modalities={
            name: ModalityStats(
                mean=float(raw[name]["mean"]),
                std=float(raw[name]["std"]),
                voxel_count=int(raw[name]["voxel_count"]),
            )
            for name in _SEQUENCE_NAMES
        },
    )


def normalize_volume(
    volume: np.ndarray, sequence: CanonicalSequence | str, stats: NormalizationStats
) -> np.ndarray:
    """Divide by the volume's own brain median, then apply the frozen z-score.

    Only brain voxels change; background stays exactly 0. The caller's array is
    never modified.
    """
    modality = stats.modalities[CanonicalSequence(sequence).value]
    scale = _patient_scale(_brain_voxels(volume))
    rescaled = np.array(volume, dtype=np.float64) / scale
    transform = NormalizeIntensity(
        subtrahend=[modality.mean],
        divisor=[modality.std],
        nonzero=True,
        channel_wise=True,
        dtype=np.float32,
    )
    normalized = np.asarray(
        transform(rescaled.astype(np.float32)[None]), dtype=np.float32
    )
    return normalized.reshape(np.shape(volume))

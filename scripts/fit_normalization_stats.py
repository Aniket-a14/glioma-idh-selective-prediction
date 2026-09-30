#!/usr/bin/env python3
"""T04.6: fit per-modality z-score statistics on the frozen UTSW training split."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import nibabel as nib
import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from glioma_selective.leakage.id_normalization import Cohort  # noqa: E402
from glioma_selective.preprocessing.cache import StageCache  # noqa: E402
from glioma_selective.preprocessing.normalize import (  # noqa: E402
    PatientMoments,
    fit_normalization_stats,
    patient_moments,
    write_normalization_stats,
)
from glioma_selective.utils import paths  # noqa: E402

_VOLUME_STAGE = "volume"
_SEQUENCES = ("T1", "T1ce", "T2", "FLAIR")
_COHORTS = {"utsw": Cohort.UTSW, "ucsf_pdgm": Cohort.UCSF_PDGM}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", default="utsw", choices=sorted(_COHORTS))
    parser.add_argument("--split", default="train")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _moments_for_patient(
    item: tuple[str, Mapping[str, str]],
) -> tuple[str, dict[str, PatientMoments]]:
    patient_id, files = item
    result: dict[str, PatientMoments] = {}
    for sequence in _SEQUENCES:
        image = nib.load(files[sequence])
        result[sequence] = patient_moments(np.asarray(image.dataobj, dtype=np.float32))
    return patient_id, result


def _volume_files(outputs: Mapping[str, object], cache: StageCache) -> dict[str, str]:
    files: dict[str, str] = {}
    for sequence in _SEQUENCES:
        entry = cache.get(_VOLUME_STAGE, str(outputs[sequence]))
        if entry is None:
            raise ValueError("a training volume is missing or fails its cache hash")
        files[sequence] = str(entry / "volume.nii.gz")
    return files


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if _COHORTS[args.cohort] is not Cohort.UTSW or args.split != "train":
        parser.error("statistics may only be fitted on the UTSW training split")
    manifests = paths.manifests_dir()
    split_path = manifests / "splits.json"
    stats_path = manifests / "normalization_stats.json"
    sidecar_path = manifests / "normalization_stats.json.sha256"
    if not args.dry_run and (stats_path.exists() or sidecar_path.exists()):
        raise FileExistsError(
            "normalization statistics already exist; a new version needs a "
            "decision-log entry"
        )
    train_ids = sorted(json.loads(split_path.read_text())["splits"]["train"])
    outputs = json.loads((manifests / "preprocessing_outputs.json").read_text())
    cache = StageCache(paths.processed_data_dir())
    work = [
        (patient_id, _volume_files(outputs["utsw"][patient_id], cache))
        for patient_id in train_ids
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        moments = dict(pool.map(_moments_for_patient, work, chunksize=4))
    stats = fit_normalization_stats(
        moments,
        cohort=_COHORTS[args.cohort],
        split_name=args.split,
        split_manifest_path=split_path,
    )
    print(f"patients: {stats.patient_count}")
    print(f"train_roster_sha256: {stats.train_roster_sha256}")
    print(f"split_manifest_sha256: {stats.split_manifest_sha256}")
    for name, modality in stats.modalities.items():
        print(
            f"{name}: mean={modality.mean!r} std={modality.std!r} "
            f"voxels={modality.voxel_count}"
        )
    if args.dry_run:
        return 0
    write_normalization_stats(stats_path, stats)
    digest = hashlib.sha256(stats_path.read_bytes()).hexdigest()
    with sidecar_path.open("x", encoding="ascii", newline="\n") as sidecar:
        sidecar.write(f"{digest}  normalization_stats.json\n")
    print(f"normalization_stats_sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

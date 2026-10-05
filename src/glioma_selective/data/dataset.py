"""UTSW-only dataset construction for reproducible Phase 06 training."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import nibabel as nib
import numpy as np
import torch
from nibabel.processing import resample_to_output
from torch.utils.data import DataLoader, Dataset, Sampler

from glioma_selective.data.adapters._common import CORE_SEQUENCES
from glioma_selective.leakage.id_normalization import Cohort, normalize_identifier
from glioma_selective.preprocessing.cache import StageCache
from glioma_selective.preprocessing.normalize import (
    NormalizationStats,
    normalize_volume,
)
from glioma_selective.training.augment import augment_sample
from glioma_selective.utils import paths

__all__ = ["IDHDataset", "load_split_patient_ids", "make_loader"]

_OUTPUT_SHAPE = (3, 96, 96, 96)
_SEQUENCES = tuple(sequence.value for sequence in CORE_SEQUENCES)


def _read_json_object(path: Path, context: str) -> Mapping[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read {context}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a JSON object")
    return cast(Mapping[str, object], value)


def load_split_patient_ids(split: str) -> list[str]:
    """Read one frozen UTSW split after verifying its SHA-256 sidecar."""
    allowed = {"train", "calibration", "internal_test"}
    if split not in allowed:
        raise ValueError("split must be train, calibration, or internal_test")
    manifest_path = paths.manifests_dir() / "splits.json"
    sidecar_path = manifest_path.with_name(manifest_path.name + ".sha256")
    try:
        expected = sidecar_path.read_text(encoding="ascii").split()[0]
        content = manifest_path.read_bytes()
    except (OSError, UnicodeError, IndexError) as error:
        raise ValueError(
            "a frozen split manifest and SHA-256 sidecar are required"
        ) from error
    actual = hashlib.sha256(content).hexdigest()
    if expected != actual:
        raise ValueError("split manifest does not match its frozen SHA-256")
    document = _read_json_object(manifest_path, "split manifest")
    splits = document.get("splits")
    if not isinstance(splits, dict):
        raise ValueError("split manifest has invalid split membership")
    patient_ids = splits.get(split)
    if not isinstance(patient_ids, list) or any(
        not isinstance(patient_id, str) for patient_id in patient_ids
    ):
        raise ValueError("split manifest has invalid UTSW patient membership")
    return list(cast(list[str], patient_ids))


def _load_nifti(path: Path) -> tuple[np.ndarray, np.ndarray]:
    image = cast(nib.Nifti1Image, nib.load(str(path)))
    return np.asarray(image.dataobj, dtype=np.float32), np.asarray(image.affine)


def _center_crop_or_pad(array: np.ndarray, center: np.ndarray) -> np.ndarray:
    """Center a 3-D array at ``center`` and return exactly 96 cubed."""
    target = np.asarray(_OUTPUT_SHAPE[1:], dtype=int)
    starts = np.asarray(center, dtype=int) - target // 2
    output = np.zeros(tuple(target), dtype=array.dtype)
    source_starts = np.maximum(starts, 0)
    source_ends = np.minimum(starts + target, np.asarray(array.shape))
    destination_starts = np.maximum(-starts, 0)
    lengths = np.maximum(source_ends - source_starts, 0)
    if np.any(lengths):
        source = tuple(
            slice(int(a), int(b))
            for a, b in zip(source_starts, source_ends, strict=True)
        )
        destination = tuple(
            slice(int(a), int(a + length))
            for a, length in zip(destination_starts, lengths, strict=True)
        )
        output[destination] = array[source]
    return output


def _resample_patient(
    volumes: Sequence[np.ndarray],
    affines: Sequence[np.ndarray],
    mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Normalize-grid volumes to 2 mm, align the mask, and center the brain."""
    reference_shape = volumes[0].shape
    reference_affine = affines[0]
    for volume, affine in zip(volumes[1:], affines[1:], strict=True):
        if volume.shape != reference_shape or not np.allclose(
            affine, reference_affine, atol=1e-4, rtol=0.0
        ):
            raise ValueError("cached UTSW modalities do not share one registered grid")
    brain = np.logical_or.reduce([volume != 0.0 for volume in volumes])
    if not np.any(brain):
        raise ValueError("normalized UTSW volumes contain no brain voxels")

    resampled_images: list[np.ndarray] = []
    for volume in volumes:
        image = nib.Nifti1Image(volume, reference_affine)
        resampled = resample_to_output(
            image, voxel_sizes=(2.0, 2.0, 2.0), order=1, mode="constant", cval=0.0
        )
        resampled_images.append(np.asarray(resampled.dataobj, dtype=np.float32))
    brain_image = nib.Nifti1Image(brain.astype(np.uint8), reference_affine)
    resampled_brain_image = resample_to_output(
        brain_image, voxel_sizes=(2.0, 2.0, 2.0), order=0, mode="constant", cval=0
    )
    resampled_brain = np.asarray(resampled_brain_image.dataobj) > 0

    if mask is None:
        resampled_mask = np.zeros(resampled_brain.shape, dtype=np.uint8)
    else:
        if mask.shape != reference_shape:
            raise ValueError(
                "cached UTSW segmentation does not share the registered grid"
            )
        mask_image = nib.Nifti1Image(mask.astype(np.uint8), reference_affine)
        resampled_mask_image = resample_to_output(
            mask_image,
            voxel_sizes=(2.0, 2.0, 2.0),
            order=0,
            mode="constant",
            cval=0,
        )
        resampled_mask = np.asarray(resampled_mask_image.dataobj, dtype=np.uint8)
    resampled_mask[~resampled_brain] = 0

    if not np.any(resampled_brain):
        raise ValueError("resampled UTSW volumes contain no brain voxels")
    coordinates = np.argwhere(resampled_brain)
    center = (coordinates.min(axis=0) + coordinates.max(axis=0)) // 2
    stacked = np.stack(resampled_images, axis=0)
    stacked[:, ~resampled_brain] = 0.0
    images = np.stack(
        [_center_crop_or_pad(channel, center) for channel in stacked], axis=0
    ).astype(np.float32, copy=False)
    cropped_mask = _center_crop_or_pad(resampled_mask, center)
    seg = np.stack([cropped_mask == class_id for class_id in (3, 1, 2)], axis=0).astype(
        np.float32
    )
    return images, seg


def _load_utsw_labels() -> dict[str, object]:
    # This existing reader opens only the UTSW source specified by metadata.py.
    from glioma_selective.splits.stratified import read_utsw_split_labels

    return cast(dict[str, object], read_utsw_split_labels())


class IDHDataset(Dataset[dict[str, Any]]):
    """UTSW-only IDH dataset with deterministic online augmentation."""

    def __init__(
        self,
        patient_ids: Sequence[str],
        *,
        stats: NormalizationStats,
        seed: int,
        augment: bool = False,
        zero_channels: Sequence[int] = (),
        storage: StageCache | Path | None = None,
    ) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if stats.fit_cohort != Cohort.UTSW.value or stats.fit_split != "train":
            raise ValueError("normalization statistics must be frozen on UTSW train")
        if set(stats.modalities) != set(_SEQUENCES):
            raise ValueError("normalization statistics must cover four UTSW modalities")
        channels = tuple(zero_channels)
        if any(
            isinstance(channel, bool)
            or not isinstance(channel, int)
            or channel not in range(4)
            for channel in channels
        ):
            raise ValueError("zero_channels entries must be indices from 0 to 3")
        labels = _load_utsw_labels()
        canonical_ids: list[str] = []
        dataset_labels: list[float] = []
        for patient_id in patient_ids:
            if not isinstance(patient_id, str):
                raise ValueError("patient IDs must be UTSW strings")
            try:
                canonical_id = normalize_identifier(patient_id, Cohort.UTSW)
            except ValueError as error:
                raise ValueError(
                    "patient IDs must belong to the UTSW cohort"
                ) from error
            label = labels.get(canonical_id)
            if label is None:
                raise ValueError("a requested UTSW patient has no IDH label")
            idh = getattr(label, "idh", None)
            if idh not in {"mutant", "wildtype"}:
                raise ValueError("a requested UTSW patient has no valid IDH label")
            canonical_ids.append(canonical_id)
            dataset_labels.append(1.0 if idh == "mutant" else 0.0)
        self.patient_ids = tuple(canonical_ids)
        self._labels = tuple(dataset_labels)
        self.stats = stats
        self.seed = seed
        self.augment = augment
        self.zero_channels = channels
        self.epoch = 0
        self.storage = storage
        if isinstance(storage, StageCache):
            self.cache = storage
        else:
            cache_root = storage if storage is not None else paths.processed_data_dir()
            self.cache = StageCache(cache_root)
        self._outputs = _read_json_object(
            paths.manifests_dir() / "preprocessing_outputs.json",
            "preprocessing output index",
        )

    @property
    def labels(self) -> tuple[float, ...]:
        """IDH labels in dataset order: 1.0 mutant, 0.0 wildtype."""
        return self._labels

    def set_epoch(self, epoch: int) -> None:
        """Set the epoch used to derive each sample's augmentation stream."""
        if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch < 0:
            raise ValueError("epoch must be a non-negative integer")
        self.epoch = epoch

    def _patient_entry(self, patient_id: str) -> Mapping[str, object]:
        cohorts = self._outputs.get("utsw")
        if not isinstance(cohorts, dict):
            raise ValueError("preprocessing output index has no UTSW records")
        entry = cohorts.get(patient_id)
        if not isinstance(entry, dict):
            raise ValueError("requested UTSW patient has no preprocessing outputs")
        return cast(Mapping[str, object], entry)

    def _load_patient(self, patient_id: str) -> tuple[np.ndarray, np.ndarray, bool]:
        entry = self._patient_entry(patient_id)
        volume_arrays: list[np.ndarray] = []
        affines: list[np.ndarray] = []
        for sequence in CORE_SEQUENCES:
            key = entry.get(sequence.value)
            if not isinstance(key, str) or not key:
                raise ValueError("a UTSW patient is missing a cached modality key")
            volume_entry = self.cache.get("volume", key)
            if volume_entry is None:
                raise ValueError("a cached UTSW volume is missing or fails its hash")
            volume, affine = _load_nifti(volume_entry / "volume.nii.gz")
            volume_arrays.append(normalize_volume(volume, sequence, self.stats))
            affines.append(affine)

        has_seg = entry.get("has_segmentation")
        if not isinstance(has_seg, bool):
            raise ValueError(
                "UTSW preprocessing outputs lack has_segmentation metadata"
            )
        raw_mask: np.ndarray | None = None
        mask_key = entry.get("mask")
        if has_seg:
            if not isinstance(mask_key, str) or not mask_key:
                raise ValueError("segmented UTSW patient lacks a cached mask key")
            mask_entry = self.cache.get("mask", mask_key)
            if mask_entry is None:
                raise ValueError("a cached UTSW mask is missing or fails its hash")
            raw_mask, mask_affine = _load_nifti(mask_entry / "mask.nii.gz")
            if not np.allclose(mask_affine, affines[0], atol=1e-4, rtol=0.0):
                raise ValueError(
                    "cached UTSW segmentation does not share the image grid"
                )
        images, seg = _resample_patient(volume_arrays, affines, raw_mask)
        if not has_seg:
            seg.fill(0.0)
        return images, seg, has_seg

    def __len__(self) -> int:
        return len(self.patient_ids)

    def __getitem__(self, index: int) -> dict[str, Any]:
        patient_id = self.patient_ids[index]
        image, seg, has_seg = self._load_patient(patient_id)
        image_tensor = torch.from_numpy(np.ascontiguousarray(image))
        for channel in self.zero_channels:
            image_tensor[channel].zero_()
        sample: dict[str, Any] = {
            "image": image_tensor,
            "seg": torch.from_numpy(np.ascontiguousarray(seg)),
            "has_seg": torch.tensor(has_seg, dtype=torch.bool),
            "label": torch.tensor(self._labels[index], dtype=torch.float32),
            "patient_id": patient_id,
        }
        if self.augment:
            rng = np.random.default_rng(
                np.random.SeedSequence([self.seed, self.epoch, index])
            )
            sample = augment_sample(sample, rng)
        return sample


class _EpochSampler(Sampler[int]):
    """Seeded sampler whose order is a pure function of seed and epoch."""

    def __init__(self, dataset: IDHDataset, seed: int, shuffle: bool) -> None:
        self.dataset = dataset
        self.seed = seed
        self.shuffle = shuffle

    def __iter__(self) -> Iterator[int]:
        if not self.shuffle:
            return iter(range(len(self.dataset)))
        generator = torch.Generator()
        generator.manual_seed(self.seed + self.dataset.epoch)
        return iter(torch.randperm(len(self.dataset), generator=generator).tolist())

    def __len__(self) -> int:
        return len(self.dataset)


def _collate(samples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "image": torch.stack(
            [cast(torch.Tensor, sample["image"]) for sample in samples]
        ),
        "seg": torch.stack([cast(torch.Tensor, sample["seg"]) for sample in samples]),
        "has_seg": torch.stack(
            [cast(torch.Tensor, sample["has_seg"]) for sample in samples]
        ),
        "label": torch.stack(
            [cast(torch.Tensor, sample["label"]) for sample in samples]
        ),
        "patient_id": [cast(str, sample["patient_id"]) for sample in samples],
    }


def _seed_worker(worker_id: int) -> None:
    """Seed worker-local third-party RNGs from PyTorch's assigned seed."""
    del worker_id
    torch.set_num_threads(1)
    worker_seed = torch.initial_seed() % (2**32)
    np.random.seed(worker_seed)


def make_loader(
    dataset: IDHDataset,
    *,
    batch_size: int,
    shuffle: bool,
    seed: int,
    num_workers: int,
) -> DataLoader[dict[str, Any]]:
    """Construct a reproducible loader with list-valued patient IDs."""
    if batch_size < 1 or num_workers < 0 or seed < 0:
        raise ValueError("batch_size and seed must be positive; workers non-negative")
    generator = torch.Generator()
    generator.manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        sampler=_EpochSampler(dataset, seed, shuffle),
        num_workers=num_workers,
        worker_init_fn=_seed_worker,
        generator=generator,
        collate_fn=_collate,
    )

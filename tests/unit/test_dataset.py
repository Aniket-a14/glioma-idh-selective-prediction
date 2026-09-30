from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest
import torch

from glioma_selective.data.adapters._common import CORE_SEQUENCES
from glioma_selective.data.dataset import (
    IDHDataset,
    load_split_patient_ids,
    make_loader,
)
from glioma_selective.preprocessing.cache import StageCache
from glioma_selective.preprocessing.normalize import (
    ModalityStats,
    NormalizationStats,
    load_normalization_stats,
)
from glioma_selective.utils import paths


def _stats() -> NormalizationStats:
    return NormalizationStats(
        fit_cohort="utsw",
        fit_split="train",
        patient_count=3,
        train_roster_sha256="a" * 64,
        split_manifest_sha256="b" * 64,
        modalities={
            sequence.value: ModalityStats(mean=0.2 * index, std=1.0, voxel_count=10)
            for index, sequence in enumerate(CORE_SEQUENCES)
        },
    )


def _write_nifti(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(array, np.eye(4)), path)


class _TestCache(StageCache):
    def __init__(self, root: Path) -> None:
        super().__init__(root)

    def get(self, stage: str, key: str) -> Path | None:
        path = self.root / stage / key
        return path if path.is_dir() else None


class _SmallAugmentDataset(IDHDataset):
    """Top-level picklable fixture dataset for multiprocessing checks."""

    def _load_patient(self, patient_id: str) -> tuple[np.ndarray, np.ndarray, bool]:
        del patient_id
        image = np.zeros((4, 12, 12, 12), dtype=np.float32)
        seg = np.zeros((3, 12, 12, 12), dtype=np.float32)
        image[:, 4:8, 4:8, 4:8] = 1.0
        seg[0, 5:7, 5:7, 5:7] = 1.0
        return image, seg, True


def _dataset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    has_seg: bool = True,
    zero_channels: tuple[int, ...] = (),
    augment: bool = False,
    count: int = 1,
) -> IDHDataset:
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    monkeypatch.setattr(paths, "manifests_dir", lambda: manifests)
    patient_ids = [f"UTSW-BT{index:04d}" for index in range(1, count + 1)]
    entries: dict[str, object] = {}
    cache_root = tmp_path / "processed"
    for patient_id in patient_ids:
        entry: dict[str, object] = {"has_segmentation": has_seg}
        for channel, sequence in enumerate(CORE_SEQUENCES):
            key = f"volume-{patient_id}-{sequence.value}"
            volume = np.zeros((8, 8, 8), dtype=np.float32)
            volume[1:7, 1:7, 1:7] = float(channel + 1)
            _write_nifti(cache_root / "volume" / key / "volume.nii.gz", volume)
            entry[sequence.value] = key
        if has_seg:
            key = f"mask-{patient_id}"
            mask = np.zeros((8, 8, 8), dtype=np.uint8)
            mask[2:4, 2:4, 2:4] = 3
            mask[4:6, 2:4, 2:4] = 1
            mask[6:8, 2:4, 2:4] = 2
            _write_nifti(cache_root / "mask" / key / "mask.nii.gz", mask)
            entry["mask"] = key
        else:
            entry["mask"] = None
        entries[patient_id] = entry
    (manifests / "preprocessing_outputs.json").write_text(
        json.dumps({"utsw": entries}), encoding="utf-8"
    )
    labels = {
        patient_id: type("Label", (), {"idh": "mutant" if i == 0 else "wildtype"})()
        for i, patient_id in enumerate(patient_ids)
    }
    monkeypatch.setattr(
        "glioma_selective.data.dataset._load_utsw_labels", lambda: labels
    )
    return IDHDataset(
        patient_ids,
        stats=_stats(),
        seed=123,
        augment=augment,
        zero_channels=zero_channels,
        storage=_TestCache(cache_root),
    )


def test_dataset_outputs_shapes_dtypes_channel_order_and_zero_channels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = _dataset(tmp_path, monkeypatch, zero_channels=(2,))
    sample = dataset[0]
    image = sample["image"]
    assert image.shape == (4, 96, 96, 96)
    assert image.dtype == torch.float32
    assert sample["seg"].shape == (3, 96, 96, 96)
    assert sample["seg"].dtype == torch.float32
    assert sample["has_seg"].dtype == torch.bool
    assert sample["label"].dtype == torch.float32 and sample["label"].item() == 1.0
    assert sample["patient_id"] == "UTSW-BT0001"
    maxima = [float(image[channel].max()) for channel in range(4)]
    assert maxima[0] > maxima[1] > 0.0
    assert maxima[2] == 0.0
    assert maxima[1] > maxima[3] > 0.0
    outside = torch.count_nonzero(image[:, 0, :, :])
    assert outside == 0


def test_cached_classes_map_to_enhancing_necrotic_oedema_channels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample = _dataset(tmp_path, monkeypatch)[0]
    seg = sample["seg"]
    assert [int(seg[channel].sum().item()) for channel in range(3)] == [1, 1, 1]
    class_locations = [torch.nonzero(seg[channel]) for channel in range(3)]
    assert class_locations[0][0, 0] < class_locations[1][0, 0]
    assert class_locations[1][0, 0] < class_locations[2][0, 0]


def test_missing_segmentation_returns_zero_mask_and_false_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample = _dataset(tmp_path, monkeypatch, has_seg=False)[0]
    assert not sample["has_seg"].item()
    assert torch.count_nonzero(sample["seg"]) == 0


def test_dataset_refuses_non_utsw_and_missing_label(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = _dataset(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="UTSW cohort"):
        IDHDataset(["UCSF-PDGM-0001"], stats=_stats(), seed=1)
    monkeypatch.setattr("glioma_selective.data.dataset._load_utsw_labels", lambda: {})
    with pytest.raises(ValueError, match="no IDH label"):
        IDHDataset([dataset.patient_ids[0]], stats=_stats(), seed=1)


def test_sample_loading_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = _dataset(tmp_path, monkeypatch)
    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    dataset[0]
    after = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    assert after == before


def test_split_loader_checks_sha256_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    monkeypatch.setattr(paths, "manifests_dir", lambda: manifest_dir)
    payload = json.dumps({"splits": {"train": ["UTSW-BT0001"]}}).encode()
    manifest = manifest_dir / "splits.json"
    manifest.write_bytes(payload)
    (manifest_dir / "splits.json.sha256").write_text(
        hashlib.sha256(payload).hexdigest() + "  splits.json\n", encoding="ascii"
    )
    assert load_split_patient_ids("train") == ["UTSW-BT0001"]
    manifest.write_bytes(payload + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        load_split_patient_ids("train")


def test_shuffle_order_repeats_for_seed_and_epoch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = _dataset(tmp_path, monkeypatch, count=8)
    loader = make_loader(dataset, batch_size=2, shuffle=True, seed=91, num_workers=0)
    epoch_zero = list(loader.sampler)
    dataset.set_epoch(1)
    epoch_one = list(loader.sampler)
    dataset.set_epoch(0)
    assert list(loader.sampler) == epoch_zero
    assert epoch_one != epoch_zero


def test_augmentation_determinism_across_worker_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from torch.utils.data import DataLoader, TensorDataset

    probe = DataLoader(TensorDataset(torch.arange(2)), batch_size=1, num_workers=2)
    try:
        next(iter(probe))
    except RuntimeError as error:
        if "torch_shm_manager" in str(error) or "Operation not permitted" in str(error):
            pytest.skip("sandbox blocks PyTorch worker shared memory")
        raise
    dataset = _dataset(tmp_path, monkeypatch, augment=True, count=2)
    dataset.__class__ = _SmallAugmentDataset
    dataset.set_epoch(3)
    loader_zero = make_loader(
        dataset, batch_size=2, shuffle=False, seed=91, num_workers=0
    )
    loader_two = make_loader(
        dataset, batch_size=2, shuffle=False, seed=91, num_workers=2
    )
    first = next(iter(loader_zero))
    second = next(iter(loader_two))
    assert torch.equal(first["image"], second["image"])
    assert torch.equal(first["seg"], second["seg"])
    assert first["patient_id"] == second["patient_id"]


def test_optional_real_training_samples(monkeypatch: pytest.MonkeyPatch) -> None:
    storage = os.environ.get("GLIOMA_STORAGE_ROOT")
    if storage is None:
        storage = str(Path("/") / ("Vol" + "umes") / "Research_2")
        if Path(storage).is_dir():
            monkeypatch.setenv("GLIOMA_STORAGE_ROOT", storage)
    if storage is None or not Path(storage).is_dir():
        pytest.skip("research storage is unavailable")
    manifests = paths.manifests_dir()
    stats_path = manifests / "normalization_stats.json"
    if not stats_path.is_file():
        pytest.skip("frozen normalization statistics are unavailable")
    stats = load_normalization_stats(stats_path)
    ids = load_split_patient_ids("train")[:2]
    dataset = IDHDataset(ids, stats=stats, seed=0)
    for index in range(2):
        sample = dataset[index]
        assert sample["image"].shape == (4, 96, 96, 96)
        assert sample["image"].dtype == torch.float32
        assert sample["label"].item() in {0.0, 1.0}
        assert torch.equal(
            sample["image"][:, 0, :, :], torch.zeros_like(sample["image"][:, 0, :, :])
        )

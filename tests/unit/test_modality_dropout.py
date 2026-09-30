"""Modality dropout schedule (D-041) and its use in the training loop."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from glioma_selective.models.segresnet import IDHNet, ModelConfig
from glioma_selective.training.loop import TrainConfig, fit
from glioma_selective.training.modality_dropout import (
    KEPT_SUBSETS,
    apply_modality_dropout,
    sample_dropped_channels,
)


def test_there_are_fourteen_non_empty_proper_subsets() -> None:
    assert len(KEPT_SUBSETS) == 14
    assert all(1 <= len(subset) <= 3 for subset in KEPT_SUBSETS)
    assert len(set(KEPT_SUBSETS)) == 14


def test_schedule_frequencies_match_the_definition() -> None:
    rng = np.random.default_rng(0)
    draws = [sample_dropped_channels(rng, 0.5) for _ in range(70_000)]
    counts = Counter(draws)
    assert counts[()] / len(draws) == pytest.approx(0.5, abs=0.01)
    # each of the 14 kept-subsets: probability 0.5 / 14 = 0.0357
    for subset in KEPT_SUBSETS:
        dropped = tuple(c for c in range(4) if c not in subset)
        assert counts[dropped] / len(draws) == pytest.approx(0.5 / 14, abs=0.005)
    assert (0, 1, 2, 3) not in counts  # never zero every sequence


def test_probability_one_never_drops_and_zero_always_drops() -> None:
    rng = np.random.default_rng(1)
    assert all(sample_dropped_channels(rng, 1.0) == () for _ in range(200))
    assert all(len(sample_dropped_channels(rng, 0.0)) >= 1 for _ in range(200))


def test_out_of_range_probability_is_an_error() -> None:
    with pytest.raises(ValueError):
        sample_dropped_channels(np.random.default_rng(0), 1.5)


def test_dropped_channels_are_exactly_zero_kept_are_unchanged_input_is_intact() -> None:
    image = torch.randn(6, 4, 3, 3, 3) + 5.0  # no accidental zeros
    original = image.clone()
    output = apply_modality_dropout(image, np.random.default_rng(3), 0.0)
    assert torch.equal(image, original)  # input not mutated
    for patient in range(6):
        for channel in range(4):
            if torch.count_nonzero(output[patient, channel]) == 0:
                continue  # dropped
            assert torch.equal(output[patient, channel], image[patient, channel])
        assert torch.count_nonzero(output[patient]) > 0  # at least one kept


def test_same_stream_gives_the_same_masks() -> None:
    image = torch.ones(8, 4, 2, 2, 2)
    first = apply_modality_dropout(image, np.random.default_rng(9), 0.5)
    second = apply_modality_dropout(image, np.random.default_rng(9), 0.5)
    assert torch.equal(first, second)


def test_bad_shape_is_an_error() -> None:
    with pytest.raises(ValueError):
        apply_modality_dropout(torch.ones(2, 3, 2, 2, 2), np.random.default_rng(0), 0.5)


class _Data:
    def __init__(self) -> None:
        g = torch.Generator().manual_seed(4)
        self.labels = torch.tensor([1.0, 0.0, 1.0, 0.0])
        self.images = torch.randn(4, 4, 8, 8, 8, generator=g) + 3.0
        self.seg = torch.zeros(4, 3, 8, 8, 8)
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch


class _Loader:
    def __init__(self, data: _Data) -> None:
        self.dataset = data

    def __iter__(self):  # type: ignore[no-untyped-def]
        for i in range(4):
            yield {
                "image": self.dataset.images[i : i + 1],
                "seg": self.dataset.seg[i : i + 1],
                "has_seg": torch.tensor([False]),
                "label": self.dataset.labels[i : i + 1],
            }


CONFIG = TrainConfig(
    max_epochs=2,
    accumulation_steps=2,
    learning_rate=1e-2,
    amp="off",
    early_stopping_patience=5,
    modality_dropout=True,
    modality_dropout_keep_all_probability=0.0,
)
SMALL = ModelConfig(
    init_filters=8, blocks_down=(1, 1, 1, 1), head_hidden=8, head_dropout=0.0
)


def _fit(directory: Path, config: TrainConfig, stop: int | None = None) -> IDHNet:
    torch.manual_seed(0)
    model = IDHNet(SMALL)
    loader = _Loader(_Data())
    fit(
        model,
        loader,
        loader,
        config,
        pos_weight=1.0,
        checkpoint_dir=directory,
        device=torch.device("cpu"),
        resume=stop is None and (directory / "last.pt").exists(),
        stop_after_steps=stop,
    )
    return model


def test_training_with_dropout_differs_from_training_without(tmp_path: Path) -> None:
    with_dropout = _fit(tmp_path / "a", CONFIG)
    without = _fit(tmp_path / "b", replace(CONFIG, modality_dropout=False))
    assert not all(
        torch.equal(a, b)
        for a, b in zip(with_dropout.parameters(), without.parameters(), strict=True)
    )


def test_resume_is_exact_with_modality_dropout(tmp_path: Path) -> None:
    straight = _fit(tmp_path / "a", CONFIG)
    _fit(tmp_path / "b", CONFIG, stop=1)
    resumed = _fit(tmp_path / "b", CONFIG)
    for a, b in zip(straight.parameters(), resumed.parameters(), strict=True):
        assert torch.equal(a, b)

"""Byte-level internal baseline captured before the Phase 12 cohort seam."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import torch
from scripts import freeze_predictions

from glioma_selective.evaluation import condition_sweep, freeze_mc_dropout
from glioma_selective.models import segresnet
from glioma_selective.models.segresnet import ModelConfig
from glioma_selective.tracking import run_record
from glioma_selective.training import checkpoint, run


def test_internal_freeze_and_sweep_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise both public drivers, including their artifact serializers."""
    from glioma_selective.data import dataset

    torch.set_num_threads(1)
    directory = tmp_path / "run"
    directory.mkdir()
    record = {
        "run_id": "synthetic",
        "seed": 4,
        "status": "completed",
        "git_dirty": False,
        "git_sha": "a" * 40,
        "checkpoint_hash": hashlib.sha256(b"weights").hexdigest(),
        "config": {"model": {"init_filters": 8, "head_hidden": 8}},
    }
    (directory / "checkpoints").mkdir()
    (directory / "checkpoints" / "best.pt").write_bytes(b"weights")
    monkeypatch.setattr(
        freeze_predictions, "_load_record", lambda _: (directory, record)
    )
    monkeypatch.setattr(
        freeze_mc_dropout, "_load_record", lambda _: (directory, record)
    )
    monkeypatch.setattr(freeze_predictions, "_current_git_sha", lambda: "a" * 40)
    monkeypatch.setattr(freeze_mc_dropout, "_current_git_sha", lambda: "a" * 40)
    monkeypatch.setattr(checkpoint, "load_model_weights", lambda *_: None)
    monkeypatch.setattr(run_record, "update_run_record", lambda *_a, **_kw: None)
    original_build = segresnet.build_model

    def build(_config: object) -> Any:
        torch.manual_seed(17)
        return original_build(ModelConfig(init_filters=8, head_hidden=8))

    monkeypatch.setattr(segresnet, "build_model", build)

    class StandIn:
        def __init__(
            self,
            ids: Any,
            *,
            stats: Any,
            seed: int,
            augment: bool = False,
            zero_channels: Any = (),
            storage: Any = None,
        ) -> None:
            self.patient_ids, self.stats, self.seed = tuple(ids), stats, seed
            self.storage, self.zero_channels = storage, zero_channels

        def __len__(self) -> int:
            return len(self.patient_ids)

        def __getitem__(self, index: int) -> dict[str, Any]:
            image = torch.stack(
                [torch.full((16, 16, 16), float(i + index + 1)) for i in range(4)]
            )
            for channel in self.zero_channels:
                image[channel].zero_()
            return {
                "patient_id": self.patient_ids[index],
                "image": image,
                "label": torch.tensor(float(index % 2)),
                "seg": torch.zeros((3, 16, 16, 16)),
                "has_seg": torch.tensor(True),
            }

    base = StandIn(["cal-a", "cal-b"], stats=object(), seed=4)
    monkeypatch.setattr(dataset, "IDHDataset", StandIn)
    monkeypatch.setattr(
        dataset, "load_split_patient_ids", lambda _: ["test-a", "test-b"]
    )
    monkeypatch.setattr(run, "_build_datasets", lambda _: (None, base, None))
    freeze_predictions.freeze_run("synthetic", device="cpu")
    condition_sweep.freeze_conditions("synthetic", passes=3, seed=9)
    digests = {
        path.relative_to(directory).as_posix(): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.suffix in {".parquet", ".json"}
    }
    expected = Path(__file__).parents[1] / "fixtures" / "phase12_internal_digests.json"
    assert digests == json.loads(expected.read_text()), json.dumps(digests, indent=2)

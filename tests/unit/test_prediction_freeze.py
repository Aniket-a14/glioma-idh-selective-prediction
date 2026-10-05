from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import torch
from scripts import freeze_predictions
from torch import nn

from glioma_selective.evaluation.freeze import predict_split, predict_split_with_dice
from glioma_selective.models.segresnet import ModelOutput
from glioma_selective.training import checkpoint
from glioma_selective.utils import paths


class _SyntheticDataset:
    def __init__(self) -> None:
        self.samples = [
            {
                "patient_id": f"UTSW-BT{index:04d}",
                "label": torch.tensor(index % 2, dtype=torch.float32),
                "image": torch.full((4, 2, 2, 2), float(index), dtype=torch.float32),
            }
            for index in (3, 1, 4, 2, 5)
        ]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return self.samples[index]


class _TinyModel(nn.Module):
    def __init__(self, column_logits: bool = False) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.tensor(0.25))
        self.column_logits = column_logits
        self.seen_eval: list[bool] = []

    def forward(self, image: torch.Tensor) -> ModelOutput:
        self.seen_eval.append(not self.training)
        values = image.mean(dim=(1, 2, 3, 4)) * self.weight
        return ModelOutput(values[:, None] if self.column_logits else values, None)


class _DiceDataset:
    def __init__(self) -> None:
        self.samples = []
        targets = [
            [[1, 0], [1, 0], [1, 1]],
            [[0, 0], [0, 0], [0, 0]],
            [[1, 1], [1, 0], [0, 0]],
        ]
        for index, target in enumerate(targets):
            self.samples.append(
                {
                    "patient_id": f"p{index}",
                    "label": torch.tensor(index % 2),
                    "image": torch.full((4, 1, 1, 1), float(index)),
                    "has_seg": torch.tensor(index != 1),
                    "seg": torch.tensor(target, dtype=torch.float32).reshape(
                        3, 1, 1, 2
                    ),
                }
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return self.samples[index]


class _DiceModel(_TinyModel):
    def forward(self, image: torch.Tensor) -> ModelOutput:
        values = image[:, 0, 0, 0, 0]
        templates = torch.tensor(
            [
                [[1, 0], [0, 0], [1, 0]],
                [[1, 0], [1, 0], [1, 1]],
                [[1, 1], [1, 0], [0, 0]],
            ],
            dtype=image.dtype,
            device=image.device,
        )
        seg_logits = templates[values.long()].reshape(-1, 3, 1, 1, 2) * 2 - 1
        return ModelOutput(values, seg_logits)


class _NoSegModel(_TinyModel):
    pass


@pytest.mark.parametrize("column_logits", [False, True])
def test_predict_split_preserves_order_and_matches_manual_forward(
    column_logits: bool,
) -> None:
    dataset = _SyntheticDataset()
    model = _TinyModel(column_logits)
    model.train()
    expected = []
    with torch.no_grad():
        for sample in dataset.samples:
            expected.append(float(model(sample["image"][None]).logit.reshape(-1)[0]))
    model.seen_eval.clear()
    predictions = predict_split(model, dataset, device="cpu", batch_size=2)
    assert [row["patient_id"] for row in predictions] == [
        sample["patient_id"] for sample in dataset.samples
    ]
    assert [row["logit"] for row in predictions] == pytest.approx(expected, abs=1e-6)
    assert all(model.seen_eval)
    assert not model.training
    assert [row["label"] for row in predictions] == [1, 1, 0, 0, 1]
    assert all(0.0 <= row["p_hat"] <= 1.0 for row in predictions)


def test_predict_split_with_dice_matches_patient_weighted_hand_calculation() -> None:
    predictions, dice = predict_split_with_dice(
        _DiceModel(), _DiceDataset(), device="cpu", batch_size=2
    )
    assert len(predictions) == 3
    assert dice["n_with_segmentation"] == 2
    assert dice["n_without_segmentation"] == 1
    per_channel = dice["per_channel"]
    assert per_channel["enhancing"] == pytest.approx(1.0)
    assert per_channel["necrotic_core"] == pytest.approx(0.5)
    assert per_channel["oedema"] == pytest.approx(5 / 6)
    assert dice["mean"] == pytest.approx((1 + 0.5 + 5 / 6) / 3)


def test_predict_split_with_dice_rejects_missing_segmentation_head() -> None:
    with pytest.raises(ValueError, match="seg_logits is None"):
        predict_split_with_dice(
            _NoSegModel(), _DiceDataset(), device="cpu", batch_size=2
        )


@pytest.fixture
def fake_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[str, Path, dict[str, Any]]:
    run_id = "01K6JQY7YGXSP6ZBZD3YF8QXPT"
    experiments = tmp_path / "artifacts" / "experiments"
    run_dir = experiments / run_id
    checkpoint_path = run_dir / "checkpoints" / "best.pt"
    checkpoint_path.parent.mkdir(parents=True)
    checkpoint_path.write_bytes(b"best model bytes")
    digest = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    record = {
        "run_id": run_id,
        "status": "completed",
        "git_dirty": False,
        "git_sha": "a" * 40,
        "checkpoint_hash": digest,
    }
    (run_dir / "record.json").write_text(json.dumps(record), encoding="utf-8")
    monkeypatch.setattr(paths, "experiments_dir", lambda: experiments)
    monkeypatch.setattr(freeze_predictions, "_current_git_sha", lambda: "a" * 40)
    monkeypatch.setattr(checkpoint, "file_sha256", lambda _path: digest)
    return run_id, checkpoint_path, record


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("status", "running", "status=completed"),
        ("git_dirty", True, "git_dirty=false"),
        ("checkpoint_hash", "f" * 64, "checkpoint_hash"),
    ],
)
def test_freeze_refuses_ineligible_run_record(
    fake_run: tuple[str, Path, dict[str, Any]],
    tmp_path: Path,
    field: str,
    value: Any,
    message: str,
) -> None:
    run_id, _checkpoint_path, record = fake_run
    record_path = tmp_path / "artifacts" / "experiments" / run_id / "record.json"
    record_path.write_text(json.dumps({**record, field: value}), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        freeze_predictions.freeze_run(run_id, device="cpu")


def test_freeze_refuses_git_sha_mismatch_and_reports_both(
    fake_run: tuple[str, Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _run_id, checkpoint_path, record = fake_run
    monkeypatch.setattr(freeze_predictions, "_current_git_sha", lambda: "c" * 40)
    with pytest.raises(ValueError, match="current git SHA c.*run git SHA a"):
        freeze_predictions.freeze_run(_run_id, device="cpu")
    current, recorded, _checkpoint = freeze_predictions._check_run(
        record, checkpoint_path, allow_sha_mismatch=True
    )
    assert current == "c" * 40
    assert recorded == "a" * 40


def test_freeze_cli_cannot_select_external_cohort_or_split() -> None:
    parser = freeze_predictions._parser()
    option_strings = {
        option for action in parser._actions for option in action.option_strings
    }
    assert "--cohort" not in option_strings
    assert "--split" not in option_strings
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["--run-id", "01K6JQY7YGXSP6ZBZD3YF8QXPT", "--cohort", "ucsf_pdgm"]
        )
    source = Path(freeze_predictions.__file__).read_text(encoding="utf-8")
    freeze_module = (
        Path(__file__).parents[2] / "src/glioma_selective/evaluation/freeze.py"
    )
    assert "GLIOMA_EXTERNAL_EVAL_AUTHORIZED" not in source
    assert "GLIOMA_EXTERNAL_EVAL_AUTHORIZED" not in freeze_module.read_text(
        encoding="utf-8"
    )

"""The four-patient overfit gate for Phase 06."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import torch

from glioma_selective.training.authorization import step_tiny_overfit

pytestmark = pytest.mark.integration


def test_synthetic_tiny_overfit_passes() -> None:
    result = step_tiny_overfit(
        "cpu", synthetic=True, max_steps=150, overfit_threshold=0.05
    )

    assert result.status == "passed", result.detail
    assert "steps=" in result.detail and "final_loss=" in result.detail


def test_synthetic_tiny_overfit_fails_without_learning() -> None:
    result = step_tiny_overfit(
        "cpu", synthetic=True, max_steps=5, overfit_threshold=0.05, learning_rate=0.0
    )

    assert result.status == "failed", result.detail


def test_real_four_patient_tiny_overfit_when_gpu_data_are_available() -> None:
    storage_root = os.environ.get("GLIOMA_STORAGE_ROOT")
    if not storage_root:
        pytest.skip("GLIOMA_STORAGE_ROOT is not set")
    root = Path(storage_root)
    manifests = root / "data" / "manifests"
    required = (
        manifests / "splits.json",
        manifests / "splits.json.sha256",
        manifests / "normalization_stats.json",
        manifests / "normalization_stats.json.sha256",
        manifests / "preprocessing_outputs.json",
    )
    if not all(path.is_file() for path in required):
        pytest.skip(
            "frozen UTSW training data and normalization manifests are unavailable"
        )
    if not torch.cuda.is_available():
        pytest.skip("no CUDA device; real 4-patient overfit is pending the GPU server")

    result = step_tiny_overfit("cuda", max_steps=150, overfit_threshold=0.05)
    assert result.status == "passed", result.detail

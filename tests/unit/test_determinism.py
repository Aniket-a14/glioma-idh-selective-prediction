"""The deterministic-mode context turns the flags on and puts the old ones back."""

from __future__ import annotations

import torch

from glioma_selective.training.determinism import deterministic_mode


def test_flags_are_on_inside_and_restored_after() -> None:
    before = (
        torch.backends.cudnn.deterministic,
        torch.backends.cudnn.benchmark,
        torch.are_deterministic_algorithms_enabled(),
        torch.is_deterministic_algorithms_warn_only_enabled(),
    )
    with deterministic_mode():
        assert torch.backends.cudnn.deterministic is True
        assert torch.backends.cudnn.benchmark is False
        assert torch.are_deterministic_algorithms_enabled()
        assert torch.is_deterministic_algorithms_warn_only_enabled()
    after = (
        torch.backends.cudnn.deterministic,
        torch.backends.cudnn.benchmark,
        torch.are_deterministic_algorithms_enabled(),
        torch.is_deterministic_algorithms_warn_only_enabled(),
    )
    assert after == before


def test_flags_are_restored_when_the_body_raises() -> None:
    before = torch.are_deterministic_algorithms_enabled()
    try:
        with deterministic_mode():
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    assert torch.are_deterministic_algorithms_enabled() == before

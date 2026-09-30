"""Deterministic GPU algorithms for runs that must resume bit for bit."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

import torch

__all__ = ["CUBLAS_WORKSPACE_CONFIG", "deterministic_mode"]

CUBLAS_WORKSPACE_CONFIG = ":4096:8"


@contextmanager
def deterministic_mode() -> Iterator[None]:
    """Turn on deterministic cuDNN and torch algorithms, then restore the old flags.

    Without this, two identical CUDA runs differ by about 5e-5 in the parameters
    after three optimizer steps (measured on an RTX 2060 SUPER), which is as large
    as the difference a resumed run shows, so resume equivalence cannot be judged.
    With it, both differences are exactly 0. ``CUBLAS_WORKSPACE_CONFIG`` should be
    set before CUDA is first used (``scripts/authorize_training.py`` does this); it
    is set here as a fallback. Operations with no deterministic version only warn.
    """
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", CUBLAS_WORKSPACE_CONFIG)
    previous = (
        torch.backends.cudnn.deterministic,
        torch.backends.cudnn.benchmark,
        torch.are_deterministic_algorithms_enabled(),
        torch.is_deterministic_algorithms_warn_only_enabled(),
    )
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True, warn_only=True)
    try:
        yield
    finally:
        torch.backends.cudnn.deterministic = previous[0]
        torch.backends.cudnn.benchmark = previous[1]
        torch.use_deterministic_algorithms(previous[2], warn_only=previous[3])

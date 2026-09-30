"""Classification head: pooled encoder features to one IDH-mutant logit."""

from __future__ import annotations

import torch
from torch import nn

__all__ = ["ClassificationHead"]


class ClassificationHead(nn.Module):
    """Two linear layers with ReLU and dropout; outputs a logit, not a probability."""

    def __init__(self, in_features: int, hidden: int, dropout: float) -> None:
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(in_features, hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(hidden, 1),
        )

    def forward(self, pooled: torch.Tensor) -> torch.Tensor:
        logit: torch.Tensor = self.layers(pooled).squeeze(-1)
        return logit

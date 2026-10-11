"""Head-only MC-dropout (M3, D-048).

The only dropout layer in the model sits inside the classification head
(``models/heads.py``), so the backbone runs once per patient in eval mode and the
head is run ``passes`` times with its dropout layers switched on. This cannot express
backbone uncertainty; the paper says so (D-048).
"""

from __future__ import annotations

import torch
from torch import nn

from glioma_selective.models.segresnet import IDHNet

__all__ = ["DEFAULT_PASSES", "mc_dropout_probabilities"]

DEFAULT_PASSES = 30


def _dropout_layers(head: nn.Module) -> list[nn.Dropout]:
    return [module for module in head.modules() if isinstance(module, nn.Dropout)]


@torch.no_grad()
def mc_dropout_probabilities(
    model: IDHNet,
    image: torch.Tensor,
    *,
    passes: int = DEFAULT_PASSES,
    generator: torch.Generator | None = None,
) -> torch.Tensor:
    """Sigmoid probabilities of ``passes`` stochastic head passes, ``[B, passes]``.

    Features come from one eval-mode backbone pass. The dropout layers are switched on
    only for the head passes and switched back to their previous mode afterwards. A
    ``generator`` makes the masks reproducible; without one the global RNG is used.
    """
    if passes < 1:
        raise ValueError("passes must be positive")
    layers = _dropout_layers(model.head)
    if not layers:
        raise ValueError("the classification head has no dropout layer")
    was_training = [layer.training for layer in layers]
    pooled, _ = model.pooled_features(image)
    pooled = pooled.detach()
    samples: list[torch.Tensor] = []
    try:
        for layer in layers:
            layer.train()
        for _ in range(passes):
            samples.append(_head_pass(model.head, pooled, generator))
    finally:
        for layer, mode in zip(layers, was_training, strict=True):
            layer.train(mode)
    logits = torch.stack(samples, dim=1)
    return torch.sigmoid(logits.to(torch.float64)).to(torch.float32)


def _head_pass(
    head: nn.Module, pooled: torch.Tensor, generator: torch.Generator | None
) -> torch.Tensor:
    """One head pass; masks are drawn from ``generator`` when one is given."""
    if generator is None:
        out: torch.Tensor = head(pooled)
        return out
    hidden = pooled
    for layer in head.layers:  # type: ignore[union-attr]
        if isinstance(layer, nn.Dropout) and layer.training:
            keep = 1.0 - layer.p
            mask = torch.bernoulli(torch.full_like(hidden, keep), generator=generator)
            hidden = hidden * mask / keep
        else:
            hidden = layer(hidden)
    return hidden.squeeze(-1)

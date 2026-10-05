"""Conformal risk control, the named secondary of D-002 (K4 of the Phase 07 contract).

The controlled risk is ``P(accepted and wrong)``, the expectation of the bounded
loss ``1[confidence >= tau and prediction != label]`` (B = 1), which is
non-increasing in ``tau``. It is not the conditional selective risk, which is a
ratio; the realized selective risk is reported next to it (D-045).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction

__all__ = ["accept", "confidence", "crc_threshold"]


def _exact(value: float) -> Fraction:
    return Fraction(repr(float(value)))


def _probability(value: float) -> Fraction:
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError("probability must be finite and in [0, 1]")
    return _exact(number)


def confidence(p_hat: float) -> float:
    """``max(p_hat, 1 - p_hat)``, computed exactly then rounded once to a double."""
    probability = _probability(p_hat)
    return float(max(probability, 1 - probability))


def accept(p_hat: float, tau: float) -> bool:
    """Accept a patient iff its confidence is at least ``tau``."""
    return confidence(p_hat) >= tau


def crc_threshold(p_hat: Sequence[float], labels: Sequence[int], alpha: float) -> float:
    """Smallest confidence threshold with corrected risk at most ``alpha`` (K4).

    Candidates are the unique calibration confidences plus ``+inf``. A threshold
    ``tau`` qualifies when ``n/(n+1) * R(tau) + 1/(n+1) <= alpha`` with
    ``R(tau)`` the mean loss, compared exactly. If none qualifies the answer is
    ``+inf`` (accept nobody).
    """
    if len(p_hat) == 0:
        raise ValueError("p_hat must not be empty")
    if len(p_hat) != len(labels):
        raise ValueError("p_hat and labels must have equal lengths")
    level = float(alpha)
    if not math.isfinite(level) or not 0.0 < level < 1.0:
        raise ValueError("alpha must be finite and in (0, 1)")
    exact_alpha = _exact(level)
    n = len(p_hat)
    confidences: list[float] = []
    wrong: list[bool] = []
    for p, y in zip(p_hat, labels, strict=True):
        if y not in (0, 1):
            raise ValueError("labels must be 0 or 1")
        probability = _probability(p)
        predicted = 1 if probability >= Fraction(1, 2) else 0
        confidences.append(confidence(p))
        wrong.append(predicted != y)
    scale = Fraction(n, n + 1)
    slack = Fraction(1, n + 1)
    for tau in sorted(set(confidences)):
        errors = sum(
            1 for c, w in zip(confidences, wrong, strict=True) if w and c >= tau
        )
        if scale * Fraction(errors, n) + slack <= exact_alpha:
            return tau
    return math.inf

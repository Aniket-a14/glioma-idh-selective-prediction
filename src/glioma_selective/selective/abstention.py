"""Per-mechanism confidence scores for the score-threshold view (S6, T09.1).

Every function returns scores where higher means more confident (accepted
first), the convention of ``selective/risk_coverage.py``.

- M1 raw and M2 temperature-scaled: ``confidence_scores`` of the raw or scaled
  probability of the IDH-mutant class.
- M3 MC-dropout: minus the entropy of the mean MC probability.
- M4 deep ensemble: minus the population variance of the member probabilities.
- M5 conformal, score-threshold view: the same ``confidence_scores`` of the
  temperature-scaled probability. M1, M2 and M5 therefore rank patients
  identically (D-047); they differ in operating points and in the set-valued
  coverage analysis only.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "binary_entropy",
    "confidence_scores",
    "ensemble_variance_scores",
    "mc_dropout_scores",
]


def _probability(value: float) -> Fraction:
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError("probability must be finite and in [0, 1]")
    return Fraction(repr(number))


def confidence_scores(p_hat: Sequence[float]) -> list[float]:
    """``max(p, 1 - p)`` per patient, computed exactly so that ties are exact."""
    if len(p_hat) == 0:
        raise ValueError("p_hat must not be empty")
    scores = []
    for value in p_hat:
        probability = _probability(value)
        scores.append(float(max(probability, 1 - probability)))
    return scores


def binary_entropy(probability: float) -> float:
    """``-q ln q - (1 - q) ln (1 - q)`` in nats, with ``0 ln 0 = 0``."""
    q = float(probability)
    if not math.isfinite(q) or not 0.0 <= q <= 1.0:
        raise ValueError("probability must be finite and in [0, 1]")
    if q in (0.0, 1.0):
        return 0.0
    return float(-q * math.log(q) - (1.0 - q) * math.log(1.0 - q))


def _matrix(
    values: Sequence[Sequence[float]] | NDArray[np.floating],
) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError("expected a non-empty patients-by-samples matrix")
    if not np.all(np.isfinite(array)) or np.any((array < 0.0) | (array > 1.0)):
        raise ValueError("probabilities must be finite and in [0, 1]")
    return array


def mc_dropout_scores(
    mc_probs: Sequence[Sequence[float]] | NDArray[np.floating],
) -> list[float]:
    """Minus the binary entropy of the mean probability over the MC passes."""
    array = _matrix(mc_probs)
    return [-binary_entropy(float(mean)) for mean in array.mean(axis=1)]


def ensemble_variance_scores(
    member_probs: Sequence[Sequence[float]] | NDArray[np.floating],
) -> list[float]:
    """Minus the population variance (divide by N) of the member probabilities."""
    array = _matrix(member_probs)
    return [-float(variance) for variance in array.var(axis=1, ddof=0)]

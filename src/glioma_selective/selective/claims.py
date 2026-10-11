"""Decision rules for claims C1-C6 (D1-D4).

Contract: ``docs/research/protocols/PHASE09_STATS_CONTRACTS.md``; the rules are
those of ``STATISTICAL_ANALYSIS_PLAN.md`` section 5 and D-050. Every threshold
comparison is exact (``Fraction(repr(x))``), so an interval limit that equals a
threshold is decided by the written rule, not by float rounding. The rules only
read numbers already computed; they never resample.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

__all__ = [
    "DeviationLabel",
    "Status",
    "deviation_label",
    "status_c4",
    "status_c5",
    "status_c6",
    "status_risk_difference",
    "worst_status",
]

Status = Literal["supported", "inconclusive", "refuted"]
_SEVERITY: dict[str, int] = {"supported": 0, "inconclusive": 1, "refuted": 2}
_C6_ALPHA = Fraction(1, 20)


def _exact(value: float | Fraction, what: str) -> Fraction:
    if isinstance(value, Fraction):
        return value
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{what} must be finite")
    return Fraction(repr(number))


def _exact_list(values: Sequence[float | Fraction], what: str) -> list[Fraction]:
    if len(values) == 0:
        raise ValueError(f"{what} must not be empty")
    return [_exact(v, what) for v in values]


def _paired(
    first: Sequence[float | Fraction], second: Sequence[float | Fraction]
) -> None:
    if len(first) != len(second):
        raise ValueError("inputs must have equal lengths")


def status_risk_difference(points: Sequence[float], uppers: Sequence[float]) -> Status:
    """C1, C2, C3: selective risk minus always-predict risk, per grid coverage (D1).

    ``points[i]`` is the point estimate of the difference and ``uppers[i]`` the
    upper 95% limit of its paired bootstrap. Refuted when any point estimate is
    at or above zero; otherwise supported when every upper limit is below zero;
    otherwise inconclusive.
    """
    _paired(points, uppers)
    point = _exact_list(points, "points")
    upper = _exact_list(uppers, "uppers")
    if any(p >= 0 for p in point):
        return "refuted"
    if all(u < 0 for u in upper):
        return "supported"
    return "inconclusive"


def status_c5(points: Sequence[float], lowers: Sequence[float]) -> Status:
    """C5: risk change between adjacent grid coverages (D2, D-050 reading a).

    ``points[k]`` is the risk at the lower coverage minus the risk at the next
    higher coverage (an increase is positive); ``lowers[k]`` is the lower 95%
    limit of its paired bootstrap. Refuted when any lower limit is above zero;
    otherwise supported when no point estimate is above zero; otherwise
    inconclusive.
    """
    _paired(points, lowers)
    point = _exact_list(points, "points")
    lower = _exact_list(lowers, "lowers")
    if any(low > 0 for low in lower):
        return "refuted"
    if all(p <= 0 for p in point):
        return "supported"
    return "inconclusive"


def status_c6(
    observed: Sequence[float], adjusted_p: Sequence[float | Fraction]
) -> Status:
    """C6: abstained-minus-overall error rate and its BH-adjusted p per coverage (D3).

    Refuted when any observed difference is at or below zero; otherwise
    supported when every adjusted p-value is strictly below 0.05; otherwise
    inconclusive.
    """
    _paired(observed, adjusted_p)
    obs = _exact_list(observed, "observed")
    adjusted = _exact_list(adjusted_p, "adjusted_p")
    if any(o <= 0 for o in obs):
        return "refuted"
    if all(p < _C6_ALPHA for p in adjusted):
        return "supported"
    return "inconclusive"


@dataclass(frozen=True)
class DeviationLabel:
    """C4 reading of one interval of coverage deviation (D4)."""

    half_width: float
    characterized: bool
    label: Literal["preserved", "degraded", "indeterminate"]


def deviation_label(lo: float, hi: float, band: float) -> DeviationLabel:
    """Label a coverage-deviation interval against a band (D4, D-050 reading b).

    ``characterized`` is ``(hi - lo) / 2 <= band``. ``preserved``: the interval
    lies inside ``[-band, band]``. ``degraded``: it lies wholly below ``-band``
    or wholly above ``band``. Anything else is ``indeterminate``.
    """
    low = _exact(lo, "lo")
    high = _exact(hi, "hi")
    width = _exact(band, "band")
    if low > high:
        raise ValueError("lo must not exceed hi")
    if width <= 0:
        raise ValueError("band must be positive")
    half = (high - low) / 2
    if -width <= low and high <= width:
        label: Literal["preserved", "degraded", "indeterminate"] = "preserved"
    elif high < -width or low > width:
        label = "degraded"
    else:
        label = "indeterminate"
    return DeviationLabel(float(half), half <= width, label)


def status_c4(intervals: Sequence[tuple[float, float]], band: float) -> Status:
    """C4: refuted when any condition's interval is wider than the band allows (D4).

    The claim is that the deviation can be characterized, so it is supported
    when every interval has half-width at most ``band`` and refuted when any
    has more. There is no inconclusive outcome (SAP section 5, "not applicable").
    """
    if len(intervals) == 0:
        raise ValueError("intervals must not be empty")
    labels = [deviation_label(lo, hi, band) for lo, hi in intervals]
    return "supported" if all(item.characterized for item in labels) else "refuted"


def worst_status(statuses: Sequence[Status]) -> Status:
    """Claim-level status: the most severe per-condition status."""
    if len(statuses) == 0:
        raise ValueError("statuses must not be empty")
    for status in statuses:
        if status not in _SEVERITY:
            raise ValueError(f"unknown status: {status!r}")
    return max(statuses, key=lambda s: _SEVERITY[s])

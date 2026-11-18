"""Nominal versus stored empirical conformal coverage; never construct a new CI."""

from __future__ import annotations

from typing import Any

import numpy as np
from matplotlib.figure import Figure

from glioma_selective.visualization.risk_coverage import (
    condition_panels,
    probability_axes,
)
from glioma_selective.visualization.tables import (
    CONFORMAL_VARIANTS,
    COVERAGE_BAND,
    conformal_alphas,
)


def coverage_figure(document: dict[str, Any]) -> tuple[Figure, str]:
    """Fig 3: show both named variants; the band is the frozen tolerance, not a CI."""
    conditions = sorted(document["conformal"])
    fig, axes, _ = condition_panels(conditions)
    for condition, ax in zip(conditions, axes, strict=True):
        nominal_axis = np.asarray([0, 1])
        ax.fill_between(
            nominal_axis,
            nominal_axis - COVERAGE_BAND,
            nominal_axis + COVERAGE_BAND,
            color="gray",
            alpha=0.15,
            label=f"Frozen tolerance +/-{COVERAGE_BAND}",
        )
        ax.plot(nominal_axis, nominal_axis, "--", color="gray")
        for variant in CONFORMAL_VARIANTS:
            entries = conformal_alphas(document["conformal"][condition], variant)
            ax.plot(
                [1 - float(alpha) for alpha, _ in entries],
                [cell["empirical_coverage"] for _, cell in entries],
                "o",
                label=variant,
            )
        probability_axes(
            ax, "Nominal coverage (1 - alpha)", "Empirical prediction-set coverage"
        )
        ax.legend(fontsize=7)
    return fig, (
        "Nominal versus empirical prediction-set coverage under complete and simulated "
        "missing modalities, for carried-over and refit variants. The "
        "shaded band is the "
        f"frozen +/-{COVERAGE_BAND} tolerance, not an interval estimate. "
        "intervals and their stored classifications appear in Table 4; they are not "
        "empirical-coverage intervals."
    )

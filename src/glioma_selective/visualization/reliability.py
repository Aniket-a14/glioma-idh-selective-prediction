"""Raw and frozen-temperature reliability diagrams using the existing binning code."""

from __future__ import annotations

from typing import Any

from matplotlib.figure import Figure

from glioma_selective.calibration.temperature import apply_temperature
from glioma_selective.evaluation.calibration_metrics import reliability_bins
from glioma_selective.visualization.risk_coverage import (
    condition_panels,
    probability_axes,
)


def reliability_figure(
    frames: dict[str, Any], temperature: float, cohort: str
) -> tuple[Figure, str]:
    """Fig 4 transforms logits with the stored temperature; it never refits it."""
    conditions = sorted(frames)
    fig, axes, _ = condition_panels(conditions)
    for condition, ax in zip(conditions, axes, strict=True):
        frame = frames[condition]
        selected = frame[
            (frame["cohort"] == cohort) & (frame["modality_condition"] == condition)
        ].sort_values("patient_id")
        if selected.empty:
            raise ValueError(f"no reliability rows for {cohort}/{condition}")
        if selected["patient_id"].duplicated().any():
            raise ValueError("duplicate reliability patient IDs")
        labels = selected["label"].to_numpy()
        scaled = apply_temperature(selected["logit"].to_numpy(), temperature)
        for name, values in (
            ("raw", selected["p_hat"].to_numpy()),
            ("temperature-scaled", scaled),
        ):
            bins = reliability_bins(values, labels)
            occupied = [entry for entry in bins if entry["count"]]
            ax.plot(
                [entry["mean_p"] for entry in occupied],
                [entry["frac_pos"] for entry in occupied],
                "o-",
                label=name,
            )
        ax.plot([0, 1], [0, 1], "--", color="gray")
        probability_axes(
            ax, "Mean predicted probability", "Observed IDH-mutant fraction"
        )
        ax.legend(fontsize=7)
    return fig, (
        "Raw and temperature-scaled reliability under complete and simulated missing "
        "modalities. Equal-width bins use the existing "
        "calibration_metrics.reliability_bins "
        "implementation; empty bins are unplotted. The temperature is copied from the "
        "frozen analysis; no calibration is fitted here."
    )

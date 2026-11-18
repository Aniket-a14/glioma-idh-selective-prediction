"""Plot the frozen rejected-but-correct rate, without estimating new quantities."""

from __future__ import annotations

from typing import Any

from matplotlib.figure import Figure

from glioma_selective.visualization.risk_coverage import (
    absent_slots,
    condition_panels,
    probability_axes,
)
from glioma_selective.visualization.tables import MECHANISMS, operating_points


def abstention_figure(document: dict[str, Any]) -> tuple[Figure, str]:
    """Fig 5 uses attained coverage, preserving tie-block behavior from the file."""
    conditions = sorted(document["conditions"])
    fig, axes, slots = condition_panels(conditions)
    for condition, ax, slot in zip(conditions, axes, slots, strict=True):
        cells = document["conditions"][condition]
        for color_index, mechanism in enumerate(MECHANISMS):
            cell = cells[mechanism]
            if cell.get("absent") is True:
                continue
            operations = [op for _, op in operating_points(cell)]
            ax.plot(
                [op["attained_coverage"] for op in operations],
                [op["rejected_but_correct_rate"] for op in operations],
                "o-",
                label=mechanism,
                color=f"C{color_index}",
            )
        probability_axes(ax, "Attained coverage", "Rejected-but-correct rate")
        absent_slots(slot, cells)
        ax.legend(fontsize=7)
    return fig, (
        "Abstention versus error under complete and simulated missing modalities: "
        "stored rejected-but-correct rates at each operating point, plotted against "
        "attained coverage. No rejected-but-correct intervals are stored; none are "
        "estimated here. Empty labelled slots retain absent mechanisms and reasons."
    )

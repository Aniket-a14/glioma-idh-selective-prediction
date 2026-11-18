"""Frozen risk-coverage curves and deterministic shared figure rendering.

All rc_points are drawn verbatim. Only the stored operating points have
intervals: horizontal attained-coverage and vertical selective-risk intervals.
No interpolation, bootstrap, smoothing or curve thinning is performed.
"""

from __future__ import annotations

import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

from glioma_selective.visualization.tables import (  # noqa: E402
    MECHANISMS,
    condition_label,
    operating_points,
)

PANEL_COLUMNS = 2
PANEL_WIDTH = 7
PANEL_HEIGHT = 5
COMPACT_PANEL_HEIGHT = 3.6
FLOW_SIZE = (10, 6)
PLOT_STYLE: dict[Any, Any] = {
    "path.simplify": False,
    "agg.path.chunksize": 0,
    "backend": "Agg",
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "svg.hashsalt": "glioma-phase13",
    "figure.dpi": 100,
    "savefig.dpi": 100,
    "pdf.fonttype": 42,
}
PROBABILITY_LIMITS = (0, 1)
DIGEST_PREFIX_LENGTH = 12


@contextmanager
def figure_style() -> Iterator[None]:
    """Contain all style changes so regeneration is independent of user defaults."""
    with matplotlib.rc_context():
        matplotlib.rcdefaults()
        matplotlib.rcParams.update(PLOT_STYLE)
        yield


def condition_panels(
    conditions: list[str], absent_conditions: set[str] | None = None
) -> tuple[Figure, list[Any], list[Any]]:
    """One condition per panel; a slot for absent cells only where one exists.

    ``absent_conditions`` names the conditions that have an absent cell. ``None``
    keeps the original layout (a reserved slot under every panel). An empty set
    gives compact panels with no slot, so a figure with nothing absent has no
    blank bands; the returned slot is then ``None``.
    """
    reserve = absent_conditions is None or bool(absent_conditions)
    rows = (len(conditions) + PANEL_COLUMNS - 1) // PANEL_COLUMNS
    height = PANEL_HEIGHT if reserve else COMPACT_PANEL_HEIGHT
    fig = Figure(figsize=(PANEL_WIDTH * PANEL_COLUMNS, height * rows))
    FigureCanvasAgg(fig)
    grid = fig.add_gridspec(
        rows, PANEL_COLUMNS, hspace=0.35 if reserve else 0.45, wspace=0.3
    )
    axes, slots = [], []
    for index, condition in enumerate(conditions):
        cell = grid[index // PANEL_COLUMNS, index % PANEL_COLUMNS]
        if reserve:
            nested = cell.subgridspec(2, 1, height_ratios=(4, 1.5), hspace=0.75)
            ax = fig.add_subplot(nested[0])
            slot = fig.add_subplot(nested[1])
            slot.set_axis_off()
        else:
            ax = fig.add_subplot(cell)
            slot = None
        ax.set_title(condition_label(condition))
        axes.append(ax)
        slots.append(slot)
    return fig, axes, slots


def conditions_with_absent(document: dict[str, Any]) -> set[str]:
    """Conditions in which at least one mechanism cell is absent."""
    return {
        condition
        for condition, cells in document["conditions"].items()
        if any(cells[name].get("absent") is True for name in MECHANISMS)
    }


def absent_slots(slot: Any, cells: dict[str, Any]) -> None:
    """Keep an empty labelled slot, including its source reason, for each absence."""
    if slot is None:
        return
    absent = [
        (name, cells[name]["reason"])
        for name in MECHANISMS
        if cells[name].get("absent") is True
    ]
    for index, (name, reason) in enumerate(absent):
        slot.text(
            0,
            1 - index / len(absent),
            textwrap.fill(f"{name}: absent\n{reason}", width=75),
            va="top",
            transform=slot.transAxes,
            fontsize=8,
            bbox={"facecolor": "none", "edgecolor": "gray"},
        )


def probability_axes(ax: Any, xlabel: str, ylabel: str) -> None:
    ax.set(
        xlim=PROBABILITY_LIMITS, ylim=PROBABILITY_LIMITS, xlabel=xlabel, ylabel=ylabel
    )
    ax.grid(alpha=0.2)


def risk_coverage_figure(document: dict[str, Any]) -> tuple[Figure, str]:
    """Fig 2, including both stored interval axes at every operating point."""
    conditions = sorted(document["conditions"])
    fig, axes, slots = condition_panels(conditions, conditions_with_absent(document))
    for condition, ax, slot in zip(conditions, axes, slots, strict=True):
        cells = document["conditions"][condition]
        for color_index, mechanism in enumerate(MECHANISMS):
            cell = cells[mechanism]
            if cell.get("absent") is True:
                continue
            points = cell["rc_points"]
            (line,) = ax.plot(
                [p[0] for p in points],
                [p[1] for p in points],
                ".-",
                label=mechanism,
                color=f"C{color_index}",
                markersize=2,
            )
            color = line.get_color()
            for _, op in operating_points(cell):
                risk_interval = op["risk_95_interval"]
                coverage_interval = op["attained_coverage_95_interval"]
                ax.vlines(
                    op["attained_coverage"],
                    risk_interval["lower"],
                    risk_interval["upper"],
                    color=color,
                )
                ax.hlines(
                    op["risk"],
                    coverage_interval["lower"],
                    coverage_interval["upper"],
                    color=color,
                )
        absent_slots(slot, cells)
        probability_axes(ax, "Attained coverage", "Selective risk")
        ax.legend(loc="upper left", fontsize=7)
    return fig, (
        "Risk-coverage curves under complete and simulated missing modalities. "
        "Every stored curve point is shown. Vertical risk and "
        "horizontal attained-coverage "
        "intervals are shown at every stored operating point. The "
        "curve between operating "
        "points has no stored intervals. Empty labelled slots retain "
        "absent cells and reasons."
    )


def cohort_flow_figure(
    cohort: dict[str, Any], exclusions: dict[str, Any]
) -> tuple[Figure, str]:
    """Fig 1 displays stored aggregate counts without reconstructing an inventory."""
    entries = sorted(cohort["cohorts"].items())
    fig = Figure(figsize=FLOW_SIZE)
    FigureCanvasAgg(fig)
    for index, (name, cell) in enumerate(entries):
        ax = fig.add_subplot(1, len(entries), index + 1)
        ax.set_axis_off()
        ax.set_title(name)
        exclusion = exclusions["cohorts"][name]
        source_key = {
            "utsw": "source_patient_count",
            "ucsf_pdgm": "metadata_patient_count",
        }[name]
        box = {"facecolor": "none", "edgecolor": "black"}
        ax.text(
            0.3,
            0.85,
            f"Source patients: {exclusion[source_key]}",
            ha="center",
            transform=ax.transAxes,
            bbox=box,
        )
        ax.text(
            0.3,
            0.2,
            f"Retained: {cell['retained_patient_count']}",
            ha="center",
            transform=ax.transAxes,
            bbox=box,
        )
        ax.text(
            0.75,
            0.55,
            f"Excluded: {cell['excluded_patient_count']}",
            ha="center",
            transform=ax.transAxes,
            bbox=box,
        )
        ax.annotate(
            "",
            xy=(0.3, 0.25),
            xytext=(0.3, 0.8),
            xycoords="axes fraction",
            arrowprops={"arrowstyle": "->"},
        )
        ax.annotate(
            "",
            xy=(0.7, 0.56),
            xytext=(0.3, 0.56),
            xycoords="axes fraction",
            arrowprops={"arrowstyle": "->"},
        )
        reasons = exclusion["reason_counts"]
        ax.text(
            0.75,
            0.45,
            "\n".join(
                textwrap.fill(f"{reason}: {count}", width=30)
                for reason, count in sorted(reasons.items())
            ),
            ha="center",
            va="top",
            transform=ax.transAxes,
        )
    return fig, (
        "Cohort flow: stored source, post-QC retained and excluded patient counts "
        "and exclusion reasons; counts only."
    )


def save_figure(fig: Figure, caption: str, stem: Path) -> tuple[Path, Path, Path]:
    """No dates, random IDs, local paths, or clock-dependent metadata in outputs."""
    png, pdf, caption_path = (
        stem.with_suffix(suffix) for suffix in (".png", ".pdf", ".caption.txt")
    )
    fig.savefig(
        png, metadata={"Software": "glioma-selective Phase 13"}, bbox_inches="tight"
    )
    fig.savefig(
        pdf,
        metadata={
            "CreationDate": None,
            "ModDate": None,
            "Producer": "glioma-selective Phase 13",
            "Creator": "glioma-selective Phase 13",
        },
        bbox_inches="tight",
    )
    caption_path.write_text(caption + "\n", encoding="utf-8")
    fig.clear()
    return png, pdf, caption_path

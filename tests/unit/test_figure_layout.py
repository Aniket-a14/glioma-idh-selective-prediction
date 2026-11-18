"""Panel layout: no blank slot band unless a cell is absent."""

from __future__ import annotations

from glioma_selective.visualization.risk_coverage import (
    COMPACT_PANEL_HEIGHT,
    PANEL_HEIGHT,
    PANEL_WIDTH,
    condition_panels,
    conditions_with_absent,
)

CONDITIONS = ["a", "b", "c", "d"]


def test_no_absent_cells_gives_compact_panels_without_slots() -> None:
    fig, axes, slots = condition_panels(CONDITIONS, set())
    assert len(axes) == 4 and slots == [None] * 4
    assert fig.get_size_inches()[1] == COMPACT_PANEL_HEIGHT * 2
    assert fig.get_size_inches()[0] == PANEL_WIDTH * 2


def test_default_and_absent_keep_the_reserved_slot_layout() -> None:
    for absent in (None, {"b"}):
        fig, axes, slots = condition_panels(CONDITIONS, absent)
        assert all(slot is not None for slot in slots)
        assert fig.get_size_inches()[1] == PANEL_HEIGHT * 2


def test_conditions_with_absent_finds_only_absent_cells() -> None:
    cells = {name: {"absent": False} for name in ("M1", "M2", "M3", "M4", "M5", "M6")}
    document = {
        "conditions": {
            "full": cells,
            "drop_t1": {**cells, "M6": {"absent": True, "reason": "x"}},
        }
    }
    assert conditions_with_absent(document) == {"drop_t1"}

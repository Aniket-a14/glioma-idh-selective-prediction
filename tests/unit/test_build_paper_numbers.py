"""Macro generator for the manuscript: TeX-safe names, deterministic output."""

from __future__ import annotations

from scripts.build_paper_numbers import _fmt, _macro, render


def test_macro_names_are_letters_only() -> None:
    assert _macro("StatusC4Int") == "StatusCFourInt"
    assert _macro("IntR2Auroc") == "IntRTwoAuroc"
    assert _macro("CThreeDelta05") == "CThreeDeltaZeroFive"


def test_render_is_sorted_and_uses_num_prefix() -> None:
    text = render({"B1": "0.5", "A": "x"})
    lines = text.splitlines()
    assert lines[1] == "\\newcommand{\\numA}{x}"
    assert lines[2] == "\\newcommand{\\numBOne}{0.5}"


def test_fmt_rounds_floats_and_keeps_ints_and_text() -> None:
    assert _fmt(0.12345, 3) == "0.123"
    assert _fmt(7, 3) == "7"
    assert _fmt("refuted", 3) == "refuted"

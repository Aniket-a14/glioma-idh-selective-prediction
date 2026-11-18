"""Table generator for the journal manuscript: formatting helpers only."""

from __future__ import annotations

from scripts.build_paper_tables import _fraction, f3, interval, tabular, tex_escape


def test_interval_and_rounding() -> None:
    assert f3(0.12345) == "0.123"
    assert interval(0.5, 0.25, 0.75) == "0.500 [0.250, 0.750]"


def test_tabular_is_booktabs_with_header_and_rows() -> None:
    text = tabular("lr", ["A", "B"], [["x", "1"], ["y", "2"]])
    lines = text.splitlines()
    assert lines[0] == "\\begin{tabular}{lr}"
    assert lines[1] == "\\toprule" and lines[2] == "A & B \\\\"
    assert "x & 1 \\\\" in lines and lines[-1] == "\\end{tabular}"


def test_fraction_strings_and_escape() -> None:
    assert _fraction("1/4") == 0.25
    assert _fraction(0.5) == 0.5
    assert tex_escape("drop_t1ce 5%") == "drop\\_t1ce 5\\%"

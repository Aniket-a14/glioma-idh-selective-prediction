from __future__ import annotations

import pytest
from scripts.order_bibitems import BibliographyError, first_citation_order, reorder

DOC = r"""
Intro \cite{b}. Then \cite{a, b} and \cite{c}.
% \cite{z} is a comment and does not count
\begin{thebibliography}{99}
% note kept
\bibitem{a} A entry.

\bibitem{b} B entry.

\bibitem{c} C entry.

\end{thebibliography}
"""


def test_first_citation_order_ignores_comments_and_repeats() -> None:
    assert first_citation_order(r"x \cite{b} y \cite{a,b} % \cite{z}") == ["b", "a"]


def test_reorder_puts_entries_in_first_citation_order() -> None:
    new, in_order = reorder(DOC)
    assert not in_order
    assert (
        new.index(r"\bibitem{b}")
        < new.index(r"\bibitem{a}")
        < new.index(r"\bibitem{c}")
    )
    assert "% note kept" in new
    again, in_order_again = reorder(new)
    assert in_order_again
    assert again == new


def test_reorder_rejects_uncited_and_missing_entries() -> None:
    with pytest.raises(BibliographyError, match="never cited"):
        reorder(DOC.replace(r"\cite{c}", ""))
    with pytest.raises(BibliographyError, match="without entry"):
        reorder(DOC.replace(r"\cite{c}", r"\cite{c,d}"))

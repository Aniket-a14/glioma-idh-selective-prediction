"""Order a manual ``thebibliography`` by first citation, as IEEE requires.

IEEE numbers references in the order they are first cited. With a hand-written
``thebibliography`` LaTeX numbers entries in the order of the ``\\bibitem``
lines, so the list itself has to be in first-citation order. This script reads
the body before ``\\begin{thebibliography}``, records the first appearance of
every key in ``\\cite{...}``, and rewrites the bibliography in that order.

It refuses to write when a cited key has no entry or an entry is never cited,
because IEEE lists only cited works.

Usage:
    python scripts/order_bibitems.py paper/main.tex            # reorder in place
    python scripts/order_bibitems.py --check paper/main.tex    # exit 1 if out of order
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CITE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\])?\{([^}]*)\}")
BEGIN = re.compile(r"\\begin\{thebibliography\}\{[^}]*\}\n?")
END = "\\end{thebibliography}"
ITEM = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}")


class BibliographyError(ValueError):
    """Cited keys and bibliography entries do not match."""


def _strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in text.splitlines())


def first_citation_order(body: str) -> list[str]:
    """Return cited keys in order of first appearance, comments ignored."""
    seen: list[str] = []
    for match in CITE.finditer(_strip_comments(body)):
        for key in match.group(1).split(","):
            key = key.strip()
            if key and key not in seen:
                seen.append(key)
    return seen


def split_entries(block: str) -> tuple[str, dict[str, str], list[str]]:
    """Split the bibliography body into its preamble and one chunk per key."""
    starts = list(ITEM.finditer(block))
    if not starts:
        raise BibliographyError("no \\bibitem entries found")
    preamble = block[: starts[0].start()]
    entries: dict[str, str] = {}
    order: list[str] = []
    for index, match in enumerate(starts):
        stop = starts[index + 1].start() if index + 1 < len(starts) else len(block)
        key = match.group(1).strip()
        if key in entries:
            raise BibliographyError(f"duplicate \\bibitem key: {key}")
        entries[key] = block[match.start() : stop].rstrip() + "\n\n"
        order.append(key)
    return preamble, entries, order


def reorder(text: str) -> tuple[str, bool]:
    """Return the text with the bibliography in first-citation order.

    The second value is True when the entries were already in order.
    """
    begin = BEGIN.search(text)
    if begin is None:
        raise BibliographyError("no \\begin{thebibliography} found")
    end = text.index(END, begin.end())
    cited = first_citation_order(text[: begin.start()])
    preamble, entries, current = split_entries(text[begin.end() : end])
    missing = [key for key in cited if key not in entries]
    uncited = [key for key in current if key not in cited]
    if missing or uncited:
        raise BibliographyError(
            f"cited without entry: {missing}; entry never cited: {uncited}"
        )
    body = preamble + "".join(entries[key] for key in cited)
    return text[: begin.end()] + body + text[end:], current == cited


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tex", type=Path, nargs="+")
    parser.add_argument(
        "--check", action="store_true", help="do not write; exit 1 if out of order"
    )
    args = parser.parse_args(argv)
    status = 0
    for path in args.tex:
        try:
            new, in_order = reorder(path.read_text())
        except BibliographyError as error:
            print(f"{path}: {error}", file=sys.stderr)
            status = 1
            continue
        if args.check:
            if not in_order:
                print(
                    f"{path}: bibliography is not in first-citation order",
                    file=sys.stderr,
                )
                status = 1
        elif not in_order:
            path.write_text(new)
            print(f"{path}: reordered")
        else:
            print(f"{path}: already in order")
    return status


if __name__ == "__main__":
    raise SystemExit(main())

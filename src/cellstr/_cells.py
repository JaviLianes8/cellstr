"""Typed iteration over the cells of terminal text, measuring and tab expansion."""

from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple

from ._ansi import segments, strip_ansi
from ._graphemes import grapheme_ends
from ._width import check_ambiguous, cluster_width, text_width

_LINE_BREAKS = frozenset({"\n", "\r", "\r\n"})


class Cell(NamedTuple):
    """One drawable unit of terminal text, or one escape sequence.

    ``text`` is a whole grapheme cluster or a whole escape sequence, ``width`` the cells
    it occupies (always 0 for an escape), ``column`` the cell offset where it starts,
    counted from the start of the text, and ``escape`` tells the two kinds apart.
    """

    text: str
    width: int
    column: int
    escape: bool


def check_tabsize(tabsize: int | None) -> int | None:
    """Return ``tabsize`` after checking it is None or a positive integer."""
    if tabsize is not None and (isinstance(tabsize, bool) or tabsize < 1):
        raise ValueError(f"tabsize must be a positive integer or None, not {tabsize!r}")
    return tabsize


def iter_cells(text: str, *, ambiguous: int = 1, tabsize: int | None = None) -> Iterator[Cell]:
    """Yield the escape sequences and grapheme clusters of ``text`` with their widths.

    With ``tabsize`` set, a tab advances to the next multiple of ``tabsize`` counted from
    the start of the current line (a CR or LF starts a new line); otherwise a tab is a
    zero-width control like every other one. The texts of the cells concatenate back to
    ``text`` exactly.

    >>> [(len(c.text), c.width, c.column) for c in iter_cells("a\\u4f60\\U0001f1ea\\U0001f1f8")]
    [(1, 1, 0), (1, 2, 1), (2, 2, 3)]
    """
    check_ambiguous(ambiguous)
    check_tabsize(tabsize)
    column = 0
    line_start = 0
    for segment in segments(text):
        if segment.is_escape:
            yield Cell(segment.text, 0, column, True)
            continue
        part = segment.text
        start = 0
        for end in grapheme_ends(part):
            cluster = part[start:end]
            start = end
            if tabsize is not None and cluster == "\t":
                width = tabsize - (column - line_start) % tabsize
            else:
                width = cluster_width(cluster, ambiguous)
            yield Cell(cluster, width, column, False)
            column += width
            if cluster in _LINE_BREAKS:
                line_start = column


def cell_len(text: str, *, ambiguous: int = 1, tabsize: int | None = None) -> int:
    """Number of display cells ``text`` occupies, ignoring ANSI escape sequences.

    Clusters are measured whole (see ``grapheme_width``), so an emoji ZWJ sequence or a
    flag counts once. Controls, including CR and LF, add nothing, so this is the width of
    a single line. ``ambiguous`` and ``tabsize`` are explained in ``char_width`` and
    ``iter_cells``.

    >>> cell_len("\\x1b[31mWARN\\x1b[0m"), cell_len("\\u4f60\\u597d"), cell_len("\\u00e9")
    (4, 4, 1)
    >>> cell_len("\\U0001f469\\u200d\\U0001f4bb"), cell_len("\\u03b1\\u03b2", ambiguous=2)
    (2, 4)
    >>> cell_len("a\\tb", tabsize=8)
    9
    """
    check_ambiguous(ambiguous)
    if check_tabsize(tabsize) is None or "\t" not in text:
        plain = strip_ansi(text) if "\x1b" in text else text
        return text_width(plain, ambiguous)
    return sum(cell.width for cell in iter_cells(text, ambiguous=ambiguous, tabsize=tabsize))


def expand_tabs(text: str, tabsize: int = 8, *, ambiguous: int = 1) -> str:
    """Replace every tab with the spaces it covers on screen.

    Unlike ``str.expandtabs`` the columns are display cells, so wide characters, emoji
    and escape sequences before a tab do not throw it off. Escapes are kept in place.

    >>> expand_tabs("\\u4f60\\tx", 4) == "\\u4f60  x"
    True
    """
    if check_tabsize(tabsize) is None:
        raise ValueError("tabsize must be a positive integer")
    if "\t" not in text:
        check_ambiguous(ambiguous)
        return text
    return "".join(
        " " * cell.width if cell.text == "\t" and not cell.escape else cell.text
        for cell in iter_cells(text, ambiguous=ambiguous, tabsize=tabsize)
    )


def total_width(cells: list[Cell]) -> int:
    """Width of a list of cells produced by ``iter_cells``."""
    return cells[-1].column + cells[-1].width if cells else 0

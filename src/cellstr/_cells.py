"""Typed iteration over the cells of terminal text, measuring and tab expansion."""

from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple

from ._ansi import segments
from ._args import check_ambiguous, check_positive, check_tabsize, check_text
from ._graphemes import grapheme_ends
from ._join import Joiner
from ._width import cluster_width, text_width

_LINE_BREAKS = frozenset({"\n", "\r", "\r\n"})


class Cell(NamedTuple):
    """One drawable unit of terminal text, or one escape sequence.

    ``text`` is a whole grapheme cluster or a whole escape sequence, ``width`` the cells
    it occupies (always 0 for an escape), ``column`` the cell offset where it starts,
    counted from the start of the text, and ``escape`` tells the two kinds apart.

    >>> Cell("\\u4f60", 2, 1, False).width
    2
    """

    text: str
    width: int
    column: int
    escape: bool


Cell.__module__ = "cellstr"


def iter_cells(text: str, *, ambiguous: int = 1, tabsize: int | None = None) -> Iterator[Cell]:
    """Return an iterator over the escape sequences and grapheme clusters of ``text``.

    Each item is a ``Cell``. With ``tabsize`` set, a tab advances to the next multiple of
    ``tabsize`` counted from the start of the current line (a CR or LF starts a new
    line); otherwise a tab is a zero-width control like every other one. The texts of
    the cells concatenate back to ``text`` exactly. The arguments are checked when the
    function is called, not when iteration starts.

    >>> [(len(c.text), c.width, c.column) for c in iter_cells("a\\u4f60\\U0001f1ea\\U0001f1f8")]
    [(1, 1, 0), (1, 2, 1), (2, 2, 3)]
    """
    return cells(check_text(text), check_ambiguous(ambiguous), check_tabsize(tabsize))


def cells(text: str, ambiguous: int, tabsize: int | None) -> Iterator[Cell]:
    """``iter_cells`` for arguments that are already checked."""
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
    flag counts once; an escape sequence ends the cluster before it. Controls, including
    CR and LF, add nothing, so this is the width of a single line. ``ambiguous`` and
    ``tabsize`` are explained in ``char_width`` and ``iter_cells``.

    >>> cell_len("\\x1b[31mWARN\\x1b[0m"), cell_len("\\u4f60\\u597d"), cell_len("\\u00e9")
    (4, 4, 1)
    >>> cell_len("\\U0001f469\\u200d\\U0001f4bb"), cell_len("\\u03b1\\u03b2", ambiguous=2)
    (2, 4)
    >>> cell_len("a\\tb", tabsize=8)
    9
    """
    return measure(check_text(text), check_ambiguous(ambiguous), check_tabsize(tabsize))


def measure(text: str, ambiguous: int, tabsize: int | None) -> int:
    """``cell_len`` for arguments that are already checked."""
    if tabsize is None or "\t" not in text:
        return text_width(text, ambiguous)
    return sum(cell.width for cell in cells(text, ambiguous, tabsize))


def expand_tabs(text: str, tabsize: int = 8, *, ambiguous: int = 1) -> str:
    """Replace every tab with the spaces it covers on screen.

    Unlike ``str.expandtabs`` the columns are display cells, so wide characters, emoji
    and escape sequences before a tab do not throw it off. Escapes are kept in place;
    a stray ESC goes as in ``cell_slice``, so the spaces never extend it into a new
    sequence. A CR or LF starts a new line, as in ``str.expandtabs``.

    >>> expand_tabs("\\u4f60\\tx", 4) == "\\u4f60  x"
    True
    """
    text = check_text(text)
    size = check_positive(tabsize, "tabsize")
    return expand(text, size, check_ambiguous(ambiguous))


def has_stray(text: str) -> bool:
    """True when ``text`` holds an ESC that starts no complete escape sequence."""
    return "\x1b" in text and any("\x1b" in s.text for s in segments(text) if not s.is_escape)


def expand(text: str, tabsize: int | None, ambiguous: int) -> str:
    """``expand_tabs`` for arguments that are already checked; ``None`` expands no tab.

    The text is rebuilt (see ``Joiner``) whenever a tab or a stray ESC is in it, so the
    result never holds an escape sequence that the text did not hold, and its width is
    the sum of the pieces it keeps.
    """
    if not ((tabsize is not None and "\t" in text) or has_stray(text)):
        return text
    out = Joiner(ambiguous)
    for cell in cells(text, ambiguous, tabsize):
        if cell.escape:
            out.escape(cell.text)
        elif tabsize is not None and cell.text == "\t":
            out.fixed(" " * cell.width)
        else:
            out.cluster(cell.text, cell.width)
    return out.text()


def total_width(cells: list[Cell]) -> int:
    """Width of a list of cells produced by ``iter_cells``."""
    return cells[-1].column + cells[-1].width if cells else 0

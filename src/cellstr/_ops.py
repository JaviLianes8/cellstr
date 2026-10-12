"""Grapheme-safe slicing and padding by display cells.

Escape sequences are always kept in place so colour, style and hyperlinks survive the
operation, while only printable cells count toward a width.
"""

from __future__ import annotations

from ._cells import Cell, check_tabsize, expand_tabs, iter_cells, total_width
from ._graphemes import grapheme_ends
from ._width import check_ambiguous, cluster_width, text_width


def cell_slice(
    text: str,
    start: int = 0,
    stop: int | None = None,
    *,
    ambiguous: int = 1,
    tabsize: int | None = None,
) -> str:
    """Return the cells of ``text`` in the half-open column range ``[start, stop)``.

    Grapheme clusters are never split: a letter keeps its accents, a flag or an emoji
    ZWJ sequence stays whole, and a wide cluster is kept only when all its cells fall
    inside the range. Every escape sequence is preserved wherever it sits, so styles and
    OSC 8 hyperlinks still open and close. A zero-width cluster belongs to the column it
    sits at, and one at the very end belongs to any non-empty range that reaches the end
    (or to an open-ended one). An empty range holds no printable text. With ``tabsize``
    set, a tab becomes the spaces it covers inside the range, so the layout survives.

    For plain text, ``cell_slice(t, 0, k) + cell_slice(t, k)`` equals ``t`` whenever
    ``k`` does not fall inside a wide cluster.

    >>> cell_slice("\\x1b[31mhello\\x1b[0m", 0, 3) == "\\x1b[31mhel\\x1b[0m"
    True
    >>> cell_slice("a\\u4f60b", 0, 2), cell_slice("e\\u0301tude", 0, 1) == "e\\u0301"
    ('a', True)
    """
    if start < 0 or (stop is not None and stop < 0):
        raise ValueError("cell_slice does not support negative indices")
    cells = list(iter_cells(text, ambiguous=ambiguous, tabsize=tabsize))
    total = total_width(cells)
    limit = total if stop is None else min(stop, total)
    tail = limit == total and (start < total or (total == 0 and stop is None))
    return "".join(_keep(cell, start, limit, total, tail, tabsize) for cell in cells)


def _keep(cell: Cell, start: int, limit: int, total: int, tail: bool, tabsize: int | None) -> str:
    if cell.escape:
        return cell.text
    if tabsize is not None and cell.text == "\t":
        return " " * max(0, min(cell.column + cell.width, limit) - max(cell.column, start))
    if cell.column < start:
        return ""
    if cell.width:
        return "" if cell.column + cell.width > limit else cell.text
    return cell.text if cell.column < limit or (tail and cell.column == total) else ""


def check_fill(fillchar: str, ambiguous: int) -> str:
    """Return ``fillchar`` after checking it is one grapheme cluster one cell wide."""
    if (
        not fillchar
        or "\x1b" in fillchar
        or next(grapheme_ends(fillchar)) != len(fillchar)
        or cluster_width(fillchar, ambiguous) != 1
    ):
        raise ValueError(f"fillchar must be a single one-cell character, not {fillchar!r}")
    return fillchar


def _prepare(text: str, fillchar: str, ambiguous: int, tabsize: int | None) -> tuple[str, int]:
    check_ambiguous(ambiguous)
    check_fill(fillchar, ambiguous)
    tabsize = check_tabsize(tabsize)
    if tabsize is not None:
        text = expand_tabs(text, tabsize, ambiguous=ambiguous)
    return text, text_width(text, ambiguous)


def ljust(
    text: str, width: int, fillchar: str = " ", *, ambiguous: int = 1, tabsize: int | None = None
) -> str:
    """Pad ``text`` on the right to ``width`` display cells.

    Text already ``width`` cells or wider is returned unchanged. ``fillchar`` must be one
    cell wide. With ``tabsize`` set, tabs are expanded first (see ``expand_tabs``).

    >>> ljust("\\u4f60", 4) == "\\u4f60  "
    True
    """
    text, used = _prepare(text, fillchar, ambiguous, tabsize)
    return text + fillchar * max(0, width - used)


def rjust(
    text: str, width: int, fillchar: str = " ", *, ambiguous: int = 1, tabsize: int | None = None
) -> str:
    """Pad ``text`` on the left to ``width`` display cells.

    >>> rjust("\\x1b[1m42\\x1b[0m", 5) == "   \\x1b[1m42\\x1b[0m"
    True
    """
    text, used = _prepare(text, fillchar, ambiguous, tabsize)
    return fillchar * max(0, width - used) + text


def center(
    text: str, width: int, fillchar: str = " ", *, ambiguous: int = 1, tabsize: int | None = None
) -> str:
    """Centre ``text`` within ``width`` display cells; an odd cell of padding goes right.

    >>> center("ab", 5)
    ' ab  '
    """
    text, used = _prepare(text, fillchar, ambiguous, tabsize)
    pad = max(0, width - used)
    left = pad // 2
    return fillchar * left + text + fillchar * (pad - left)

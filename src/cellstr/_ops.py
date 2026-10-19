"""Grapheme-safe slicing and padding by display cells.

Escape sequences are always kept in place so colour, style and hyperlinks survive the
operation, while only printable cells count toward a width.
"""

from __future__ import annotations

from ._args import check_ambiguous, check_int, check_tabsize, check_text, check_width, show
from ._cells import Cell, cells, expand, total_width
from ._graphemes import grapheme_ends
from ._join import Joiner
from ._width import cluster_width, text_width


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
    sits at, and one at the very end belongs to a non-empty range that reaches the end
    from a column before it (for text with no width at all, to any range starting at 0
    that is open-ended or non-empty). An empty range holds no printable text. With
    ``tabsize`` set, a tab becomes the spaces it covers inside the range, so the layout
    survives. ``start`` and ``stop`` are non-negative integers; ``stop=None`` means the end.

    The result never holds an escape sequence or a wider cluster that the text did not
    hold. A stray ESC (one that starts no complete sequence) is dropped when the result
    ends with it or goes on with printable ASCII, which could extend it into a sequence,
    and a zero-width cluster that the cut glues to an emoji, widening it, is dropped.

    For plain text, ``cell_slice(t, 0, k) + cell_slice(t, k)`` equals ``t`` whenever
    ``k`` does not fall inside a wide cluster.

    >>> cell_slice("\\x1b[31mhello\\x1b[0m", 0, 3) == "\\x1b[31mhel\\x1b[0m"
    True
    >>> cell_slice("a\\u4f60b", 0, 2), cell_slice("e\\u0301tude", 0, 1) == "e\\u0301"
    ('a', True)
    """
    text = check_text(text)
    first = check_width(start, "start")
    end = None if stop is None else check_width(stop, "stop")
    policy = check_ambiguous(ambiguous)
    found = list(cells(text, policy, check_tabsize(tabsize)))
    out = Joiner(policy)
    keep_range(out, found, first, end, tabsize is not None)
    return out.text()


def keep_range(out: Joiner, found: list[Cell], first: int, stop: int | None, tabs: bool) -> None:
    """Add to ``out`` every escape and the cells of ``found`` in columns ``[first, stop)``."""
    total = total_width(found)
    limit = total if stop is None else min(stop, total)
    # A zero-width cluster at the very end: who gets it (see the docstring).
    reach = (first < total) if total else (first == 0 and (stop is None or stop > 0))
    tail = limit == total and reach
    for cell in found:
        if cell.escape:
            out.escape(cell.text)
        elif tabs and cell.text == "\t":
            spaces = min(cell.column + cell.width, limit) - max(cell.column, first)
            if spaces > 0:
                out.fixed(" " * spaces)
        elif _inside(cell, first, limit, total, tail):
            out.cluster(cell.text, cell.width)


def _inside(cell: Cell, start: int, limit: int, total: int, tail: bool) -> bool:
    if cell.column < start:
        return False
    if cell.width:
        return cell.column + cell.width <= limit
    return cell.column < limit or (tail and cell.column == total)


def check_fill(fillchar: object, ambiguous: int) -> str:
    """Return ``fillchar`` after checking it is one grapheme cluster one cell wide."""
    fill = check_text(fillchar, "fillchar")
    if (
        not fill
        or "\x1b" in fill
        or next(grapheme_ends(fill)) != len(fill)
        or cluster_width(fill, ambiguous) != 1
    ):
        raise ValueError(f"fillchar must be a single one-cell character, not {show(fill)}")
    return fill


def _prepare(
    text: object, width: object, fillchar: object, ambiguous: object, tabsize: object
) -> tuple[str, int, str]:
    """Check the padding arguments; return the text, the cells to add and the fill."""
    body = check_text(text)
    size = check_int(width, "width")
    policy = check_ambiguous(ambiguous)
    fill = check_fill(fillchar, policy)
    body = expand(body, check_tabsize(tabsize), policy)
    return body, max(0, size - text_width(body, policy)), fill


def ljust(
    text: str, width: int, fillchar: str = " ", *, ambiguous: int = 1, tabsize: int | None = None
) -> str:
    """Pad ``text`` on the right to ``width`` display cells.

    Text already ``width`` cells or wider gets no padding, nor does any text when
    ``width`` is zero or negative (as with ``str.ljust``). ``fillchar`` must be one
    cell wide. With ``tabsize`` set, tabs are expanded first (see ``expand_tabs``); a
    stray ESC goes as in ``cell_slice``, so the fill never extends it into a sequence.

    >>> ljust("\\u4f60", 4) == "\\u4f60  "
    True
    """
    body, pad, fill = _prepare(text, width, fillchar, ambiguous, tabsize)
    return body + fill * pad


def rjust(
    text: str, width: int, fillchar: str = " ", *, ambiguous: int = 1, tabsize: int | None = None
) -> str:
    """Pad ``text`` on the left to ``width`` display cells (see ``ljust`` for the rules).

    >>> rjust("\\x1b[1m42\\x1b[0m", 5) == "   \\x1b[1m42\\x1b[0m"
    True
    """
    body, pad, fill = _prepare(text, width, fillchar, ambiguous, tabsize)
    return fill * pad + body


def center(
    text: str, width: int, fillchar: str = " ", *, ambiguous: int = 1, tabsize: int | None = None
) -> str:
    """Centre ``text`` within ``width`` display cells; an odd cell of padding goes right.

    The odd cell always goes right, unlike ``str.center``, which moves it depending on
    the parity of ``width``. The other rules are those of ``ljust``.

    >>> center("ab", 5), center("abc", 6)
    (' ab  ', ' abc  ')
    """
    body, pad, fill = _prepare(text, width, fillchar, ambiguous, tabsize)
    left = pad // 2
    return fill * left + body + fill * (pad - left)

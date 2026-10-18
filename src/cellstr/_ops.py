"""Grapheme-safe slicing and padding by display cells.

Escape sequences are always kept in place so colour, style and hyperlinks survive the
operation, while only printable cells count toward a width.
"""

from __future__ import annotations

from ._args import check_ambiguous, check_int, check_tabsize, check_text, check_width, show
from ._cells import Cell, cells, expand, total_width
from ._graphemes import grapheme_ends
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
    that is open-ended or non-empty). An empty range holds no printable text. With ``tabsize``
    set, a tab becomes the spaces it covers inside the range, so the layout survives.
    ``start`` and ``stop`` are non-negative integers; ``stop=None`` means the end.

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
    found = list(cells(text, check_ambiguous(ambiguous), check_tabsize(tabsize)))
    total = total_width(found)
    limit = total if end is None else min(end, total)
    # A zero-width cluster at the very end: who gets it (see the docstring).
    reach = (first < total) if total else (first == 0 and (end is None or end > 0))
    tail = limit == total and reach
    tabs = tabsize is not None
    return "".join(_keep(cell, first, limit, total, tail, tabs) for cell in found)


def _keep(cell: Cell, start: int, limit: int, total: int, tail: bool, tabs: bool) -> str:
    if cell.escape:
        return cell.text
    if tabs and cell.text == "\t":
        return " " * max(0, min(cell.column + cell.width, limit) - max(cell.column, start))
    if cell.column < start:
        return ""
    if cell.width:
        return "" if cell.column + cell.width > limit else cell.text
    return cell.text if cell.column < limit or (tail and cell.column == total) else ""


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
    tabs = check_tabsize(tabsize)
    if tabs is not None:
        body = expand(body, tabs, policy)
    return body, max(0, size - text_width(body, policy)), fill


def ljust(
    text: str, width: int, fillchar: str = " ", *, ambiguous: int = 1, tabsize: int | None = None
) -> str:
    """Pad ``text`` on the right to ``width`` display cells.

    Text already ``width`` cells or wider is returned unchanged, as is any text when
    ``width`` is zero or negative (as with ``str.ljust``). ``fillchar`` must be one
    cell wide. With ``tabsize`` set, tabs are expanded first (see ``expand_tabs``).

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


def splice(text: str, head: int, rstart: int, insert: str, ambiguous: int) -> str:
    """Keep the clusters in ``[0, head)`` and ``[rstart, end)``, putting ``insert`` between.

    Every escape sequence is kept exactly once, in place, and ``insert`` goes where the
    first dropped cluster was.
    """
    found = list(cells(text, ambiguous, None))
    total = total_width(found)
    out: list[str] = []
    pending = True
    for cell in found:
        end = cell.column + cell.width
        left = end <= head if cell.width else cell.column < head
        right = rstart <= cell.column and end <= total
        if not (cell.escape or left) and pending:
            out.append(insert)
            pending = False
        if cell.escape or left or right:
            out.append(cell.text)
    if pending:
        out.append(insert)
    return "".join(out)

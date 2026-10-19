"""Width-aware truncation with a suffix at the end, start or middle, and exact fitting."""

from __future__ import annotations

from typing import Literal, NamedTuple

from ._args import check_ambiguous, check_choice, check_tabsize, check_text, check_width
from ._cells import cells, expand, measure
from ._ops import center, check_fill, ljust, rjust
from ._splice import cut
from ._width import text_width

Position = Literal["end", "start", "middle"]
Align = Literal["left", "right", "center"]
_POSITIONS = ("end", "start", "middle")
_ALIGNS = ("left", "right", "center")


class Truncation(NamedTuple):
    """The outcome of ``truncate_detailed``.

    ``text`` is the result, ``width`` the cells it occupies, ``original_width`` the cells
    the input occupied (tabs at their stops when ``tabsize`` is set) and ``truncated``
    whether anything was cut.

    >>> Truncation("hi", 2, 2, False).truncated
    False
    """

    text: str
    width: int
    original_width: int
    truncated: bool


Truncation.__module__ = "cellstr"


def truncate_detailed(
    text: str,
    width: int,
    suffix: str = "...",
    *,
    position: Position = "end",
    ambiguous: int = 1,
    tabsize: int | None = None,
) -> Truncation:
    """Shorten ``text`` to at most ``width`` cells and report what happened.

    ``position`` says where the cut goes: ``"end"`` keeps the start, ``"start"`` keeps
    the end (log tails, right-aligned numbers) and ``"middle"`` keeps both ends (paths,
    identifiers), giving the odd cell to the left part; when a wide cluster leaves a cell
    of one part unused, the other part takes it. The suffix marks the cut. When the
    suffix alone would not fit, the text is cut to ``width`` with no suffix. Grapheme
    clusters are never split, so a wide cluster at a cut may leave the result short by
    less than its width. Every escape sequence in the text is kept once, in place; the
    suffix is inserted as given (it may hold escape sequences) and must not contain tabs
    or line breaks. As in ``cell_slice``, the result never holds an escape sequence or a
    cluster that the text and the suffix did not hold. ``width`` is a non-negative
    integer. With ``tabsize`` set, every tab in the result becomes the spaces it covers
    there, as in ``cell_slice``.

    >>> truncate_detailed("hello world", 8)
    Truncation(text='hello...', width=8, original_width=11, truncated=True)
    """
    text = check_text(text)
    limit = check_width(width)
    suffix = check_text(suffix, "suffix")
    if any(ch in suffix for ch in "\t\n\r"):
        raise ValueError("suffix must not contain tabs or line breaks")
    where = check_choice(position, "position", _POSITIONS)
    policy = check_ambiguous(ambiguous)
    tabs = check_tabsize(tabsize)
    # Tabs are measured at their stops and turned into spaces only inside the kept parts,
    # so the work stays proportional to the text and the result, whatever the tab size.
    total = measure(text, policy, tabs)
    if total <= limit:
        body = expand(text, tabs, policy)
        return Truncation(body, total if body is text else text_width(body, policy), total, False)
    room = limit - text_width(suffix, policy)
    if room < 0:  # no room for the suffix: hard cut, and a middle cut becomes an end cut
        suffix, room = "", limit
        where = "start" if where == "start" else "end"
    found = list(cells(text, policy, tabs))
    result = cut(found, total, room, where, suffix, policy, tabs is not None)
    return Truncation(result, text_width(result, policy), total, True)


def truncate(
    text: str,
    width: int,
    suffix: str = "...",
    *,
    position: Position = "end",
    ambiguous: int = 1,
    tabsize: int | None = None,
) -> str:
    """Shorten ``text`` to at most ``width`` cells, marking the cut with ``suffix``.

    ``text`` is returned unchanged when it already fits, except that with ``tabsize`` set
    its tabs are expanded and that a stray ESC goes as in ``cell_slice``. See
    ``truncate_detailed`` for the cut positions and the rules.

    >>> truncate("hello world", 8), truncate("/usr/local/lib/python", 12, position="middle")
    ('hello...', '/usr/...thon')
    """
    return truncate_detailed(
        text, width, suffix, position=position, ambiguous=ambiguous, tabsize=tabsize
    ).text


def fit(
    text: str,
    width: int,
    *,
    align: Align = "left",
    suffix: str = "...",
    position: Position = "end",
    fillchar: str = " ",
    ambiguous: int = 1,
    tabsize: int | None = None,
) -> str:
    """Return ``text`` truncated or padded to exactly ``width`` cells: one table cell.

    Long text is cut as ``truncate`` does, short text is padded as ``ljust``, ``rjust``
    or ``center`` do, depending on ``align``. When a wide cluster at the cut leaves the
    result short, padding fills the missing cells, so columns always line up.

    >>> fit("\\u4f60\\u597d\\u4e16\\u754c", 5, suffix="") == "\\u4f60\\u597d "
    True
    >>> fit("42", 5, align="right")
    '   42'
    """
    side = check_choice(align, "align", _ALIGNS)
    policy = check_ambiguous(ambiguous)
    fill = check_fill(fillchar, policy)
    cut = truncate_detailed(
        text, width, suffix, position=position, ambiguous=policy, tabsize=tabsize
    ).text
    pad = {"left": ljust, "right": rjust, "center": center}[side]
    return pad(cut, width, fill, ambiguous=policy)

"""Width-aware truncation with a suffix at the end, start or middle, and exact fitting."""

from __future__ import annotations

from typing import Literal, NamedTuple

from ._args import check_ambiguous, check_choice, check_tabsize, check_text, check_width
from ._cells import expand
from ._ops import cell_slice, center, check_fill, ljust, rjust, splice
from ._width import text_width

Position = Literal["end", "start", "middle"]
Align = Literal["left", "right", "center"]
_POSITIONS = ("end", "start", "middle")
_ALIGNS = ("left", "right", "center")


class Truncation(NamedTuple):
    """The outcome of ``truncate_detailed``.

    ``text`` is the result, ``width`` the cells it occupies, ``original_width`` the cells
    the input occupied (after tab expansion) and ``truncated`` whether anything was cut.

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
    identifiers), giving the odd cell to the left part. The suffix marks the cut. When
    the suffix alone would not fit, the text is cut to ``width`` with no suffix. Grapheme
    clusters are never split, so a wide character at the cut may leave the result one
    cell short. Every escape sequence in the text is kept once, in place; the suffix is
    inserted as given (it may hold escape sequences) and must not contain tabs or line
    breaks. ``width`` is a non-negative integer.

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
    if tabs is not None:
        text = expand(text, tabs, policy)
    total = text_width(text, policy)
    if total <= limit:
        return Truncation(text, total, total, False)
    room = limit - text_width(suffix, policy)
    if room < 0:  # no room for the suffix: hard cut, and a middle cut becomes an end cut
        suffix, room = "", limit
        where = "start" if where == "start" else "end"
    if where == "end":
        cut = cell_slice(text, 0, room, ambiguous=policy) + suffix
    elif where == "start":
        cut = suffix + cell_slice(text, total - room, ambiguous=policy)
    else:
        head = (room + 1) // 2
        cut = splice(text, head, total - (room - head), suffix, policy)
    return Truncation(cut, text_width(cut, policy), total, True)


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

    ``text`` is returned unchanged when it already fits; with ``tabsize`` set its tabs
    are expanded first. See ``truncate_detailed`` for the cut positions and the rules.

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
    or ``center`` do, depending on ``align``. When a wide character at the cut leaves the
    result one cell short, padding fills it, so columns always line up.

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

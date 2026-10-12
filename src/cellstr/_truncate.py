"""Width-aware truncation with a suffix at the end, start or middle, and exact fitting."""

from __future__ import annotations

from typing import Literal, NamedTuple

from ._ansi import strip_ansi
from ._cells import check_tabsize, expand_tabs
from ._ops import cell_slice, center, check_fill, ljust, rjust
from ._width import check_ambiguous, text_width

Position = Literal["end", "start", "middle"]
Align = Literal["left", "right", "center"]
_POSITIONS = ("end", "start", "middle")
_ALIGNS = ("left", "right", "center")


class Truncation(NamedTuple):
    """The outcome of ``truncate_detailed``.

    ``text`` is the result, ``width`` the cells it occupies, ``original_width`` the cells
    the input occupied and ``truncated`` whether anything was cut.
    """

    text: str
    width: int
    original_width: int
    truncated: bool


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
    cell short. Escape sequences in the text are kept; the suffix is inserted as given.

    >>> truncate_detailed("hello world", 8)
    Truncation(text='hello...', width=8, original_width=11, truncated=True)
    """
    if width < 0:
        raise ValueError(f"width must be non-negative, not {width}")
    if position not in _POSITIONS:
        raise ValueError(f"position must be one of {', '.join(_POSITIONS)}, not {position!r}")
    check_ambiguous(ambiguous)
    tabsize = check_tabsize(tabsize)
    if tabsize is not None:
        text = expand_tabs(text, tabsize, ambiguous=ambiguous)
    total = text_width(strip_ansi(text), ambiguous)
    if total <= width:
        return Truncation(text, total, total, False)
    room = width - text_width(strip_ansi(suffix), ambiguous)
    if room < 0:
        cut = cell_slice(text, total - width) if position == "start" else cell_slice(text, 0, width)
    elif position == "end":
        cut = cell_slice(text, 0, room) + suffix
    elif position == "start":
        cut = suffix + cell_slice(text, total - room)
    else:
        left = (room + 1) // 2
        cut = cell_slice(text, 0, left) + suffix + cell_slice(text, total - (room - left))
    return Truncation(cut, text_width(strip_ansi(cut), ambiguous), total, True)


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

    ``text`` is returned unchanged when it already fits. See ``truncate_detailed`` for
    the cut positions and the rules.

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
    if align not in _ALIGNS:
        raise ValueError(f"align must be one of {', '.join(_ALIGNS)}, not {align!r}")
    check_fill(fillchar, check_ambiguous(ambiguous))
    cut = truncate_detailed(
        text, width, suffix, position=position, ambiguous=ambiguous, tabsize=tabsize
    ).text
    pad = {"left": ljust, "right": rjust, "center": center}[align]
    return pad(cut, width, fillchar, ambiguous=ambiguous)

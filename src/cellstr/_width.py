"""Display width of characters and whole strings."""

from __future__ import annotations

from bisect import bisect_right

from ._ansi import strip_ansi
from ._table import WIDE, ZERO_WIDTH

_ZERO_STARTS = [low for low, _ in ZERO_WIDTH]
_WIDE_STARTS = [low for low, _ in WIDE]


def _in_ranges(cp: int, starts: list[int], ranges: tuple[tuple[int, int], ...]) -> bool:
    index = bisect_right(starts, cp) - 1
    return index >= 0 and ranges[index][0] <= cp <= ranges[index][1]


def char_width(char: str) -> int:
    """Display cells a single character occupies: 0, 1 or 2.

    Control characters and combining marks are zero, East Asian wide and
    fullwidth characters are two, everything else is one.
    """
    if len(char) != 1:
        raise ValueError("char_width expects a single character")
    cp = ord(char)
    if cp == 0 or cp < 0x20 or 0x7F <= cp < 0xA0:
        return 0
    if _in_ranges(cp, _ZERO_STARTS, ZERO_WIDTH):
        return 0
    if _in_ranges(cp, _WIDE_STARTS, WIDE):
        return 2
    return 1


def cell_len(text: str) -> int:
    """Number of display cells ``text`` occupies, ignoring ANSI escapes."""
    return sum(char_width(ch) for ch in strip_ansi(text))

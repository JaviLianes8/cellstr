"""Assembly of a result from kept pieces of a text, so that no piece fuses with a new neighbour.

Cutting, padding and tab expansion put next to each other pieces that were not neighbours
in the input. Two things could then appear that the input did not hold: an escape sequence,
when a stray ESC (one that starts no complete sequence) meets printable ASCII, and a wider
grapheme cluster, when an orphan such as VS16 or a tag character meets an emoji. ``Joiner``
drops the stray ESC, or the cluster that would fuse, in exactly those cases.
"""

from __future__ import annotations

from ._ansi import segments
from ._graphemes import Scan, may_join, scan
from ._props import EMOJI_BIT, EXT_PICT_BIT, MODIFIER_BIT, prop
from ._width import code_width

_ESC = "\x1b"


class Joiner:
    """Collect the pieces of a result in order; ``text()`` returns the result."""

    def __init__(self, ambiguous: int) -> None:
        self._parts: list[str] = []
        self._tail = ""  # the text piece kept last; empty at the start and after an escape
        self._state: Scan | None = None  # break state after the tail, computed on demand
        self._stray = 0  # stray ESCs in a row, waiting for the code point that follows them
        self._ambiguous = ambiguous

    def escape(self, sequence: str) -> None:
        """Keep a complete escape sequence."""
        self._settle(sequence)
        self._parts.append(sequence)
        self._tail, self._state = "", None

    def cluster(self, text: str, width: int) -> None:
        """Keep a grapheme cluster of the input unless it would fuse into a wider cluster."""
        if text == _ESC:
            self._stray += 1
        else:
            self._settle(text)
            self._add(text, width)

    def fixed(self, text: str) -> None:
        """Keep text the caller adds (a suffix, spaces for a tab); stray ESCs in it may go."""
        for index, piece in enumerate(text.split(_ESC)):
            if index:
                self._stray += 1
            if piece:
                self._settle(piece)
                self._add(piece, None)

    def insert(self, text: str) -> None:
        """Keep a suffix: its escape sequences, and its text as ``fixed``."""
        for segment in segments(text):
            if segment.is_escape:
                self.escape(segment.text)
            else:
                self.fixed(segment.text)

    def text(self) -> str:
        """The result; stray ESCs still waiting at the very end are dropped."""
        return "".join(self._parts)

    def _settle(self, following: str) -> None:
        # A run of stray ESCs can only start an escape sequence with printable ASCII.
        if self._stray:
            if not " " <= following[0] <= "~":
                self._parts.append(_ESC * self._stray)
                self._tail, self._state = _ESC, None
            self._stray = 0

    def _add(self, text: str, width: int | None) -> None:
        tail = self._tail
        if tail and may_join(prop(ord(tail[-1])), prop(ord(text[0]))):
            if self._state is None:
                self._state = scan(tail, None)[1]
            before = self._state
            joined, after = scan(text, before)
            if joined and before is not None:
                if width is not None and self._grows(text, width, before[4]):
                    return
                self._parts.append(text)
                self._tail, self._state = text, after
                return
        self._parts.append(text)
        self._tail, self._state = text, None

    def _grows(self, text: str, width: int, head: int) -> bool:
        """True when ``text``, glued to a cluster starting with ``head``, would widen it.

        Glued clusters add up their code points, except when the first is an emoji: then
        a variation selector, a tag or a modifier can make the whole two cells.
        """
        if width < sum(code_width(prop(ord(char)), self._ambiguous) for char in text):
            return True
        return width == 0 and bool(head & (EMOJI_BIT | EXT_PICT_BIT)) and not head & MODIFIER_BIT

"""Assembly of a result from kept pieces of a text, so that no piece fuses with a new neighbour.

Cutting, padding and tab expansion put next to each other pieces that were not neighbours
in the input. Two things could then appear that the input did not hold: an escape sequence,
when a stray ESC (one that starts no complete sequence) meets printable ASCII, and a cluster
of another width, when a piece glues to the cluster before it (VS16 or a tag character after
an emoji, an emoji after a ZWJ). ``Joiner`` drops the stray ESC, or the piece that would glue
at another width, in exactly those cases, for the clusters of the text and for the text the
caller adds alike. So the width of the result is always the sum of the pieces it keeps.
"""

from __future__ import annotations

from ._ansi import segments
from ._graphemes import grapheme_ends, may_join
from ._props import prop
from ._width import cluster_width, text_width

_ESC = "\x1b"


class Joiner:
    """Collect the pieces of a result in order; ``text()`` returns the result."""

    def __init__(self, ambiguous: int) -> None:
        self._parts: list[str] = []
        self._tail = ""  # the text piece kept last; empty at the start and after an escape
        self._open: str | None = None  # the last cluster of the result; None: of the tail
        self._stray = 0  # stray ESCs in a row, waiting for the code point that follows them
        self._ambiguous = ambiguous

    def escape(self, sequence: str) -> None:
        """Keep a complete escape sequence."""
        self._settle(sequence)
        self._parts.append(sequence)
        self._tail, self._open = "", None

    def cluster(self, text: str, width: int) -> None:
        """Keep a grapheme cluster of the input unless it would glue at another width."""
        if text == _ESC:
            self._stray += 1
        else:
            self._settle(text)
            self._add(text, width)

    def fixed(self, text: str) -> None:
        """Keep text the caller adds (a suffix, spaces for a tab); stray ESCs in it may go.

        A cluster of it that would glue to the kept text at another width goes, as in
        ``cluster``.
        """
        for index, piece in enumerate(text.split(_ESC)):
            if index:
                self._stray += 1
            if piece:
                self._settle(piece)
                self._add_fixed(piece)

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
                self._tail, self._open = _ESC, None
            self._stray = 0

    def _add_fixed(self, piece: str) -> None:
        # Only the clusters at its start can glue to what is kept, so the rest goes in whole.
        while piece and self._tail and may_join(prop(ord(self._tail[-1])), prop(ord(piece[0]))):
            end = next(grapheme_ends(piece))
            self._add(piece[:end], cluster_width(piece[:end], self._ambiguous))
            piece = piece[end:]
        if piece:
            self._parts.append(piece)
            self._tail, self._open = piece, None

    def _add(self, text: str, width: int) -> None:
        tail = self._tail
        if tail and may_join(prop(ord(tail[-1])), prop(ord(text[0]))):
            head = self._open if self._open is not None else _last_cluster(tail)
            glued = head + text
            # A cluster starts a fresh run of the break rules, so ``glued`` splits as it
            # does in the whole result; when ``text`` does not join, the widths add up.
            if text_width(glued, self._ambiguous) != cluster_width(head, self._ambiguous) + width:
                return
            self._parts.append(text)
            self._tail, self._open = text, _last_cluster(glued)
            return
        self._parts.append(text)
        self._tail, self._open = text, None


def _last_cluster(text: str) -> str:
    start = 0
    for end in grapheme_ends(text):
        if end < len(text):
            start = end
    return text[start:]
